import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import PRICE_PER_M2, BRANCH_NAMES
from keyboards.default_kb import get_branch_menu
from keyboards.inline_kb import get_width_kb, get_color_kb, get_confirm_import_kb
from utils.states import ImportStates
from database.local_db import add_roll
from handlers.common import get_user_role

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "📥 Import (Kirim)")
async def start_import(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    await state.clear()
    await state.set_state(ImportStates.choosing_width)
    await message.answer("Rulonning enini (metr) tanlang:", reply_markup=get_width_kb("import_width"))

@router.callback_query(F.data.startswith("import_width:"), ImportStates.choosing_width)
async def process_width(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    width = float(callback.data.split(":")[1])
    await state.update_data(width=width)
    await state.set_state(ImportStates.choosing_color)
    await callback.message.edit_text(
        f"Tanlangan eni: {width:g} metr\n\nEndi rulon rangini tanlang:",
        reply_markup=get_color_kb("import_color")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("import_color:"), ImportStates.choosing_color)
async def process_color(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    color = callback.data.split(":")[1]
    await state.update_data(color=color)
    await state.set_state(ImportStates.entering_length)
    
    data = await state.get_data()
    width = data["width"]
    
    await callback.message.edit_text(
        f"Tanlangan: {width:g}x - {color}\n\n"
        "Uzunlikni metrda yozib yuboring (Masalan: 10.95 yoki 15):"
    )
    await callback.answer()

@router.message(ImportStates.entering_length)
async def process_length(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    text = message.text.strip().replace(",", ".")
    try:
        length = float(text)
        if length <= 0:
            await message.answer("Uzunlik 0 dan katta bo'lishi kerak! Qaytadan kiriting:")
            return
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting (Masalan: 10.95 yoki 15):")
        return

    data = await state.get_data()
    width = data["width"]
    color = data["color"]
    
    area_m2 = round(width * length, 2)
    total_price = round(area_m2 * PRICE_PER_M2, 2)
    
    await state.update_data(length=length, area_m2=area_m2, total_price=total_price)
    await state.set_state(ImportStates.confirming)
    
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    summary = (
        f"📦 *Yangi rulon ({b_name}):*\n\n"
        f"📏 O'lchami: `{width:g} x {length} metr`\n"
        f"🎨 Rangi: *{color}*\n"
        f"📐 Maydoni: `{area_m2} m²`\n"
        f"💰 Qiymati ($8/m²): `${total_price:.2f}`\n\n"
        f"Qisqacha: *{width:g}x{length} - {color}*\n\n"
        f"Ma'lumotlar to'g'riligini tasdiqlaysizmi?"
    )
    await message.answer(summary, parse_mode="Markdown", reply_markup=get_confirm_import_kb())

@router.callback_query(F.data == "retry_import", ImportStates.confirming)
async def retry_import(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    await state.set_state(ImportStates.choosing_width)
    await callback.message.edit_text("Rulonning enini tanlang:", reply_markup=get_width_kb("import_width"))
    await callback.answer()

@router.callback_query(F.data == "confirm_import", ImportStates.confirming)
async def confirm_import(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    width = data["width"]
    color = data["color"]
    length = data["length"]
    
    created_roll = await add_roll(width=width, color=color, length=length, branch_id=branch_id)
    
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await callback.message.answer(
        f"✅ *Rulon omborga saqlandi! ({b_name})*\n\n"
        f"🆔 Rulon kodi: *{created_roll['roll_code']}*\n"
        f"📐 O'lchami: {width:g} x {length} metr ({created_roll['area_m2']} m²)\n"
        f"🎨 Rangi: {color}\n"
        f"💰 Qiymati: ${created_roll['total_price']:.2f}",
        parse_mode="Markdown",
        reply_markup=get_branch_menu(b_name)
    )
    await callback.answer("Saqlandi!")
