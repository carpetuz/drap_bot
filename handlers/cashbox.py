import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import BRANCH_NAMES
from keyboards.default_kb import get_branch_menu
from keyboards.inline_kb import get_cash_categories_kb, get_confirm_withdraw_kb
from utils.states import CashStates
from database.local_db import get_cash_balance, withdraw_cash
from handlers.common import get_user_role

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "💵 Kassa")
async def show_cash(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    await state.clear()
    
    carpet_balance = await get_cash_balance(branch_id=branch_id, category="carpet")
    leather_balance = await get_cash_balance(branch_id=branch_id, category="leather")
    kavralan_balance = await get_cash_balance(branch_id=branch_id, category="kavralan")
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    
    text = (
        f"💵 *{b_name} — KASSA VA TOPSHIRISH BO'LIMI:*\n\n"
        f"🌀 *Gilam kassasi qoldig'i:* `${carpet_balance:.2f}`\n"
        f"🐑 *Teri kassasi qoldig'i:* `${leather_balance:.2f}`\n"
        f"🧶 *Kavralan kassasi qoldig'i:* `${kavralan_balance:.2f}`\n\n"
        f"⚠️ *Eslatma:* Kassalar alohida topshiriladi. Topshirmoqchi bo'lgan kassangizni tanlang:"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_cash_categories_kb())

@router.callback_query(F.data.startswith("withdraw_cat:"))
async def choose_withdraw_category(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    category = callback.data.split(":")[1]  # 'carpet', 'leather', or 'kavralan'
    balance = await get_cash_balance(branch_id=branch_id, category=category)
    cat_name = "🌀 Gilam" if category == "carpet" else ("🐑 Teri" if category == "leather" else "🧶 Kavralan")
    
    if balance <= 0:
        await callback.message.answer(f"{cat_name} kassasida topshirish uchun pul mavjud emas ($0.00).")
        await callback.answer()
        return
        
    await state.update_data(category=category, balance=balance)
    await state.set_state(CashStates.entering_withdrawal_amount)
    
    await callback.message.edit_text(
        f"Tanlangan: *{cat_name} kassasi*\n"
        f"Mavjud kassa: *${balance:.2f}*\n\n"
        f"Qancha kassa berdingiz? Summani yozing (Masalan: 150):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(CashStates.entering_withdrawal_amount)
async def process_withdraw_amount(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    text = message.text.strip().replace(",", ".").replace("$", "")
    try:
        amount = float(text)
        if amount <= 0:
            await message.answer("Summa 0 dan katta bo'lishi kerak! Qaytadan kiriting:")
            return
    except ValueError:
        await message.answer("Iltimos, to'g'ri summa kiriting (Masalan: 150):")
        return

    data = await state.get_data()
    category = data["category"]
    balance = await get_cash_balance(branch_id=branch_id, category=category)
    cat_name = "🌀 Gilam" if category == "carpet" else ("🐑 Teri" if category == "leather" else "🧶 Kavralan")
    
    if amount > balance:
        await message.answer(
            f"❌ Xatolik! {cat_name} kassasida buncha mablag' yo'q!\n"
            f"Mavjud kassa: *${balance:.2f}*.\n\n"
            f"Qaytadan kiriting:",
            parse_mode="Markdown"
        )
        return

    new_balance = round(balance - amount, 2)
    await state.update_data(amount=amount, new_balance=new_balance)
    await state.set_state(CashStates.confirming_withdrawal)
    
    await message.answer(
        f"📤 *Kassa topshirishni tasdiqlang: ({cat_name} kassasi)*\n\n"
        f"Mavjud edi: `${balance:.2f}`\n"
        f"Topshirilmoqda: *-${amount:.2f}*\n"
        f"Kassada qoladigan pul: *${new_balance:.2f}*\n\n"
        f"Tasdiqlaysizmi?",
        parse_mode="Markdown",
        reply_markup=get_confirm_withdraw_kb()
    )

@router.callback_query(F.data == "confirm_withdraw", CashStates.confirming_withdrawal)
async def confirm_withdraw(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    amount = data["amount"]
    category = data["category"]
    cat_name = "🌀 Gilam" if category == "carpet" else ("🐑 Teri" if category == "leather" else "🧶 Kavralan")
    
    res = await withdraw_cash(amount=amount, branch_id=branch_id, category=category, note=f"Kassa topshirildi ({cat_name})")
    
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await callback.message.answer(
        f"✅ *{cat_name} kassasi muvaffaqiyatli topshirildi! ({b_name})*\n\n"
        f"📤 Chiqim summasi: *${res['amount']:.2f}*\n"
        f"💰 {cat_name} kassasidagi yangi qoldiq: *${res['new_balance']:.2f}*",
        parse_mode="Markdown",
        reply_markup=get_branch_menu(b_name)
    )
    await callback.answer("Topshirildi!")
