import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import BRANCH_NAMES
from keyboards.default_kb import get_branch_menu
from keyboards.inline_kb import get_cash_menu_kb, get_confirm_withdraw_kb
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
    balance = await get_cash_balance(branch_id=branch_id)
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await message.answer(
        f"💵 *KASSA VA PUL TOPSHIRISH ({b_name}):*\n\n"
        f"💰 Hozirgi kassadagi qoldiq summa: *${balance:.2f}*\n\n"
        f"Pul topshirish (chiqim qilish) uchun quyidagi tugmani bosing:",
        parse_mode="Markdown",
        reply_markup=get_cash_menu_kb()
    )

@router.callback_query(F.data == "cash_withdraw")
async def start_withdraw(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    balance = await get_cash_balance(branch_id=branch_id)
    if balance <= 0:
        await callback.message.answer("Kassada topshirish uchun pul mavjud emas ($0.00).")
        await callback.answer()
        return
        
    await state.set_state(CashStates.entering_withdrawal_amount)
    await callback.message.edit_text(
        f"Joriy kassa: *${balance:.2f}*\n\n"
        "Qancha kassa berdingiz? Summani yozing (Masalan: 325 yoki 100):",
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
        await message.answer("Iltimos, to'g'ri summa kiriting (Masalan: 325):")
        return

    balance = await get_cash_balance(branch_id=branch_id)
    if amount > balance:
        await message.answer(
            f"❌ Xatolik! Kassada buncha mablag' yo'q!\n"
            f"Mavjud kassa: *${balance:.2f}*.\n\n"
            f"Qaytadan kiriting:",
            parse_mode="Markdown"
        )
        return

    new_balance = round(balance - amount, 2)
    await state.update_data(amount=amount, new_balance=new_balance)
    await state.set_state(CashStates.confirming_withdrawal)
    
    await message.answer(
        f"📤 *Kassa topshirishni tasdiqlang:*\n\n"
        f"Oldingi balans: `${balance:.2f}`\n"
        f"Topshirilayotgan summa: *-${amount:.2f}*\n"
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
    
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    res = await withdraw_cash(amount=amount, branch_id=branch_id, note="Kassa topshirildi")
    
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        f"✅ *Kassa muvaffaqiyatli topshirildi! ({b_name})*\n\n"
        f"📤 Chiqim summasi: *${res['amount']:.2f}*\n"
        f"💰 Kassadagi yangi qoldiq: *${res['new_balance']:.2f}*",
        parse_mode="Markdown",
        reply_markup=get_branch_menu(b_name)
    )
    await callback.answer("Topshirildi!")
