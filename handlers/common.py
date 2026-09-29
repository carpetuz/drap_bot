import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import SUPER_ADMIN_IDS, BRANCH_USERS, BRANCH_NAMES
from keyboards.default_kb import get_branch_menu, get_superadmin_menu, get_carpet_submenu, get_branch3_menu

router = Router()
logger = logging.getLogger(__name__)

def get_user_role(user_id: int):
    if user_id in SUPER_ADMIN_IDS:
        return "superadmin", None
    if user_id in BRANCH_USERS:
        branch_id = BRANCH_USERS[user_id]
        return "branch", branch_id
    return None, None

def get_user_menu(role: str, branch_id: int | None):
    if role == "superadmin":
        return get_superadmin_menu()
    if branch_id == 3:
        return get_branch3_menu()
    return get_branch_menu(BRANCH_NAMES.get(branch_id, "Filial"))

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if not role:
        await message.answer("Kechirasiz, siz ushbu tizimdan foydalana olmaysiz. (Ruxsat berilmagan foydalanuvchi)")
        return
    await state.clear()
    first_name = message.from_user.first_name or "Foydalanuvchi"
    
    if role == "superadmin":
        msg = (
            f"Assalomu alaykum, Hurmatli Bosh Admin ({first_name})!\n\n"
            "Siz tizimdagi barcha filiallarning Gilam, Teri, Asl Kavralan va 3-Filial mahsulotlari hisobini to'liq nazorat qilish huquqiga egasiz.\n"
            "Kerakli filialni yoki umumiy hisobotni tanlang:"
        )
        await message.answer(msg, reply_markup=get_superadmin_menu())
    elif branch_id == 3:
        msg = (
            f"Assalomu alaykum, {first_name}!\n\n"
            f"Siz *3-Filial* savdo tizimiga ulandingiz.\n"
            "Kerakli bo'limni tanlang:"
        )
        await message.answer(msg, parse_mode="Markdown", reply_markup=get_branch3_menu())
    else:
        b_name = BRANCH_NAMES.get(branch_id, f"Filial-{branch_id}")
        msg = (
            f"Assalomu alaykum, {first_name}!\n\n"
            f"Siz *{b_name}* CRM tizimiga ulandingiz.\n"
            "Kerakli bo'limni tanlang:"
        )
        await message.answer(msg, parse_mode="Markdown", reply_markup=get_branch_menu(b_name))

@router.message(F.text == "🌀 Rezinka Gilam")
async def open_carpet_menu(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch" or branch_id == 3:
        return
    await state.clear()
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await message.answer(
        f"🌀 *{b_name} — Rezinka Gilam Bo'limi*\n\nKerakli amalni tanlang:",
        parse_mode="Markdown",
        reply_markup=get_carpet_submenu()
    )

@router.message(F.text == "🔙 Bosh menyu")
@router.message(F.text == "❌ Bekor qilish")
async def btn_cancel(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if not role:
        return
    await state.clear()
    menu = get_user_menu(role, branch_id)
    await message.answer("Bosh menyu:", reply_markup=menu)

@router.callback_query(F.data == "cancel_action")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if not role:
        return
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    menu = get_user_menu(role, branch_id)
    await callback.message.answer("Amal bekor qilindi.", reply_markup=menu)
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if not role:
        return
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    menu = get_user_menu(role, branch_id)
    await callback.message.answer("Asosiy menyu:", reply_markup=menu)
    await callback.answer()
