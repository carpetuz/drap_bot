import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from keyboards.default_kb import get_main_menu

router = Router()
logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Kechirasiz, siz ushbu botdan foydalana olmaysiz. (Faqat ruxsat etilgan admin uchun)")
        return
    await state.clear()
    first_name = message.from_user.first_name or "Admin"
    welcome_msg = (
        f"Assalomu alaykum, {first_name}!\n\n"
        "Rezinka gilam rulonlari CRM tizimiga xush kelibsiz.\n"
        "Kerakli bo'limni tanlang:"
    )
    await message.answer(welcome_msg, reply_markup=get_main_menu())

@router.message(F.text == "❌ Bekor qilish")
async def btn_cancel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("Amal bekor qilindi.", reply_markup=get_main_menu())

@router.callback_query(F.data == "cancel_action")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("Amal bekor qilindi.", reply_markup=get_main_menu())
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu())
    await callback.answer()
