import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import BRANCH3_COLLECTIONS, BRANCH3_WIDTH
from keyboards.default_kb import get_branch3_menu
from keyboards.inline_kb import (
    get_branch3_collections_kb,
    get_branch3_confirm_sale_kb,
    get_branch3_report_kb
)
from utils.states import Branch3SaleStates
from database.local_db import (
    make_branch3_sale,
    get_branch3_stats,
    get_branch3_sales_history
)
from handlers.common import get_user_role

router = Router()
logger = logging.getLogger(__name__)

# --- SOTUV JARAYONI ---

@router.message(F.text == "🛒 Sotuv")
async def start_branch3_sale(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch" or branch_id != 3:
        return
    await state.clear()
    await state.set_state(Branch3SaleStates.choosing_collection)
    await message.answer(
        "🛒 *Mahsulotni tanlang:*",
        parse_mode="Markdown",
        reply_markup=get_branch3_collections_kb()
    )

@router.callback_query(F.data.startswith("b3_coll:"), Branch3SaleStates.choosing_collection)
async def process_branch3_collection(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch" or branch_id != 3:
        return
    collection_name = callback.data.split(":")[1]
    if collection_name not in BRANCH3_COLLECTIONS:
        await callback.answer("Noto'g'ri tanlov!", show_alert=True)
        return
    price = BRANCH3_COLLECTIONS[collection_name]
    await state.update_data(collection_name=collection_name, price=price)
    await state.set_state(Branch3SaleStates.entering_length)

    await callback.message.edit_text(
        f"Tanlandi: *{collection_name}* (${price:g}/m²)\n\n"
        "Uzunligini metrda kiriting:\n"
        "(Masalan: `5` yoki `3.5`):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(Branch3SaleStates.entering_length)
async def process_branch3_length(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch" or branch_id != 3:
        return
    text = message.text.strip().replace(",", ".")
    try:
        length = float(text)
        if length <= 0:
            await message.answer("Uzunlik 0 dan katta bo'lishi kerak. Qaytadan kiriting:")
            return
    except ValueError:
        await message.answer("Iltimos, son kiriting (Masalan: `5` yoki `3.5`):")
        return

    length = round(length, 2)
    data = await state.get_data()
    collection_name = data["collection_name"]
    price = data["price"]

    area_m2 = round(BRANCH3_WIDTH * length, 2)
    total_price = round(area_m2 * price, 2)

    await state.update_data(length=length, area_m2=area_m2, total_price=total_price)
    await state.set_state(Branch3SaleStates.confirming)

    chek = (
        f"🧾 *Sotuv cheki:*\n\n"
        f"• Mahsulot: *{collection_name}*\n"
        f"• O'lcham: *{BRANCH3_WIDTH:g} x {length:g} m*\n"
        f"• Maydon: *{area_m2:.2f} m²*\n"
        f"• Narx: *${price:g} / m²*\n"
        f"💰 *Jami summa:* *${total_price:.2f}*\n\n"
        f"Sotuvni tasdiqlaysizmi?"
    )
    await message.answer(chek, parse_mode="Markdown", reply_markup=get_branch3_confirm_sale_kb())

@router.callback_query(F.data == "b3_retry_sale", Branch3SaleStates.confirming)
async def retry_branch3_sale(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch" or branch_id != 3:
        return
    await state.set_state(Branch3SaleStates.choosing_collection)
    await callback.message.edit_text(
        "🛒 *Mahsulotni tanlang:*",
        parse_mode="Markdown",
        reply_markup=get_branch3_collections_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "b3_confirm_sale", Branch3SaleStates.confirming)
async def confirm_branch3_sale(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch" or branch_id != 3:
        return
    data = await state.get_data()
    collection_name = data["collection_name"]
    length = data["length"]

    res = await make_branch3_sale(collection_name=collection_name, length=length, branch_id=3)

    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"✅ *Sotuv muvaffaqiyatli saqlandi!*\n\n"
        f"• Mahsulot: *{collection_name}* ({BRANCH3_WIDTH:g}x{length:g}m = {res['area_m2']:.2f} m²)\n"
        f"💰 *Qabul qilingan summa:* *${res['total_price']:.2f}*\n\n"
        f"💵 *Qo'lingizdagi jami kassa:* *${res['new_cash_balance']:.2f}*",
        parse_mode="Markdown",
        reply_markup=get_branch3_menu()
    )
    await callback.answer("Saqlandi!")

# --- HISOBOT VA TARIX ---

@router.message(F.text == "📊 Hisobot")
async def show_branch3_report(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch" or branch_id != 3:
        return
    await state.clear()

    stats = await get_branch3_stats(branch_id=3)

    coll_lines = []
    for coll, d in stats["by_collection"].items():
        coll_lines.append(f"  • {coll}: {d['m2']} m² (${d['rev']:.2f})")
    coll_text = "\n".join(coll_lines) if coll_lines else "  • Hozircha savdo yo'q"

    text = (
        f"📊 *3-Filial Hisoboti:*\n\n"
        f"💵 *QO'LINGIZDAGI KASSA:* *${stats['cash_balance']:.2f}*\n"
        f"📐 *Jami sotilgan maydon:* *{stats['total_m2']:.2f} m²*\n"
        f"🛒 *Jami sotuvlar soni:* *{stats['total_count']} ta*\n\n"
        f"📅 *Bugungi savdo:*\n"
        f"• Sotilgan maydon: *{stats['today_m2']:.2f} m²*\n"
        f"• Tushum: *${stats['today_rev']:.2f}* ({stats['today_count']} ta)\n\n"
        f"📦 *Kolleksiyalar bo'yicha:*\n"
        f"{coll_text}"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_branch3_report_kb())

@router.callback_query(F.data == "b3_history")
async def show_branch3_history(callback: CallbackQuery):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch" or branch_id != 3:
        return
    history = await get_branch3_sales_history(branch_id=3, limit=15)
    if not history:
        await callback.message.answer("Hozircha sotuvlar tarixi mavjud emas.")
        await callback.answer()
        return

    lines = ["📜 *OXIRGI SOTUVLAR TARIXI:*\n"]
    for idx, s in enumerate(history, start=1):
        lines.append(
            f"{idx}. *{s['collection_name']}* | 4x{s['length']:g}m ({s['area_m2']} m²)\n"
            f"   💰 *${s['total_price']:.2f}* (${s['price_per_m2']:g}/m²)\n"
            f"   📅 {s['created_at']}\n"
        )

    await callback.message.answer("\n".join(lines), parse_mode="Markdown")
    await callback.answer()
