import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import KAVRALAN_PRICE, KAVRALAN_WIDTH, BRANCH_NAMES
from keyboards.default_kb import get_kavralan_submenu, get_branch_menu
from keyboards.inline_kb import (
    get_confirm_kavralan_import_kb,
    get_kavralan_rolls_selection_kb,
    get_confirm_kavralan_sale_kb,
    get_confirm_debt_sale_kb
)
from utils.states import KavralanImportStates, KavralanSaleStates
from database.local_db import (
    add_kavralan_roll,
    make_kavralan_sale,
    get_available_kavralan_rolls,
    get_kavralan_roll_by_id
)
from handlers.common import get_user_role

router = Router()
logger = logging.getLogger(__name__)

# --- MENYU O'TISHLARI ---

@router.message(F.text == "🧶 Asl Kavralan")
async def open_kavralan_menu(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    await state.clear()
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await message.answer(
        f"🧶 *{b_name} — Asl Kavralan Bo'limi*\n\n"
        f"• Eni: *{KAVRALAN_WIDTH:g} metr (4x)*\n"
        f"• Narxi: *${KAVRALAN_PRICE:.2f} / m²*\n\n"
        "Kerakli amalni tanlang:",
        parse_mode="Markdown",
        reply_markup=get_kavralan_submenu()
    )

# --- KAVRALAN KIRIM (IMPORT) ---

@router.message(F.text == "📥 Kavralan Kirim")
async def start_kavralan_import(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    await state.clear()
    await state.set_state(KavralanImportStates.entering_length)
    await message.answer(
        f"📥 *Yangi Asl Kavralan kirimi ({KAVRALAN_WIDTH:g}x)*\n\n"
        "Kavralan rulonining uzunligini (metrda) kiriting:\n"
        "(Masalan: `25` yoki `20.5`):",
        parse_mode="Markdown"
    )

@router.message(KavralanImportStates.entering_length)
async def process_kavralan_import_length(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    text = message.text.strip().replace(",", ".")
    try:
        length = float(text)
        if length <= 0:
            await message.answer("Uzunlik 0 dan katta bo'lishi kerak. Qaytadan kiriting:")
            return
    except ValueError:
        await message.answer("Iltimos, son kiriting (Masalan: `25` yoki `20.5`):")
        return

    length = round(length, 2)
    area_m2 = round(KAVRALAN_WIDTH * length, 2)
    total_val = round(area_m2 * KAVRALAN_PRICE, 2)

    await state.update_data(length=length, area_m2=area_m2, total_val=total_val)
    await state.set_state(KavralanImportStates.confirming)

    summary = (
        f"📦 *Yangi Kavralan kirimini tasdiqlang:*\n\n"
        f"🧶 Mahsulot: *Asl Kavralan*\n"
        f"📏 O'lchami: *{KAVRALAN_WIDTH:g} x {length} m*\n"
        f"📐 Maydoni: *{area_m2:.2f} m²*\n"
        f"💵 Narxi: *${KAVRALAN_PRICE:.2f} / m²*\n"
        f"💰 Tovar umumiy qiymati: *${total_val:.2f}*\n\n"
        f"Ma'lumotlar to'g'rimi?"
    )
    await message.answer(summary, parse_mode="Markdown", reply_markup=get_confirm_kavralan_import_kb())

@router.callback_query(F.data == "retry_kavralan_import", KavralanImportStates.confirming)
async def retry_kavralan_import(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    await state.set_state(KavralanImportStates.entering_length)
    await callback.message.edit_text(
        f"📥 Kavralan rulonining uzunligini (metrda) qaytadan kiriting:\n(Masalan: `25` yoki `20.5`):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_kavralan_import", KavralanImportStates.confirming)
async def confirm_kavralan_import(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    length = data["length"]

    res = await add_kavralan_roll(length=length, branch_id=branch_id)

    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass

    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await callback.message.answer(
        f"✅ *Asl Kavralan omborga muvaffaqiyatli qo'shildi! ({b_name})*\n\n"
        f"🆔 Rulon kodi: *{res['roll_code']}*\n"
        f"📏 O'lchami: *{KAVRALAN_WIDTH:g} x {res['current_length']} m*\n"
        f"📐 Maydoni: *{res['area_m2']:.2f} m²*\n"
        f"💰 Qiymati ($30 dan): *${res['total_price']:.2f}*",
        parse_mode="Markdown",
        reply_markup=get_kavralan_submenu()
    )
    await callback.answer("Qabul qilindi!")

# --- KAVRALAN SOTUV ---

@router.message(F.text == "🛒 Kavralan Sotuv")
async def start_kavralan_sale(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    await state.clear()

    rolls = await get_available_kavralan_rolls(branch_id=branch_id)
    if not rolls:
        await message.answer(
            "Omborda sotuvga mavjud Kavralan ruloni yo'q!\nAvval '📥 Kavralan Kirim' bo'limidan qo'shing.",
            reply_markup=get_kavralan_submenu()
        )
        return

    await state.set_state(KavralanSaleStates.choosing_roll)
    await message.answer(
        "Sotilayotgan Kavralan rulonini tanlang:",
        reply_markup=get_kavralan_rolls_selection_kb(rolls)
    )

@router.callback_query(F.data.startswith("kavralan_sale_roll:"), KavralanSaleStates.choosing_roll)
async def process_kavralan_sale_roll(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    roll_id = int(callback.data.split(":")[1])
    roll = await get_kavralan_roll_by_id(roll_id)
    if not roll:
        await callback.answer("Rulon topilmadi!", show_alert=True)
        return

    await state.update_data(roll_id=roll_id, roll_code=roll["roll_code"], current_length=roll["current_length"])
    await state.set_state(KavralanSaleStates.entering_sold_length)

    await callback.message.edit_text(
        f"Tanlangan rulon: *{roll['roll_code']}*\n"
        f"Mavjud o'lcham: *{KAVRALAN_WIDTH:g} x {roll['current_length']} m* ({roll['area_m2']} m²)\n\n"
        "Necha metr kesib sotildi? (Uzunligini metrda kiriting, masalan: `3.5` yoki `5`):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(KavralanSaleStates.entering_sold_length)
async def process_kavralan_sale_length(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    text = message.text.strip().replace(",", ".")
    try:
        sold_length = float(text)
        if sold_length <= 0:
            await message.answer("Sotilayotgan uzunlik 0 dan katta bo'lishi kerak:")
            return
    except ValueError:
        await message.answer("Iltimos, son kiriting (Masalan: `3.5` yoki `5`):")
        return

    data = await state.get_data()
    roll_id = data["roll_id"]
    roll = await get_kavralan_roll_by_id(roll_id)
    if not roll or roll["current_length"] < sold_length:
        avail = roll["current_length"] if roll else 0
        await message.answer(
            f"❌ Rulonda yetarli uzunlik yo'q!\n"
            f"Mavjud qoldiq: *{avail} metr*.\n\n"
            f"Qaytadan kamroq uzunlik kiriting:",
            parse_mode="Markdown"
        )
        return

    sold_length = round(sold_length, 2)
    sold_area = round(KAVRALAN_WIDTH * sold_length, 2)
    total_val = round(sold_area * KAVRALAN_PRICE, 2)
    remaining_length = round(roll["current_length"] - sold_length, 2)

    await state.update_data(
        sold_length=sold_length,
        sold_area=sold_area,
        total_val=total_val,
        remaining_length=remaining_length
    )
    await state.set_state(KavralanSaleStates.confirming)

    summary = (
        f"🛒 *Kavralan sotuvini tasdiqlang:*\n\n"
        f"🆔 Rulon: *{roll['roll_code']}*\n"
        f"✂️ Kesilayotgan o'lcham: *{KAVRALAN_WIDTH:g} x {sold_length} m*\n"
        f"📐 Maydoni: *{sold_area:.2f} m²*\n"
        f"💵 Narxi: *${KAVRALAN_PRICE:.2f} / m²*\n"
        f"💰 Jami sotuv summasi: *${total_val:.2f}*\n"
        f"📏 Rulonda qoladi: *{remaining_length} m*\n\n"
        f"To'lov turini tanlang yoki sotuvni tasdiqlang:"
    )
    await message.answer(summary, parse_mode="Markdown", reply_markup=get_confirm_kavralan_sale_kb())

@router.callback_query(F.data == "retry_kavralan_sale", KavralanSaleStates.confirming)
async def retry_kavralan_sale(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    rolls = await get_available_kavralan_rolls(branch_id=branch_id)
    await state.set_state(KavralanSaleStates.choosing_roll)
    await callback.message.edit_text(
        "Sotilayotgan Kavralan rulonini tanlang:",
        reply_markup=get_kavralan_rolls_selection_kb(rolls)
    )
    await callback.answer()

# 1. NAQD KAVRALAN SOTUV
@router.callback_query(F.data.in_(["confirm_kavralan_sale", "confirm_kavralan_sale_cash"]), KavralanSaleStates.confirming)
async def confirm_kavralan_sale(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    roll_id = data["roll_id"]
    sold_length = data["sold_length"]

    res = await make_kavralan_sale(
        roll_id=roll_id,
        sold_length=sold_length,
        branch_id=branch_id,
        is_debt=False
    )

    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass

    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    await callback.message.answer(
        f"✅ *Asl Kavralan sotuvi muvaffaqiyatli amalga oshirildi! ({b_name})*\n"
        f"💵 *To'lov turi:* Naqd to'lov\n\n"
        f"🆔 Rulon: *{res['roll_code']}*\n"
        f"✂️ Kesildi: *{KAVRALAN_WIDTH:g} x {res['sold_length']} m* ({res['sold_area']} m²)\n"
        f"💰 Sotuv summasi: *${res['sale_total_price']:.2f}*\n"
        f"📏 Rulondagi qoldiq: *{res['remaining_length']} m*\n\n"
        f"💵 *Kavralan kassasiga qo'shildi:* +${res['sale_total_price']:.2f}\n"
        f"💰 *Joriy Kavralan kassa balansi:* ${res['new_kavralan_cash_balance']:.2f}",
        parse_mode="Markdown",
        reply_markup=get_kavralan_submenu()
    )
    await callback.answer("Sotildi!")

# 2. NASIYA (QARZ) KAVRALAN SOTUV
@router.callback_query(F.data == "kavralan_debt_start", KavralanSaleStates.confirming)
async def start_kavralan_debt_flow(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    await state.set_state(KavralanSaleStates.entering_customer_name)
    await callback.message.edit_text(
        "📝 *Nasiya (Qarz) rasmiylashtirish:*\n\n"
        "Mijozning ismini kiriting (Masalan: Alisher aka yoki Rustam):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(KavralanSaleStates.entering_customer_name)
async def kavralan_debt_name(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    name = message.text.strip()
    if not name:
        await message.answer("Iltimos, mijoz ismini kiriting:")
        return
    await state.update_data(customer_name=name)
    await state.set_state(KavralanSaleStates.entering_customer_phone)
    await message.answer(
        f"Mijoz: *{name}*\n\n"
        "Telefon raqamini kiriting (Masalan: `+998901234567` yoki telefon bo'lmasa `/otkazish` deb yozing):",
        parse_mode="Markdown"
    )

@router.message(KavralanSaleStates.entering_customer_phone)
async def kavralan_debt_phone(message: Message, state: FSMContext):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    text = message.text.strip()
    phone = "" if text.lower() in ["/otkazish", "otkazish", "-", "yoq", "yo'q"] else text
    await state.update_data(customer_phone=phone)

    data = await state.get_data()
    total_val = data["total_val"]

    await state.set_state(KavralanSaleStates.entering_initial_paid)
    await message.answer(
        f"💰 Jami sotuv summasi: *${total_val:.2f}*\n\n"
        "Mijoz boshlang'ich qisman to'lov qildimi?\n"
        "To'langan summani kiriting (agar umuman to'lamagan bo'lsa `0` deb yozing):",
        parse_mode="Markdown"
    )

@router.message(KavralanSaleStates.entering_initial_paid)
async def kavralan_debt_initial(message: Message, state: FSMContext):
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
        await message.answer("Iltimos, faqat raqam kiriting (Masalan: `100` yoki `0`):")
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
    await state.set_state(KavralanSaleStates.confirming_debt)

    roll_code = data["roll_code"]
    sold_length = data["sold_length"]
    sold_area = data["sold_area"]
    customer_name = data["customer_name"]
    customer_phone = data["customer_phone"]
    phone_display = customer_phone if customer_phone else "Kiritilmagan"

    summary = (
        f"📋 *Nasiya (Qarz) Kavralan sotuvini tasdiqlang:*\n\n"
        f"👤 Mijoz: *{customer_name}*\n"
        f"📞 Telefon: `{phone_display}`\n"
        f"🆔 Rulon: *{roll_code}*\n"
        f"✂️ Kesilmoqda: *{KAVRALAN_WIDTH:g} x {sold_length} m* ({sold_area} m²)\n"
        f"💰 Jami summa: *${total_val:.2f}*\n"
        f"💵 Boshlang'ich to'lov (kassaga tushadi): *${initial_paid:.2f}*\n"
        f"⏳ Qolgan qarz (Nasiya): *${remaining_debt:.2f}*\n\n"
        f"Nasiyani tasdiqlaysizmi?"
    )
    await message.answer(summary, parse_mode="Markdown", reply_markup=get_confirm_debt_sale_kb("kavralan"))

@router.callback_query(F.data == "retry_kavralan_debt", KavralanSaleStates.confirming_debt)
async def retry_kavralan_debt(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    await state.set_state(KavralanSaleStates.entering_customer_name)
    await callback.message.edit_text(
        "Mijozning ismini qaytadan kiriting:",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_kavralan_debt_final", KavralanSaleStates.confirming_debt)
async def confirm_kavralan_debt_final(callback: CallbackQuery, state: FSMContext):
    role, branch_id = get_user_role(callback.from_user.id)
    if role != "branch":
        return
    data = await state.get_data()
    roll_id = data["roll_id"]
    sold_length = data["sold_length"]
    customer_name = data["customer_name"]
    customer_phone = data["customer_phone"]
    initial_paid = data["initial_paid"]

    res = await make_kavralan_sale(
        roll_id=roll_id,
        sold_length=sold_length,
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
    phone_display = customer_phone if customer_phone else "Kiritilmagan"
    await callback.message.answer(
        f"✅ *Asl Kavralan nasiyaga (qarzga) sotildi! ({b_name})*\n\n"
        f"🆔 Nasiya ID: *#D-{res['debt_id']}*\n"
        f"👤 Mijoz: *{customer_name}* ({phone_display})\n"
        f"🆔 Rulon: *{res['roll_code']}*\n"
        f"✂️ Kesildi: *{KAVRALAN_WIDTH:g} x {res['sold_length']} m* ({res['sold_area']} m²)\n"
        f"💰 Jami sotuv: *${res['sale_total_price']:.2f}*\n"
        f"💵 Boshlang'ich to'lov: *${res['initial_paid']:.2f}*\n"
        f"⏳ Qolgan qarz: *${res['remaining_debt']:.2f}*\n"
        f"📏 Rulondagi qoldiq: *{res['remaining_length']} m*\n\n"
        f"💵 *Kavralan kassasiga qo'shildi:* +${res['initial_paid']:.2f}\n"
        f"💰 *Joriy Kavralan kassa balansi:* ${res['new_kavralan_cash_balance']:.2f}",
        parse_mode="Markdown",
        reply_markup=get_kavralan_submenu()
    )
    await callback.answer("Nasiyaga sotildi!")

# --- KAVRALAN OMBOR QOLDIG'I ---

@router.message(F.text == "📦 Kavralan Ombori")
async def show_kavralan_inventory(message: Message):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    rolls = await get_available_kavralan_rolls(branch_id=branch_id)
    b_name = BRANCH_NAMES.get(branch_id, "Filial")

    if not rolls:
        await message.answer(f"📦 {b_name} omborida Asl Kavralan rulonlari mavjud emas!")
        return

    lines = [f"🧶 *{b_name} — ASL KAVRALAN OMBOR QOLDIG'I:*\n"]
    total_m2 = 0.0
    total_val = 0.0

    for idx, r in enumerate(rolls, start=1):
        total_m2 += r["area_m2"]
        total_val += r["total_price"]
        lines.append(f"{idx}. *{r['roll_code']}*: {r['width']:g}x{r['current_length']}m (`{r['area_m2']} m²`) — ${r['total_price']:.2f}")

    lines.append(f"\n🔢 *Jami rulonlar soni:* `{len(rolls)} ta`")
    lines.append(f"📐 *Jami maydon:* `{round(total_m2, 2)} m²`")
    lines.append(f"💰 *Jami tovar qiymati ($30 dan):* `${round(total_val, 2):.2f}`")

    await message.answer("\n".join(lines), parse_mode="Markdown")
