import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from config import BRANCH_NAMES
from handlers.common import get_user_role
from keyboards.default_kb import get_branch_menu, get_superadmin_menu
from keyboards.inline_kb import (
    get_debts_main_kb, 
    get_debts_selection_kb, 
    get_confirm_pay_debt_kb
)
from utils.states import DebtPaymentStates
from database.local_db import (
    get_debts_summary,
    get_active_debts,
    get_debt_by_id,
    get_closed_debts,
    pay_debt
)

router = Router()
logger = logging.getLogger(__name__)

# --- NASIYA (QARZLAR) ASOSIY BO'LIMI ---

@router.message(F.text == "📒 Nasiya / Qarzlar")
async def show_debts_menu(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if not role:
        return
    await state.clear()
    
    summary = await get_debts_summary(branch_id=branch_id if role == "branch" else None)
    
    if role == "branch":
        b_name = BRANCH_NAMES.get(branch_id, "Filial")
        title = f"📒 *{b_name} — Nasiyalar (Qarzlar) Daftari*"
    else:
        title = "📒 *Barcha filiallar — Umumiy Nasiyalar Daftari*"
        
    text = (
        f"{title}\n\n"
        f"👥 Faol qarzdorlar soni: *{summary['active_count']} ta*\n"
        f"⏳ Jami kutilayotgan summa: *${summary['total_rem']:.2f}*\n"
        f"  • 🌀 Gilam bo'yicha: *${summary['carpet_rem']:.2f}*\n"
        f"  • 🐑 Teri bo'yicha: *${summary['leather_rem']:.2f}*\n\n"
        "Kerakli bo'limni tanlang:"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_debts_main_kb(is_superadmin=(role == "superadmin")))

@router.callback_query(F.data == "debts_menu")
async def cb_debts_menu(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if not role:
        return
    await state.clear()
    
    summary = await get_debts_summary(branch_id=branch_id if role == "branch" else None)
    if role == "branch":
        b_name = BRANCH_NAMES.get(branch_id, "Filial")
        title = f"📒 *{b_name} — Nasiyalar (Qarzlar) Daftari*"
    else:
        title = "📒 *Barcha filiallar — Umumiy Nasiyalar Daftari*"
        
    text = (
        f"{title}\n\n"
        f"👥 Faol qarzdorlar soni: *{summary['active_count']} ta*\n"
        f"⏳ Jami kutilayotgan summa: *${summary['total_rem']:.2f}*\n"
        f"  • 🌀 Gilam bo'yicha: *${summary['carpet_rem']:.2f}*\n"
        f"  • 🐑 Teri bo'yicha: *${summary['leather_rem']:.2f}*\n\n"
        "Kerakli bo'limni tanlang:"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_debts_main_kb(is_superadmin=(role == "superadmin")))
    await callback.answer()

# --- FAOL QARZLAR RO'YXATI ---

@router.callback_query(F.data == "debts_active_list")
async def show_active_debts(callback: CallbackQuery):
    role, branch_id = get_user_role(callback.from_user.id)
    if not role:
        return
        
    debts = await get_active_debts(branch_id=branch_id if role == "branch" else None)
    if not debts:
        await callback.message.edit_text(
            "✅ *Hozirda faol nasiyalar (qarzlar) mavjud emas!*\nBarcha mijozlar hisob-kitobni o'z vaqtida to'liq amalga oshirgan.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Ortga", callback_data="debts_menu")]
            ])
        )
        await callback.answer()
        return
        
    lines = ["📋 *FAOL NASIYALAR (QARZLAR) RO'YXATI:*\n"]
    buttons = []
    
    for idx, d in enumerate(debts, start=1):
        cat_emoji = "🌀" if d["category"] == "carpet" else "🐑"
        cat_name = "Gilam" if d["category"] == "carpet" else "Teri"
        b_name = BRANCH_NAMES.get(d["branch_id"], f"Filial-{d['branch_id']}")
        
        info = (
            f"*{idx}. #D-{d['id']} | {d['customer_name']}*\n"
            f"  • 🏢 Filial: {b_name}\n"
            f"  • 📞 Tel: `{d['customer_phone'] or 'Kiritilmagan'}`\n"
            f"  • {cat_emoji} Tovar: `{d['item_details']}` ({cat_name})\n"
            f"  • 💰 Jami sotuv: `${d['total_amount']:.2f}` | To'langan: `${d['paid_amount']:.2f}`\n"
            f"  • ⏳ *Qarz qoldig'i:* *${d['remaining_amount']:.2f}*\n"
            f"  • 📅 Berilgan sana: {d['created_at']}\n"
        )
        lines.append(info)
        
        # Har bir qarz uchun to'lash tugmasi
        if role == "branch" and d["branch_id"] == branch_id:
            buttons.append([InlineKeyboardButton(
                text=f"💰 To'lov: {d['customer_name']} (${d['remaining_amount']:.2f})", 
                callback_data=f"debt_pay_select:{d['id']}"
            )])
            
    buttons.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="debts_menu")])
    
    await callback.message.edit_text("\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

# --- QARZ TO'LOVINI QABUL QILISH ---

@router.callback_query(F.data == "debts_pay_start")
async def start_debt_payment(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        await callback.answer("Qarz to'lovini faqat tegishli filial xodimi qabul qilishi mumkin!", show_alert=True)
        return
        
    debts = await get_active_debts(branch_id=branch_id)
    if not debts:
        await callback.message.edit_text(
            "Sizning filialingizda hozirda to'lanishi kerak bo'lgan faol qarz yo'q.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Ortga", callback_data="debts_menu")]
            ])
        )
        await callback.answer()
        return
        
    await callback.message.edit_text(
        "💰 *Qarz to'lovini qabul qilish:*\n\nQaysi mijoz to'lov qilmoqda? Quyidagi ro'yxatdan tanlang:",
        parse_mode="Markdown",
        reply_markup=get_debts_selection_kb(debts)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("debt_pay_select:"))
async def select_debt_for_payment(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    debt_id = int(callback.data.split(":")[1])
    debt = await get_debt_by_id(debt_id)
    
    if not debt or debt["status"] == "paid" or debt["remaining_amount"] <= 0:
        await callback.message.edit_text(
            "Ushbu qarz allaqachon to'liq yopilgan!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Nasiyalar menyusi", callback_data="debts_menu")]
            ])
        )
        await callback.answer()
        return
        
    await state.update_data(debt_id=debt_id, debt=debt)
    await state.set_state(DebtPaymentStates.entering_payment_amount)
    
    cat_emoji = "🌀" if debt["category"] == "carpet" else "🐑"
    cat_name = "Gilam" if debt["category"] == "carpet" else "Teri"
    
    text = (
        f"💵 *Qarz to'lovini kiritish:*\n\n"
        f"🆔 Nasiya: *#D-{debt['id']}*\n"
        f"👤 Mijoz: *{debt['customer_name']}*\n"
        f"📞 Telefon: `{debt['customer_phone'] or 'Mavjud emas'}`\n"
        f"{cat_emoji} Mahsulot: `{debt['item_details']}` ({cat_name})\n"
        f"💰 Jami summa: `${debt['total_amount']:.2f}`\n"
        f"💳 To'langan: `${debt['paid_amount']:.2f}`\n"
        f"⏳ *Qolgan qarz miqdori:* *${debt['remaining_amount']:.2f}*\n\n"
        f"Qancha to'lov qabul qildingiz? Summani yozing (Masalan: `50` yoki to'liq to'langan bo'lsa `{debt['remaining_amount']:.2f}`):"
    )
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

@router.message(DebtPaymentStates.entering_payment_amount)
async def process_debt_payment_amount(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    text = message.text.strip().replace(",", ".")
    try:
        amount = float(text)
        if amount <= 0:
            await message.answer("To'lov summasi 0 dan katta bo'lishi kerak! Qaytadan kiriting:")
            return
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting (Masalan: `50` yoki `100.5`):")
        return
        
    data = await state.get_data()
    debt = data["debt"]
    rem = round(debt["remaining_amount"], 2)
    
    if amount > rem:
        await message.answer(
            f"❌ Xatolik! Kiritilgan summa qarz miqdoridan (${rem:.2f}) ko'p!\n\n"
            f"Iltimos, ${rem:.2f} dan oshmagan miqdor kiriting:"
        )
        return
        
    new_rem = round(rem - amount, 2)
    await state.update_data(payment_amount=amount, new_rem=new_rem)
    await state.set_state(DebtPaymentStates.confirming_payment)
    
    cat_name = "Gilam" if debt["category"] == "carpet" else "Teri"
    
    summary = (
        f"📝 *Qarz to'lovini tasdiqlang:*\n\n"
        f"👤 Mijoz: *{debt['customer_name']}*\n"
        f"💵 Qabul qilinayotgan summa: *+${amount:.2f}*\n"
        f"📥 Tushum kassasi: *{cat_name} kassasi*\n"
        f"⏳ To'lovdan so'ng qarz: *${new_rem:.2f}* "
        f"({'🎉 Qarz to\\'liq yopiladi' if new_rem <= 0.001 else 'Qisman to\\'lanadi'})\n\n"
        f"To'lovni tasdiqlaysizmi?"
    )
    await message.answer(summary, parse_mode="Markdown", reply_markup=get_confirm_pay_debt_kb(debt["id"]))

@router.callback_query(F.data.startswith("confirm_pay_debt:"), DebtPaymentStates.confirming_payment)
async def confirm_debt_payment(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    debt_id = data["debt_id"]
    payment_amount = data["payment_amount"]
    
    res = await pay_debt(debt_id=debt_id, payment_amount=payment_amount, branch_id=branch_id)
    
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    cat_title = "Gilam" if res["category"] == "carpet" else "Teri"
    status_str = "🎉 *QARZ TO'LIQ YOPILDI!*" if res["status"] == "paid" else f"⏳ *Qolgan qarz:* ${res['remaining_amount']:.2f}"
    
    receipt = (
        f"✅ *Qarz to'lovi muvaffaqiyatli qabul qilindi! ({b_name})*\n\n"
        f"🆔 Nasiya ID: *#D-{res['debt_id']}*\n"
        f"👤 Mijoz: *{res['customer_name']}*\n"
        f"📦 Mahsulot: `{res['item_details']}`\n"
        f"💵 To'langan summa: *+${res['payment_amount']:.2f}*\n"
        f"{status_str}\n\n"
        f"📥 *{cat_title} kassasiga qo'shildi:* +${res['payment_amount']:.2f}\n"
        f"💰 *Joriy {cat_title} kassa balansi:* ${res['new_cash_balance']:.2f}"
    )
    await callback.message.answer(receipt, parse_mode="Markdown", reply_markup=get_branch_menu(b_name))
    await callback.answer("Qabul qilindi!")

# --- YOPILGAN QARZLAR TARIXI ---

@router.callback_query(F.data == "debts_history")
async def show_debts_history(callback: CallbackQuery):
    role, branch_id = get_user_role(callback.from_user.id)
    if not role:
        return
        
    closed = await get_closed_debts(branch_id=branch_id if role == "branch" else None, limit=15)
    if not closed:
        await callback.message.edit_text(
            "Hozircha yopilgan qarzlar tarixi mavjud emas.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Ortga", callback_data="debts_menu")]
            ])
        )
        await callback.answer()
        return
        
    lines = ["📜 *OXIRGI YOPILGAN (TO'LANGAN) QARZLAR:*\n"]
    for idx, d in enumerate(closed, start=1):
        cat_name = "Gilam" if d["category"] == "carpet" else "Teri"
        b_name = BRANCH_NAMES.get(d["branch_id"], f"Filial-{d['branch_id']}")
        lines.append(
            f"{idx}. *#D-{d['id']} | {d['customer_name']}* ({b_name})\n"
            f"   • Tovar: `{d['item_details']}` ({cat_name})\n"
            f"   • Jami to'langan: `${d['paid_amount']:.2f}`\n"
            f"   • Yopilgan sana: {d['updated_at']}\n"
        )
        
    await callback.message.edit_text(
        "\n".join(lines), 
        parse_mode="Markdown", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Ortga", callback_data="debts_menu")]
        ])
    )
    await callback.answer()
