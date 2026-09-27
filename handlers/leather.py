import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import LEATHER_PRICE, BRANCH_NAMES
from keyboards.default_kb import get_leather_submenu, get_branch_menu
from keyboards.inline_kb import (
    get_leather_colors_kb,
    get_available_leather_colors_kb,
    get_confirm_leather_import_kb,
    get_confirm_leather_sale_kb,
    get_confirm_debt_sale_kb
)
from utils.states import LeatherImportStates, LeatherSaleStates
from database.local_db import (
    add_leather,
    make_leather_sale,
    get_leather_stock,
    get_available_leather_colors
)
from handlers.common import get_user_role

router = Router()
logger = logging.getLogger(__name__)

# --- MENYU O'TISHLARI ---

@router.message(F.text == "🐑 Teri Bo'limi")
async def open_leather_menu(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    await state.clear()
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await message.answer(
        f"🐑 *{b_name} — Teri Mahsulotlari Bo'limi*\n\n"
        f"• Donasi: *${LEATHER_PRICE:.2f}*\n"
        f"• Ranglar: Oppoq, Bejiviy, Seriy\n\n"
        "Kerakli amalni tanlang:",
        parse_mode="Markdown",
        reply_markup=get_leather_submenu()
    )

# --- TERI KIRIM (IMPORT) ---

@router.message(F.text == "📥 Teri Kirim")
async def start_leather_import(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    await state.clear()
    await state.set_state(LeatherImportStates.choosing_color)
    await message.answer("Qabul qilingan terining rangini tanlang:", reply_markup=get_leather_colors_kb("leather_import_color"))

@router.callback_query(F.data.startswith("leather_import_color:"), LeatherImportStates.choosing_color)
async def process_leather_import_color(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    color = callback.data.split(":")[1]
    await state.update_data(color=color)
    await state.set_state(LeatherImportStates.entering_quantity)
    
    await callback.message.edit_text(
        f"Tanlangan rang: *{color}*\n\n"
        "Necha dona qabul qilindi? (Faqat butun son kiriting, masalan: 10):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(LeatherImportStates.entering_quantity)
async def process_leather_import_quantity(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    text = message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("Iltimos, musbat butun son kiriting (Masalan: 10 yoki 5):")
        return
        
    quantity = int(text)
    data = await state.get_data()
    color = data["color"]
    total_val = round(quantity * LEATHER_PRICE, 2)
    
    await state.update_data(quantity=quantity, total_val=total_val)
    await state.set_state(LeatherImportStates.confirming)
    
    summary = (
        f"📦 *Yangi teri kirimini tasdiqlang:*\n\n"
        f"🐑 Mahsulot: *Teri*\n"
        f"🎨 Rangi: *{color}*\n"
        f"🔢 Miqdori: *{quantity} dona*\n"
        f"💵 Donasi: `${LEATHER_PRICE:.2f}`\n"
        f"💰 Tovar umumiy qiymati: *${total_val:.2f}*\n\n"
        f"Ma'lumotlar to'g'rimi?"
    )
    await message.answer(summary, parse_mode="Markdown", reply_markup=get_confirm_leather_import_kb())

@router.callback_query(F.data == "retry_leather_import", LeatherImportStates.confirming)
async def retry_leather_import(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    await state.set_state(LeatherImportStates.choosing_color)
    await callback.message.edit_text("Qabul qilingan terining rangini tanlang:", reply_markup=get_leather_colors_kb("leather_import_color"))
    await callback.answer()

@router.callback_query(F.data == "confirm_leather_import", LeatherImportStates.confirming)
async def confirm_leather_import(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    color = data["color"]
    quantity = data["quantity"]
    
    res = await add_leather(color=color, quantity=quantity, branch_id=branch_id)
    
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await callback.message.answer(
        f"✅ *Teri omborga muvaffaqiyatli qo'shildi! ({b_name})*\n\n"
        f"🎨 Rangi: *{color}*\n"
        f"➕ Qo'shildi: *+{quantity} dona*\n"
        f"📦 Ushbu rangdagi jami qoldiq: *{res['total_quantity']} dona*\n"
        f"💰 Qiymati ($50 dan): *${res['total_value']:.2f}*",
        parse_mode="Markdown",
        reply_markup=get_leather_submenu()
    )
    await callback.answer("Qabul qilindi!")

# --- TERI SOTUV ---

@router.message(F.text == "🛒 Teri Sotuv")
async def start_leather_sale(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    await state.clear()
    
    colors_stock = await get_available_leather_colors(branch_id=branch_id)
    if not colors_stock:
        await message.answer(
            "Omborda sotuvga mavjud teri yo'q! Avval '📥 Teri Kirim' bo'limidan mahsulot qo'shing.",
            reply_markup=get_leather_submenu()
        )
        return
        
    await state.set_state(LeatherSaleStates.choosing_color)
    await message.answer("Sotilayotgan terining rangini tanlang:", reply_markup=get_available_leather_colors_kb(colors_stock))

@router.callback_query(F.data.startswith("leather_sale_color:"), LeatherSaleStates.choosing_color)
async def process_leather_sale_color(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    color = callback.data.split(":")[1]
    await state.update_data(color=color)
    await state.set_state(LeatherSaleStates.entering_quantity)
    
    await callback.message.edit_text(
        f"Tanlangan rang: *{color}*\n\n"
        "Necha dona sotildi? (Soni yozing, masalan: 3):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(LeatherSaleStates.entering_quantity)
async def process_leather_sale_qty(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    text = message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("Iltimos, musbat butun son kiriting (Masalan: 3):")
        return
        
    quantity = int(text)
    data = await state.get_data()
    color = data["color"]
    
    # Qoldiqni tekshiramiz
    stocks = await get_available_leather_colors(branch_id=branch_id)
    avail = next((s["quantity"] for s in stocks if s["color"] == color), 0)
    
    if quantity > avail:
        await message.answer(
            f"❌ Xatolik! Omborda buncha {color} teri yo'q!\n"
            f"Mavjud qoldiq: *{avail} dona*.\n\n"
            f"Qaytadan kamroq miqdor kiriting:",
            parse_mode="Markdown"
        )
        return
        
    total_val = round(quantity * LEATHER_PRICE, 2)
    remains = avail - quantity
    await state.update_data(quantity=quantity, total_val=total_val, remains=remains)
    await state.set_state(LeatherSaleStates.confirming)
    
    summary = (
        f"🛒 *Teri sotuvini tasdiqlang:*\n\n"
        f"🎨 Rangi: *{color}*\n"
        f"🔢 Sotilmoqda: *{quantity} dona*\n"
        f"💵 Donasi: `${LEATHER_PRICE:.2f}`\n"
        f"💰 Jami sotuv summasi: *${total_val:.2f}*\n"
        f"✂️ Omborda qoladi: *{remains} dona*\n\n"
        f"To'lov turini tanlang yoki sotuvni tasdiqlang:"
    )
    await message.answer(summary, parse_mode="Markdown", reply_markup=get_confirm_leather_sale_kb())

@router.callback_query(F.data == "retry_leather_sale", LeatherSaleStates.confirming)
async def retry_leather_sale(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    colors_stock = await get_available_leather_colors(branch_id=branch_id)
    await state.set_state(LeatherSaleStates.choosing_color)
    await callback.message.edit_text("Sotilayotgan terining rangini tanlang:", reply_markup=get_available_leather_colors_kb(colors_stock))
    await callback.answer()

# 1. NAQD TERI SOTUV
@router.callback_query(F.data.in_(["confirm_leather_sale", "confirm_leather_sale_cash"]), LeatherSaleStates.confirming)
async def confirm_leather_sale(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    color = data["color"]
    quantity = data["quantity"]
    
    res = await make_leather_sale(color=color, quantity=quantity, branch_id=branch_id, is_debt=False)
    
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await callback.message.answer(
        f"✅ *Teri sotuvi muvaffaqiyatli amalga oshirildi! ({b_name})*\n"
        f"💵 *To'lov turi:* Naqd to'lov\n\n"
        f"🎨 Rangi: *{color}*\n"
        f"🔢 Sotildi: *{quantity} dona*\n"
        f"💰 Sotuv summasi: *${res['sale_total_price']:.2f}*\n"
        f"✂️ Ombordagi qoldiq: *{res['remaining_quantity']} dona*\n\n"
        f"💵 *Teri kassasiga qo'shildi:* +${res['sale_total_price']:.2f}\n"
        f"💰 *Joriy Teri kassa balansi:* ${res['new_leather_cash_balance']:.2f}",
        parse_mode="Markdown",
        reply_markup=get_leather_submenu()
    )
    await callback.answer("Sotildi!")

# 2. NASIYA (QARZ) TERI SOTUV OQIMI
@router.callback_query(F.data == "leather_debt_start", LeatherSaleStates.confirming)
async def start_leather_debt_flow(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    await state.set_state(LeatherSaleStates.entering_customer_name)
    await callback.message.edit_text(
        "📝 *Nasiya (Qarz) rasmiylashtirish:*\n\n"
        "Mijozning ismini kiriting (Masalan: Alisher aka yoki Rustam):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(LeatherSaleStates.entering_customer_name)
async def leather_debt_name(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    name = message.text.strip()
    if not name:
        await message.answer("Iltimos, mijoz ismini kiriting:")
        return
    await state.update_data(customer_name=name)
    await state.set_state(LeatherSaleStates.entering_customer_phone)
    await message.answer(
        f"Mijoz: *{name}*\n\n"
        "Telefon raqamini kiriting (Masalan: `+998901234567` yoki telefon bo'lmasa `/otkazish` deb yozing):",
        parse_mode="Markdown"
    )

@router.message(LeatherSaleStates.entering_customer_phone)
async def leather_debt_phone(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    text = message.text.strip()
    phone = "" if text.lower() in ["/otkazish", "otkazish", "-", "yoq", "yo'q"] else text
    await state.update_data(customer_phone=phone)
    
    data = await state.get_data()
    total_val = data["total_val"]
    
    await state.set_state(LeatherSaleStates.entering_initial_paid)
    await message.answer(
        f"💰 Jami sotuv summasi: *${total_val:.2f}*\n\n"
        "Mijoz boshlang'ich qisman to'lov qildimi?\n"
        "To'langan summani kiriting (agar umuman to'lamagan bo'lsa `0` deb yozing):",
        parse_mode="Markdown"
    )

@router.message(LeatherSaleStates.entering_initial_paid)
async def leather_debt_initial(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    text = message.text.strip().replace(",", ".")
    try:
        initial_paid = float(text)
        if initial_paid < 0:
            await message.answer("To'lov summasi manfiy bo'lishi mumkin emas. Qaytadan kiriting:")
            return
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting (Masalan: `50` yoki `0`):")
        return
        
    data = await state.get_data()
    total_val = data["total_val"]
    
    if initial_paid >= total_val:
        await message.answer(
            f"❌ Boshlang'ich to'lov jami summadan (${total_val:.2f}) kam bo'lishi kerak.\n"
            f"Agar mijoz to'liq to'lagan bo'lsa, 'Naqd to'lov' deb tasdiqlash lozim.\n\n"
            f"Iltimos, qaytadan boshlang'ich to'lov miqdorini kiriting (yoki 0):"
        )
        return
        
    remaining_debt = round(total_val - initial_paid, 2)
    await state.update_data(initial_paid=initial_paid, remaining_debt=remaining_debt)
    await state.set_state(LeatherSaleStates.confirming_debt)
    
    color = data["color"]
    quantity = data["quantity"]
    customer_name = data["customer_name"]
    customer_phone = data["customer_phone"]
    
    summary = (
        f"📋 *Nasiya (Qarz) teri sotuvini tasdiqlang:*\n\n"
        f"👤 Mijoz: *{customer_name}*\n"
        f"📞 Telefon: `{customer_phone or 'Kiritilmagan'}`\n"
        f"🎨 Rangi: *{color}*\n"
        f"🔢 Sotilmoqda: *{quantity} dona*\n"
        f"💰 Jami summa: *${total_val:.2f}*\n"
        f"💵 Boshlang'ich to'lov (kassaga tushadi): *${initial_paid:.2f}*\n"
        f"⏳ Qolgan qarz (Nasiya): *${remaining_debt:.2f}*\n\n"
        f"Nasiyani tasdiqlaysizmi?"
    )
    await message.answer(summary, parse_mode="Markdown", reply_markup=get_confirm_debt_sale_kb("leather"))

@router.callback_query(F.data == "retry_leather_debt", LeatherSaleStates.confirming_debt)
async def retry_leather_debt(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    await state.set_state(LeatherSaleStates.entering_customer_name)
    await callback.message.edit_text(
        "Mijozning ismini qaytadan kiriting:",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_leather_debt_final", LeatherSaleStates.confirming_debt)
async def confirm_leather_debt_final(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    color = data["color"]
    quantity = data["quantity"]
    customer_name = data["customer_name"]
    customer_phone = data["customer_phone"]
    initial_paid = data["initial_paid"]
    
    res = await make_leather_sale(
        color=color, 
        quantity=quantity, 
        branch_id=branch_id, 
        is_debt=True, 
        customer_name=customer_name, 
        customer_phone=customer_phone, 
        initial_paid=initial_paid
    )
    
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await callback.message.answer(
        f"✅ *Teri nasiyaga (qarzga) sotildi! ({b_name})*\n\n"
        f"🆔 Nasiya ID: *#D-{res['debt_id']}*\n"
        f"👤 Mijoz: *{customer_name}* ({customer_phone or 'Tel yo\\'q'})\n"
        f"🎨 Rangi: *{color}*\n"
        f"🔢 Miqdori: *{quantity} dona*\n"
        f"💰 Jami sotuv: *${res['sale_total_price']:.2f}*\n"
        f"💵 Boshlang'ich to'lov: *${res['initial_paid']:.2f}*\n"
        f"⏳ Qolgan qarz: *${res['remaining_debt']:.2f}*\n"
        f"✂️ Ombordagi qoldiq: {res['remaining_quantity']} dona\n\n"
        f"💵 *Teri kassasiga qo'shildi:* +${res['initial_paid']:.2f}\n"
        f"💰 *Joriy Teri kassa balansi:* ${res['new_leather_cash_balance']:.2f}",
        parse_mode="Markdown",
        reply_markup=get_leather_submenu()
    )
    await callback.answer("Nasiyaga sotildi!")


# --- TERI OMBOR QOLDIG'I ---

@router.message(F.text == "📦 Teri Ombori")
async def show_leather_inventory(message: Message):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    stocks = await get_leather_stock(branch_id=branch_id)
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    
    if not stocks:
        await message.answer(f"📦 {b_name} omborida teri mahsuloti mavjud emas!")
        return

    lines = [f"🐑 *{b_name} — TERI OMBOR QOLDIG'I:*\n"]
    total_qty = 0
    total_val = 0.0

    for idx, s in enumerate(stocks, start=1):
        v = round(s["quantity"] * s["price_per_item"], 2)
        total_qty += s["quantity"]
        total_val += v
        lines.append(f"{idx}. *{s['color']}*: `{s['quantity']} dona` (${v:.2f})")

    lines.append(f"\n🔢 *Jami teri soni:* `{total_qty} dona`")
    lines.append(f"💰 *Jami tovar qiymati ($50 dan):* `${round(total_val, 2):.2f}`")

    await message.answer("\n".join(lines), parse_mode="Markdown")
