
import asyncio

async def delete_after_delay(bot, chat_id: int, message_id: int, delay_seconds: int = 5):
    """Xabarni bir necha soniyadan so'ng chatdan tozalab tashlash (interfeys toza turishi uchun)"""
    try:
        await asyncio.sleep(delay_seconds)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from config import SUPER_ADMIN_IDS, BRANCH_USERS, BRANCH_NAMES, WEBAPP_URL
from web.auth import QR_REQUESTS, get_short_id_for_user

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
            if qr_token in QR_REQUESTS:
                QR_REQUESTS[qr_token]["status"] = "rejected"
            await message.answer("❌ Kechirasiz, sizning Telegram hisobingiz DRAP ERP xodimlari ro'yxatida yo'q. Tizimga kirish taqiqlangan.")
            return

        # Foydalanuvchi yuborgan /start login_... xabarini 5 soniyadan so'ng tozalash
        asyncio.create_task(delete_after_delay(message.bot, message.chat.id, message.message_id, 5))

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, kirishga ruxsat berish", callback_data=f"qr_approve:{qr_token}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"qr_reject:{qr_token}")
            ]
        ])
        await message.answer(
            "🖥 *Kompyuterdan tizimga kirish so'rovi!*\n\n"
            "Siz hozirgina kompyuteringizda DRAP ERP tizimiga kirish uchun QR-kodni skaner qildingiz.\n\n"
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
    short_id = get_short_id_for_user(user_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 DRAP ERP Tizimiga kirish", url=WEBAPP_URL)]
    ])

    msg = (
        f"Assalomu alaykum, *{first_name}*!\n\n"
        f"Sizning maqomingiz: *{role_label}*\n"
        f"🔑 **Sizning Xodim ID:** `{short_id}` (Telegram ID: `{user_id}`)\n\n"
        f"✨ *DRAP ERP tizimi to'liq faol!*\n"
        f"Web saytga kirish uchun **{short_id}** raqamini kiritib, botga keladigan OTP kod orqali yoki tezkor QR kod orqali kirishingiz mumkin.\n\n"
        f"🔗 Sayt: **{WEBAPP_URL}**"
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
            "✅ *Muvaffaqiyatli!* Kompyuteringizdagi tizimga kirdingiz.\n\nEndi brauzer orqali ishlashingiz mumkin.\n\n_Ushbu xabar 5 soniyadan so'ng avtomatik o'chiriladi..._",
            parse_mode="Markdown"
        )
        asyncio.create_task(delete_after_delay(callback.bot, callback.message.chat.id, callback.message.message_id, 5))
    else:
        await callback.message.edit_text(
            "❌ Xatolik: Kirish so'rovi topilmadi yoki muddati o'tib ketgan.",
            parse_mode="Markdown"
        )
        asyncio.create_task(delete_after_delay(callback.bot, callback.message.chat.id, callback.message.message_id, 6))
    await callback.answer()

@router.callback_query(F.data.startswith("qr_reject:"))
async def cb_qr_reject(callback: CallbackQuery):
    await callback.message.edit_text("❌ Tizimga kirish so'rovi bekor qilindi.")
    asyncio.create_task(delete_after_delay(callback.bot, callback.message.chat.id, callback.message.message_id, 5))
    await callback.answer()

# --- TRANSFERNI QABUL QILISH / RAD ETISH HANDLERLARI ---

@router.callback_query(F.data.startswith("tr_accept:"))
async def cb_transfer_accept(callback: CallbackQuery):
    transfer_id_str = callback.data.split(":", 1)[1]
    try:
        transfer_id = int(transfer_id_str)
    except ValueError:
        await callback.answer("Noto'g'ri transfer ID", show_alert=True)
        return

    user_id = callback.from_user.id
    role, branch_id = get_user_role(user_id)
    if not role:
        await callback.answer("Sizga ruxsat berilmagan!", show_alert=True)
        return

    from database import local_db
    try:
        user_name = callback.from_user.first_name or f"Foydalanuvchi {user_id}"
        res = await local_db.accept_transfer(transfer_id, accepted_by=f"{user_name} (Telegram)")
        to_name = BRANCH_NAMES.get(res["to_branch"], f"{res['to_branch']}-Filial")
        from_name = BRANCH_NAMES.get(res["from_branch"], f"{res['from_branch']}-Filial")
        
        await callback.message.edit_text(
            f"✅ *TRANSFER QABUL QILINDI!*\n\n"
            f"📍 *Qabul qiluvchi:* {to_name}\n"
            f"📍 *Jo'natuvchi:* {from_name}\n"
            f"📦 *Rulon:* {res.get('width')}m x {res.get('length')}m ({res.get('color')})\n"
            f"👤 *Qabul qildi:* {user_name}\n"
            f"⏰ *Vaqt:* {res.get('accepted_at')}\n\n"
            f"🎉 Mahsulot {to_name} omboriga muvaffaqiyatli kirim qilindi!",
            parse_mode="Markdown"
        )
        await callback.answer("✅ Transfer qabul qilindi va omboringizga qo'shildi!", show_alert=True)
    except Exception as e:
        await callback.answer(f"Xatolik: {str(e)}", show_alert=True)

@router.callback_query(F.data.startswith("tr_reject:"))
async def cb_transfer_reject(callback: CallbackQuery):
    transfer_id_str = callback.data.split(":", 1)[1]
    try:
        transfer_id = int(transfer_id_str)
    except ValueError:
        await callback.answer("Noto'g'ri transfer ID", show_alert=True)
        return

    user_id = callback.from_user.id
    role, branch_id = get_user_role(user_id)
    if not role:
        await callback.answer("Sizga ruxsat berilmagan!", show_alert=True)
        return

    from database import local_db
    try:
        user_name = callback.from_user.first_name or f"Foydalanuvchi {user_id}"
        tr = await local_db.reject_transfer(transfer_id, rejected_by=f"{user_name} (Telegram)")
        to_name = BRANCH_NAMES.get(tr["to_branch"], f"{tr['to_branch']}-Filial")
        from_name = BRANCH_NAMES.get(tr["from_branch"], f"{tr['from_branch']}-Filial")
        
        await callback.message.edit_text(
            f"❌ *TRANSFER RAD ETILDI!*\n\n"
            f"📍 *Rad etgan:* {to_name} ({user_name})\n"
            f"📍 *Jo'natuvchi:* {from_name}\n"
            f"📦 *Rulon:* {tr.get('width')}m x {tr.get('length')}m ({tr.get('color')})\n\n"
            f"ℹ️ Tovar {from_name} ombori balansida qoldi.",
            parse_mode="Markdown"
        )
        await callback.answer("❌ Transfer rad etildi.", show_alert=True)
    except Exception as e:
        await callback.answer(f"Xatolik: {str(e)}", show_alert=True)

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



@router.message(Command("id", "myid"))
async def cmd_myid(message: Message):
    user_id = message.from_user.id
    role, branch_id = get_user_role(user_id)
    if not role:
        await message.answer(f"❌ Siz tizim xodimi emassiz.\nSizning Telegram ID: <code>{user_id}</code>", parse_mode="HTML")
        return
    
    short_id = get_short_id_for_user(user_id)
    role_label = "👑 Bosh Admin" if role == "superadmin" else f"🏢 {BRANCH_NAMES.get(branch_id, 'Filial')} xodimi"
    
    await message.answer(
        f"👤 <b>Sizning DRAP ERP ma'lumotlaringiz:</b>\n\n"
        f"• <b>Xodim ID:</b> <code>{short_id}</code>\n"
        f"• <b>Telegram ID:</b> <code>{user_id}</code>\n"
        f"• <b>Vazifangiz:</b> {role_label}\n\n"
        f"💡 <i>Web saytga (<a href='{WEBAPP_URL}'>drap.uz</a>) kirayotganda ushbu <b>{short_id}</b> raqamini kiritib, "
        f"bir martalik OTP kod orqali kirishingiz mumkin.</i>",
        parse_mode="HTML"
    )
