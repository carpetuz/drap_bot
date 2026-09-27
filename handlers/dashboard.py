import os
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from config import BRANCH_NAMES
from database.local_db import get_dashboard_stats, get_all_active_rolls, get_leather_stock, get_all_active_kavralan_rolls
from utils.excel_export import generate_excel_report
from handlers.common import get_user_role

router = Router()
logger = logging.getLogger(__name__)

# --- FILIAL XODIMI STATISTIKASI ---

@router.message(F.text == "📊 Dashboard")
async def show_dashboard(message: Message):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    stats = await get_dashboard_stats(branch_id=branch_id)
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    
    text = (
        f"📊 *{b_name} DASHBOARDI*\n\n"
        f"🌀 *REZINKA GILAM:*\n"
        f"• Ombordagi rulonlar: *{stats['carpet_rolls_count']} ta* ({stats['carpet_total_m2']} m²)\n"
        f"• Tovar qiymati ($8/m²): *${stats['carpet_total_val']:.2f}*\n"
        f"• Bugungi savdo: *{stats['today_carpet_count']} ta* ({stats['today_carpet_m2']} m² — ${stats['today_carpet_rev']:.2f})\n"
        f"• 💵 *Gilam kassasi qoldig'i:* *${stats['carpet_cash']:.2f}*\n\n"
        f"🐑 *TERI MAHSULOTI ($50/dona):*\n"
        f"• Ombordagi teri: *{stats['leather_total_qty']} dona*\n"
        f"• Tovar qiymati: *${stats['leather_total_val']:.2f}*\n"
        f"• Bugungi savdo: *{stats['today_leather_count']} ta* ({stats['today_leather_qty']} dona — ${stats['today_leather_rev']:.2f})\n"
        f"• 💵 *Teri kassasi qoldig'i:* *${stats['leather_cash']:.2f}*\n\n"
        f"🧶 *ASL KAVRALAN ($30/m²):*\n"
        f"• Ombordagi rulonlar: *{stats['kavralan_rolls_count']} ta* ({stats['kavralan_total_m2']} m²)\n"
        f"• Tovar qiymati: *${stats['kavralan_total_val']:.2f}*\n"
        f"• Bugungi savdo: *{stats['today_kavralan_count']} ta* ({stats['today_kavralan_m2']} m² — ${stats['today_kavralan_rev']:.2f})\n"
        f"• 💵 *Kavralan kassasi qoldig'i:* *${stats['kavralan_cash']:.2f}*\n\n"
        f"📒 *NASIYALAR (QARZLAR):*\n"
        f"• Faol qarzdorlar soni: *{stats['active_debts_count']} ta*\n"
        f"• ⏳ Kutilayotgan umumiy qarz: *${stats['total_debt_rem']:.2f}*\n"
        f"  (Gilam: ${stats['carpet_debt_rem']:.2f} | Teri: ${stats['leather_debt_rem']:.2f} | Kavralan: ${stats['kavralan_debt_rem']:.2f})"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text.in_(["📦 Ombor Qoldig'i", "📦 Umumiy Ombor"]))
async def show_inventory(message: Message):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    rolls = await get_all_active_rolls(branch_id=branch_id)
    leathers = await get_leather_stock(branch_id=branch_id)
    kavralans = await get_all_active_kavralan_rolls(branch_id=branch_id)
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    
    lines = [f"📦 *{b_name} — OMBOR QOLDIG'I:*\n"]
    
    # Gilamlar
    lines.append("🌀 *Rezinka Gilamlar:*")
    if not rolls:
        lines.append("• Gilam mavjud emas.")
    else:
        c_m2 = 0.0
        c_val = 0.0
        for idx, r in enumerate(rolls, start=1):
            c_m2 += r["area_m2"]
            c_val += r["total_price"]
            lines.append(f"{idx}. *{r['roll_code']}*: `{r['width']:g}x{r['current_length']}m` - {r['color']} ({r['area_m2']} m² | ${r['total_price']:.2f})")
        lines.append(f"Jami gilam: `{round(c_m2, 2)} m²` (${round(c_val, 2):.2f})\n")
        
    # Terilar
    lines.append("🐑 *Teri Mahsulotlari:*")
    if not leathers:
        lines.append("• Teri mavjud emas.")
    else:
        l_qty = 0
        l_val = 0.0
        for idx, s in enumerate(leathers, start=1):
            v = round(s["quantity"] * s["price_per_item"], 2)
            l_qty += s["quantity"]
            l_val += v
            lines.append(f"• *{s['color']}*: `{s['quantity']} dona` (${v:.2f})")
        lines.append(f"Jami teri: `{l_qty} dona` (${round(l_val, 2):.2f})\n")

    # Kavralan
    lines.append("🧶 *Asl Kavralan (4x):*")
    if not kavralans:
        lines.append("• Kavralan mavjud emas.")
    else:
        k_m2 = 0.0
        k_val = 0.0
        for idx, k in enumerate(kavralans, start=1):
            k_m2 += k["area_m2"]
            k_val += k["total_price"]
            lines.append(f"{idx}. *{k['roll_code']}*: `4x{k['current_length']}m` ({k['area_m2']} m² | ${k['total_price']:.2f})")
        lines.append(f"Jami kavralan: `{round(k_m2, 2)} m²` (${round(k_val, 2):.2f})")

    await message.answer("\n".join(lines), parse_mode="Markdown")

@router.message(F.text == "📦 Gilam Ombori")
async def show_carpet_inventory(message: Message):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    rolls = await get_all_active_rolls(branch_id=branch_id)
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    if not rolls:
        await message.answer(f"📦 {b_name} omborida gilam mavjud emas!")
        return
        
    lines = [f"🌀 *{b_name} — GILAM OMBOR QOLDIG'I ({len(rolls)} ta):*\n"]
    total_m2 = 0.0
    total_val = 0.0
    for idx, r in enumerate(rolls, start=1):
        total_m2 += r["area_m2"]
        total_val += r["total_price"]
        lines.append(f"{idx}. *{r['roll_code']}*: `{r['width']:g}x{r['current_length']}m` - *{r['color']}* ({r['area_m2']} m² | ${r['total_price']:.2f})")
    lines.append(f"\n📐 *Jami:* `{round(total_m2, 2)} m²` | 💰 `${round(total_val, 2):.2f}`")
    await message.answer("\n".join(lines), parse_mode="Markdown")

@router.message(F.text == "📑 Excel hisobot")
async def send_excel_report(message: Message):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    wait_msg = await message.answer("⏳ Excel hisobot tayyorlanmoqda...")
    try:
        report_path = f"CRM_{b_name}.xlsx"
        await generate_excel_report(report_path, branch_id=branch_id)
        doc = FSInputFile(report_path, filename=f"Hisobot_{b_name}_{datetime.now().strftime('%Y-%m-%d')}.xlsx")
        await message.answer_document(
            document=doc,
            caption=f"📊 *{b_name} to'liq hisoboti*\n\n1. Gilam Ombori\n2. Teri Ombori\n3. Gilam Sotuvlari\n4. Teri Sotuvlari\n5. Gilam Kassasi\n6. Teri Kassasi",
            parse_mode="Markdown"
        )
        await wait_msg.delete()
    except Exception as e:
        logger.error(f"Excel xatolik: {e}")
        await wait_msg.edit_text(f"❌ Xatolik: {e}")

# --- SUPER ADMIN STATISTIKASI ---

@router.message(F.text.in_(["🏢 1-Filial hisoboti", "🏢 2-Filial hisoboti"]))
async def superadmin_branch_stats(message: Message):
    role, _ = get_user_role(message.from_user.id)
    if role != "superadmin":
        return
    branch_id = 1 if "1-Filial" in message.text else 2
    b_name = BRANCH_NAMES.get(branch_id, f"Filial-{branch_id}")
    stats = await get_dashboard_stats(branch_id=branch_id)
    
    text = (
        f"🏢 *{b_name} STATISTIKASI (Bosh Admin uchun)*\n\n"
        f"🌀 *REZINKA GILAM:*\n"
        f"• Ombordagi tovar: *{stats['carpet_rolls_count']} ta* ({stats['carpet_total_m2']} m²)\n"
        f"• Tovar qiymati: *${stats['carpet_total_val']:.2f}*\n"
        f"• Bugungi savdo: *{stats['today_carpet_count']} ta* (${stats['today_carpet_rev']:.2f})\n"
        f"• 💵 *Gilam kassasi:* *${stats['carpet_cash']:.2f}*\n\n"
        f"🐑 *TERI MAHSULOTI:*\n"
        f"• Ombordagi tovar: *{stats['leather_total_qty']} dona*\n"
        f"• Tovar qiymati: *${stats['leather_total_val']:.2f}*\n"
        f"• Bugungi savdo: *{stats['today_leather_count']} ta* (${stats['today_leather_rev']:.2f})\n"
        f"• 💵 *Teri kassasi:* *${stats['leather_cash']:.2f}*\n\n"
        f"🧶 *ASL KAVRALAN:*\n"
        f"• Ombordagi tovar: *{stats['kavralan_rolls_count']} ta* ({stats['kavralan_total_m2']} m²)\n"
        f"• Tovar qiymati: *${stats['kavralan_total_val']:.2f}*\n"
        f"• Bugungi savdo: *{stats['today_kavralan_count']} ta* (${stats['today_kavralan_rev']:.2f})\n"
        f"• 💵 *Kavralan kassasi:* *${stats['kavralan_cash']:.2f}*\n\n"
        f"📒 *NASIYALAR (QARZLAR):*\n"
        f"• Faol qarzdorlar soni: *{stats['active_debts_count']} ta*\n"
        f"• ⏳ Kutilayotgan umumiy qarz: *${stats['total_debt_rem']:.2f}*\n"
        f"  (Gilam: ${stats['carpet_debt_rem']:.2f} | Teri: ${stats['leather_debt_rem']:.2f} | Kavralan: ${stats['kavralan_debt_rem']:.2f})"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "🌐 Barcha filiallar statistikasi")
async def superadmin_global_stats(message: Message):
    role, _ = get_user_role(message.from_user.id)
    if role != "superadmin":
        return
    stats = await get_dashboard_stats(branch_id=None)
    
    text = (
        "🌐 *BARCHA FILIALLARNING UMUMIY STATISTIKASI*\n\n"
        f"🌀 *REZINKA GILAMLAR (Jami):*\n"
        f"• Ombordagi rulonlar: *{stats['carpet_rolls_count']} ta* ({stats['carpet_total_m2']} m²)\n"
        f"• Tovar qiymati: *${stats['carpet_total_val']:.2f}*\n"
        f"• Bugungi savdo: *${stats['today_carpet_rev']:.2f}*\n"
        f"• 💵 *Jami Gilam kassalari:* *${stats['carpet_cash']:.2f}*\n\n"
        f"🐑 *TERI MAHSULOTLARI (Jami):*\n"
        f"• Ombordagi teri: *{stats['leather_total_qty']} dona*\n"
        f"• Tovar qiymati: *${stats['leather_total_val']:.2f}*\n"
        f"• Bugungi savdo: *${stats['today_leather_rev']:.2f}*\n"
        f"• 💵 *Jami Teri kassalari:* *${stats['leather_cash']:.2f}*\n\n"
        f"🧶 *ASL KAVRALAN (Jami):*\n"
        f"• Ombordagi rulonlar: *{stats['kavralan_rolls_count']} ta* ({stats['kavralan_total_m2']} m²)\n"
        f"• Tovar qiymati: *${stats['kavralan_total_val']:.2f}*\n"
        f"• Bugungi savdo: *${stats['today_kavralan_rev']:.2f}*\n"
        f"• 💵 *Jami Kavralan kassalari:* *${stats['kavralan_cash']:.2f}*\n\n"
        f"📒 *NASIYALAR (QARZLAR) — JAMI:*\n"
        f"• Barcha faol qarzdorlar: *{stats['active_debts_count']} ta*\n"
        f"• ⏳ Kutilayotgan umumiy qarz: *${stats['total_debt_rem']:.2f}*\n"
        f"  (Gilam: ${stats['carpet_debt_rem']:.2f} | Teri: ${stats['leather_debt_rem']:.2f} | Kavralan: ${stats['kavralan_debt_rem']:.2f})"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text.in_(["📑 1-Filial Excel", "📑 2-Filial Excel"]))
async def superadmin_branch_excel(message: Message):
    role, _ = get_user_role(message.from_user.id)
    if role != "superadmin":
        return
    branch_id = 1 if "1-Filial" in message.text else 2
    b_name = BRANCH_NAMES.get(branch_id, f"Filial-{branch_id}")
    wait_msg = await message.answer(f"⏳ {b_name} Excel hisoboti tayyorlanmoqda...")
    try:
        report_path = f"CRM_{b_name}.xlsx"
        await generate_excel_report(report_path, branch_id=branch_id)
        doc = FSInputFile(report_path, filename=f"Hisobot_{b_name}_{datetime.now().strftime('%Y-%m-%d')}.xlsx")
        await message.answer_document(
            document=doc,
            caption=f"📊 *{b_name} hisoboti*\n\n1. Gilam Ombori\n2. Teri Ombori\n3. Kavralan Ombori\n4. Sotuvlar (Gilam, Teri, Kavralan)\n5. Kassalar (Gilam, Teri, Kavralan)\n6. Nasiyalar (Qarzlar)",
            parse_mode="Markdown"
        )
        await wait_msg.delete()
    except Exception as e:
        logger.error(f"Excel xatolik: {e}")
        await wait_msg.edit_text(f"❌ Xatolik: {e}")

@router.message(F.text == "📊 Umumiy Birlashgan Excel")
async def superadmin_global_excel(message: Message):
    role, _ = get_user_role(message.from_user.id)
    if role != "superadmin":
        return
    wait_msg = await message.answer("⏳ Barcha filiallar umumiy Excel hisoboti tayyorlanmoqda...")
    try:
        report_path = "CRM_Barcha_Filiallar.xlsx"
        await generate_excel_report(report_path, branch_id=None)
        doc = FSInputFile(report_path, filename=f"CRM_Umumiy_{datetime.now().strftime('%Y-%m-%d')}.xlsx")
        await message.answer_document(
            document=doc,
            caption="🌐 *Barcha filiallar birlashgan to'liq Excel hisoboti*\n\nUshbu faylda Gilam, Teri va Asl Kavralan omborlari, barcha sotuvlar, har bir toifaning alohida kassa harakatlari hamda to'liq Nasiyalar daftari jamlangan.",
            parse_mode="Markdown"
        )
        await wait_msg.delete()
    except Exception as e:
        logger.error(f"Excel xatolik: {e}")
        await wait_msg.edit_text(f"❌ Xatolik: {e}")
