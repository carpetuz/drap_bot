import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from config import SUPER_ADMIN_IDS, BRANCH_USERS, BRANCH_NAMES, WEBAPP_URL

router = Router()
logger = logging.getLogger(__name__)

def get_user_role(user_id: int):
    if user_id in SUPER_ADMIN_IDS:
        return "superadmin", 1
    if user_id in BRANCH_USERS:
        return "branch", BRANCH_USERS[user_id]
    return None, None

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
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

    # 2. Oddiy /start yuborilganda:
    role, branch_id = get_user_role(user_id)
    if not role:
        await message.answer("❌ Kechirasiz, sizga ushbu tizimdan foydalanishga ruxsat berilmagan (ID ro'yxatda yo'q).")
        return

    first_name = message.from_user.first_name or "Foydalanuvchi"
    role_label = "👑 Bosh Admin" if role == "superadmin" else f"🏢 {BRANCH_NAMES.get(branch_id, 'Filial')} xodimi"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 DRAP CRM Veb-Tizimiga kirish", url=WEBAPP_URL)]
    ])

    msg = (
        f"Assalomu alaykum, *{first_name}*!\n\n"
        f"Sizning maqomingiz: *{role_label}*\n\n"
        f"✨ *DRAP CRM tizimi to'liq veb-formatga o'tkazildi!*\n"
        f"Barcha savdo amallari (Sotuv, Kirim, Ombor qoldiqlari, Filiallararo transfer, Nasiyalar, Rasxod va Kassa) "
        f"endi to'liq veb-sayt orqali boshqariladi.\n\n"
        f"🔗 Sayt manzili: **{WEBAPP_URL}**\n\n"
        f"Kompyuterdan kirish uchun brauzeringizda saytni oching va ekrandagi QR kodni Telegram orqali tasdiqlang."
    )

    # Remove any old reply keyboard and show web link
    await message.answer(msg, parse_mode="Markdown", reply_markup=kb)

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

# Qolgan barcha matnli xabarlar uchun yo'naltirish
@router.message()
async def all_other_messages(message: Message):
    role, _ = get_user_role(message.from_user.id)
    if not role:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Saytga o'tish (drap.uz)", url=WEBAPP_URL)]
    ])
    await message.answer(
        "ℹ️ Barcha amallar (Sotuv, Kirim, Ombor, Transfer, Kassa) endi faqat **drap.uz** veb-sayti orqali amalga oshiriladi.\n\n"
        "Quyidagi tugma orqali saytga kiring:",
        parse_mode="Markdown",
        reply_markup=kb
    )

