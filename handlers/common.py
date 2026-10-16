import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from config import SUPER_ADMIN_IDS, BRANCH_USERS, BRANCH_NAMES
from keyboards.default_kb import get_branch_menu, get_superadmin_menu, get_carpet_submenu, get_branch3_menu, get_branch2_menu

router = Router()
logger = logging.getLogger(__name__)

# Super Admin qaysi filial rejimida ko'rayotganini saqlovchi xotira
ADMIN_ACTIVE_BRANCH: dict[int, int] = {}

def get_user_role(user_id: int):
    if user_id in SUPER_ADMIN_IDS:
        if user_id in ADMIN_ACTIVE_BRANCH:
            return "branch", ADMIN_ACTIVE_BRANCH[user_id]
        return "superadmin", None
    if user_id in BRANCH_USERS:
        branch_id = BRANCH_USERS[user_id]
        return "branch", branch_id
    return None, None

def get_user_menu(role: str, branch_id: int | None, user_id: int | None = None):
    is_admin = bool(user_id and user_id in SUPER_ADMIN_IDS and user_id in ADMIN_ACTIVE_BRANCH)
    if role == "superadmin":
        return get_superadmin_menu()
    if branch_id == 3:
        return get_branch3_menu(is_admin=is_admin)
    if branch_id == 2:
        return get_branch2_menu(is_admin=is_admin)
    return get_branch_menu(BRANCH_NAMES.get(branch_id, "Filial"), is_admin=is_admin)

@router.message(Command("admin"))
@router.message(F.text == "👑 Admin panelga qaytish")
async def back_to_admin_panel(message: Message, state: FSMContext):
    if message.from_user.id not in SUPER_ADMIN_IDS:
        return
    await state.clear()
    ADMIN_ACTIVE_BRANCH.pop(message.from_user.id, None)
    await message.answer(
        "👑 *Bosh Admin paneliga qaytdingiz.*\n\nKerakli bo'limni tanlang:",
        parse_mode="Markdown",
        reply_markup=get_superadmin_menu()
    )

@router.message(F.text.in_(["👁 Filial rejimiga o'tish (Ko'rish)", "👁 Filialga kirish"]))
async def open_switch_branch_menu(message: Message, state: FSMContext):
    if message.from_user.id not in SUPER_ADMIN_IDS:
        return
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 1-Filial (Barcha mahsulotlar)", callback_data="admin_view_branch:1")],
        [InlineKeyboardButton(text="🏢 2-Filial (Faqat Rezinka gilam)", callback_data="admin_view_branch:2")],
        [InlineKeyboardButton(text="🏢 3-Filial (Omborsiz savdo)", callback_data="admin_view_branch:3")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ])
    await message.answer(
        "👁 *Filial rejimiga o'tish:*\n\n"
        "Qaysi filial nomidan kirib, tizimni ko'rmoqchisiz? Tanlang:",
        parse_mode="Markdown",
        reply_markup=kb
    )

@router.callback_query(F.data.startswith("admin_view_branch:"))
async def process_switch_branch(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    if callback.from_user.id not in SUPER_ADMIN_IDS:
        return
    await state.clear()
    target_branch = int(callback.data.split(":")[1])
    ADMIN_ACTIVE_BRANCH[callback.from_user.id] = target_branch
    
    b_name = BRANCH_NAMES.get(target_branch, f"{target_branch}-Filial")
    menu = get_user_menu("branch", target_branch, user_id=callback.from_user.id)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    if target_branch == 3:
        detail = "Siz *3-Filial* savdo tizimidasiz.\n(Mahsulotlar: Laughton, Craft, Pretty — Ombor yo'q)"
    elif target_branch == 2:
        detail = f"Siz *{b_name} (Faqat Rezinka Gilam)* tizimidasiz.\n(Mahsulotlar: Rezinka gilam kirim/sotuv, kassa, ombor, hisobot)"
    else:
        detail = f"Siz *{b_name}* to'liq tizimidasiz.\n(Mahsulotlar: Rezinka Gilam, Teri, Asl Kavralan)"
        
    await callback.message.answer(
        f"✅ *{b_name} rejimiga muvaffaqiyatli o'tdingiz!*\n\n"
        f"{detail}\n\n"
        f"💡 _Ushbu filial xodimlari botda nimani ko'rsa, sizga ham xuddi shunday ko'rinadi va barcha funksiyalarni sinab ko'rishingiz mumkin._\n\n"
        f"👑 Admin paneliga qaytish uchun pastdagi *'👑 Admin panelga qaytish'* tugmasini bosing yoki /admin buyrug'ini yuboring.",
        parse_mode="Markdown",
        reply_markup=menu
    )

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # 1. QR kod yoki brauzerdan kirish so'rovi tekshiruvi (/start login_<token>)
    text_parts = (message.text or "").split(maxsplit=1)
    if len(text_parts) > 1 and text_parts[1].startswith("login_"):
        qr_token = text_parts[1].replace("login_", "").strip()
        role, branch_id = get_user_role(user_id)
        if not role:
            await message.answer("❌ Kechirasiz, sizga CRM tizimidan foydalanishga ruxsat berilmagan.")
            return

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, kirishga ruxsat berish", callback_data=f"qr_approve:{qr_token}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"qr_reject:{qr_token}")
            ]
        ])
        await message.answer(
            "🖥 *Kompyuterdan tizimga kirish so'rovi!*\n\n"
            "Siz hozirgina kompyuteringizda DRAP CRM tizimiga kirish uchun QR-kodni skaner qildingiz.\n\n"
            "Tizimga kirishga ruxsat berasizmi?",
            parse_mode="Markdown",
            reply_markup=kb
        )
        return

    if user_id in SUPER_ADMIN_IDS:
        ADMIN_ACTIVE_BRANCH.pop(user_id, None)
        await state.clear()
        first_name = message.from_user.first_name or "Bosh Admin"
        msg = (
            f"Assalomu alaykum, Hurmatli Bosh Admin ({first_name})!\n\n"
            "Siz tizimdagi barcha filiallarning Gilam, Teri, Asl Kavralan va 3-Filial mahsulotlari hisobini to'liq nazorat qilish huquqiga egasiz.\n\n"
            "Kerakli filialni yoki umumiy hisobotni tanlang, yoki filiallar rejimiga o'ting:"
        )
        await message.answer(msg, reply_markup=get_superadmin_menu())
        return

    role, branch_id = get_user_role(user_id)
    if not role:
        await message.answer("Kechirasiz, siz ushbu tizimdan foydalana olmaysiz. (Ruxsat berilmagan foydalanuvchi)")
        return
    await state.clear()
    first_name = message.from_user.first_name or "Foydalanuvchi"
    
    if branch_id == 3:
        msg = (
            f"Assalomu alaykum, {first_name}!\n\n"
            f"Siz *3-Filial* savdo tizimiga ulandingiz.\n"
            "Kerakli bo'limni tanlang:"
        )
        await message.answer(msg, parse_mode="Markdown", reply_markup=get_branch3_menu())
    elif branch_id == 2:
        b_name = BRANCH_NAMES.get(branch_id, "2-Filial")
        msg = (
            f"Assalomu alaykum, {first_name}!\n\n"
            f"Siz *{b_name} (Rezinka Gilam)* savdo tizimiga ulandingiz.\n"
            "Kerakli bo'limni tanlang:"
        )
        await message.answer(msg, parse_mode="Markdown", reply_markup=get_branch2_menu())
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
    if role != "branch" or branch_id in [2, 3]:
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
    menu = get_user_menu(role, branch_id, user_id=message.from_user.id)
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
    menu = get_user_menu(role, branch_id, user_id=callback.from_user.id)
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
    menu = get_user_menu(role, branch_id, user_id=callback.from_user.id)
    await callback.message.answer("Asosiy menyu:", reply_markup=menu)
    await callback.answer()

# --- QR KOD BILAN KIRISHNI TASDIQLASH HANDLERLARI ---

@router.callback_query(F.data.startswith("qr_approve:"))
async def cb_qr_approve(callback: CallbackQuery):
    qr_token = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    user_info = {
        "id": user_id,
        "first_name": callback.from_user.first_name,
        "username": callback.from_user.username
    }
    from web.auth import approve_qr_request
    success = approve_qr_request(qr_token, user_id, user_info)
    if success:
        await callback.message.edit_text(
            "✅ *Muvaffaqiyatli!* Kompyuteringizdagi tizimga kirdingiz.\n\nEndi brauzer orqali ishlashingiz mumkin.",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "❌ Xatolik: Kirish so'rovi topilmadi yoki muddati o'tib ketgan.",
            parse_mode="Markdown"
        )
    await callback.answer()

@router.callback_query(F.data.startswith("qr_reject:"))
async def cb_qr_reject(callback: CallbackQuery):
    await callback.message.edit_text("❌ Tizimga kirish so'rovi bekor qilindi.")
    await callback.answer()

@router.message(Command("crm"))
@router.message(F.text == "🌐 CRM Veb-tizimni ochish")
async def cmd_open_crm(message: Message):
    role, branch_id = get_user_role(message.from_user.id)
    if not role:
        return
    from config import WEBAPP_URL
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 DRAP CRM Saytini ochish", url=WEBAPP_URL)]
    ])
    await message.answer(
        f"🌐 *DRAP CRM Veb-Tizimi:*\n\n"
        f"🔗 Manzil: {WEBAPP_URL}\n\n"
        f"Kompyuterdan kirmoqchi bo'lsangiz, havolani brauzerda oching va ekrandagi QR kodni Telegram orqali tasdiqlang.",
        parse_mode="Markdown",
        reply_markup=kb
    )

