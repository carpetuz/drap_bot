import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import PRICE_PER_M2, BRANCH_NAMES
from keyboards.default_kb import get_branch_menu
from keyboards.inline_kb import (
    get_available_widths_kb, 
    get_available_colors_kb, 
    get_rolls_selection_kb, 
    get_confirm_sale_kb
)
from utils.states import SaleStates
from database.local_db import (
    get_available_widths, 
    get_available_colors, 
    get_available_rolls, 
    get_roll_by_id, 
    make_sale
)
from handlers.common import get_user_role

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "🛒 Sotuv qilish")
async def start_sale(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    await state.clear()
    
    widths = await get_available_widths(branch_id=branch_id)
    if not widths:
        await message.answer(
            f"Sizning filialingiz omborida mavjud gilam rulonlari yo'q! Avval '📥 Import (Kirim)' bo'limidan mahsulot qo'shing.",
            reply_markup=get_branch_menu()
        )
        return
        
    await state.set_state(SaleStates.choosing_width)
    await message.answer("Sotilayotgan rulonning enini tanlang:", reply_markup=get_available_widths_kb(widths))

@router.callback_query(F.data.startswith("sale_width:"), SaleStates.choosing_width)
async def sale_choose_width(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    width = float(callback.data.split(":")[1])
    await state.update_data(width=width)
    
    colors = await get_available_colors(width, branch_id=branch_id)
    if not colors:
        await callback.message.edit_text("Ushbu o'lchamda faol rulon topilmadi.")
        return
        
    await state.set_state(SaleStates.choosing_color)
    await callback.message.edit_text(
        f"Eni: {width:g}x metr\n\nEndi rangni tanlang:",
        reply_markup=get_available_colors_kb(colors)
    )
    await callback.answer()

@router.callback_query(F.data == "sale_back_to_width")
async def sale_back_to_width(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    widths = await get_available_widths(branch_id=branch_id)
    await state.set_state(SaleStates.choosing_width)
    await callback.message.edit_text("Sotilayotgan rulonning enini tanlang:", reply_markup=get_available_widths_kb(widths))
    await callback.answer()

@router.callback_query(F.data.startswith("sale_color:"), SaleStates.choosing_color)
async def sale_choose_color(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    color = callback.data.split(":")[1]
    await state.update_data(color=color)
    
    data = await state.get_data()
    width = data["width"]
    
    rolls = await get_available_rolls(width, color, branch_id=branch_id)
    if not rolls:
        await callback.message.edit_text("Ushbu rangda mavjud rulon topilmadi.")
        return
        
    await state.set_state(SaleStates.choosing_roll)
    await callback.message.edit_text(
        f"Tanlangan: {width:g}x - {color}\n\nQaysi rulondan kesib sotmoqchisiz? Tanlang:",
        reply_markup=get_rolls_selection_kb(rolls)
    )
    await callback.answer()

@router.callback_query(F.data == "sale_back_to_color")
async def sale_back_to_color(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    width = data["width"]
    colors = await get_available_colors(width, branch_id=branch_id)
    await state.set_state(SaleStates.choosing_color)
    await callback.message.edit_text(
        f"Eni: {width:g}x metr\n\nEndi rangni tanlang:",
        reply_markup=get_available_colors_kb(colors)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("sale_roll:"), SaleStates.choosing_roll)
async def sale_choose_roll(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    roll_id = int(callback.data.split(":")[1])
    roll = await get_roll_by_id(roll_id)
    if not roll or roll["branch_id"] != branch_id:
        await callback.message.edit_text("Rulon topilmadi!")
        return
        
    await state.update_data(roll_id=roll_id, roll=roll)
    await state.set_state(SaleStates.entering_sold_length)
    
    await callback.message.edit_text(
        f"Tanlangan rulon: *{roll['roll_code']}*\n"
        f"O'lchami: {roll['width']:g} x {roll['current_length']} metr - {roll['color']}\n"
        f"Mavjud qoldiq: *{roll['current_length']} metr*\n\n"
        "Qancha metr sotildi? Uzunlikni yozing (Masalan: 10 yoki 3.5):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(SaleStates.entering_sold_length)
async def sale_process_length(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    text = message.text.strip().replace(",", ".")
    try:
        sold_length = float(text)
        if sold_length <= 0:
            await message.answer("Sotilgan uzunlik 0 dan katta bo'lishi kerak! Qaytadan kiriting:")
            return
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting (Masalan: 10 yoki 3.5):")
        return

    data = await state.get_data()
    roll = data["roll"]
    
    if sold_length > roll["current_length"]:
        await message.answer(
            f"❌ Xatolik! Rulonda buncha uzunlik yo'q!\n"
            f"Mavjud qoldiq: *{roll['current_length']} metr*.\n\n"
            f"Iltimos, mavjud qoldiqdan oshmagan miqdor kiriting:",
            parse_mode="Markdown"
        )
        return
        
    sold_area = round(roll["width"] * sold_length, 2)
    total_price = round(sold_area * PRICE_PER_M2, 2)
    remaining_length = round(roll["current_length"] - sold_length, 2)
    
    await state.update_data(
        sold_length=sold_length, 
        sold_area=sold_area, 
        total_price=total_price, 
        remaining_length=remaining_length
    )
    await state.set_state(SaleStates.confirming)
    
    summary = (
        f"🛒 *Sotuvni tasdiqlash:*\n\n"
        f"🆔 Rulon: *{roll['roll_code']}*\n"
        f"📦 Mahsulot: `{roll['width']:g}x{sold_length} metr - {roll['color']}`\n"
        f"📐 Sotilgan maydon: `{sold_area} m²`\n"
        f"💵 Narxi ($8/m²): `${PRICE_PER_M2:.2f}`\n"
        f"💰 Jami summa: *${total_price:.2f}*\n"
        f"✂️ Rulonda qoladi: `{remaining_length} metr`\n\n"
        f"Sotuvni tasdiqlaysizmi?"
    )
    await message.answer(summary, parse_mode="Markdown", reply_markup=get_confirm_sale_kb())

@router.callback_query(F.data == "retry_sale", SaleStates.confirming)
async def retry_sale(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    roll = data["roll"]
    await state.set_state(SaleStates.entering_sold_length)
    await callback.message.edit_text(
        f"Rulon: *{roll['roll_code']}* (Qoldiq: {roll['current_length']} metr)\n\n"
        "Qancha metr sotildi? Qaytadan kiriting:",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_sale", SaleStates.confirming)
async def confirm_sale(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    roll_id = data["roll_id"]
    sold_length = data["sold_length"]
    
    result = await make_sale(roll_id=roll_id, sold_length=sold_length, branch_id=branch_id)
    
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await callback.message.answer(
        f"✅ *Sotuv muvaffaqiyatli amalga oshirildi! ({b_name})*\n\n"
        f"📦 Mahsulot: {result['width']:g}x{result['sold_length']}m - {result['color']}\n"
        f"📐 Maydoni: {result['sold_area']} m²\n"
        f"💰 Sotuv summasi: *${result['sale_total_price']:.2f}*\n"
        f"✂️ Rulondagi qoldiq: {result['remaining_length']} metr\n\n"
        f"💵 *Kassangizga qo'shildi:* +${result['sale_total_price']:.2f}\n"
        f"💰 *Joriy kassa balansingiz:* ${result['new_cash_balance']:.2f}",
        parse_mode="Markdown",
        reply_markup=get_branch_menu(b_name)
    )
    await callback.answer("Sotildi!")
