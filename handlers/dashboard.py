import os
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from config import BRANCH_NAMES
from database.local_db import get_dashboard_stats, get_all_active_rolls
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
        f"📦 *Ombordagi tovaringiz:*\n"
        f"• Faol rulonlar: *{stats['stock_rolls_count']} ta*\n"
        f"• Jami hajm: *{stats['stock_total_m2']} m²*\n"
        f"• Tovar qiymati ($8/m²): *${stats['stock_total_value']:.2f}*\n\n"
        f"💵 *Kassa holatingiz:*\n"
        f"• Kassadagi naqd pul: *${stats['cash_balance']:.2f}*\n\n"
        f"📈 *Bugungi savdo:*\n"
        f"• Sotuvlar soni: *{stats['today_sales_count']} ta*\n"
        f"• Sotilgan maydon: *{stats['today_sold_m2']} m²*\n"
        f"• Bugungi tushum: *${stats['today_revenue']:.2f}*\n\n"
        f"🏆 *Umumiy statistika:*\n"
        f"• Jami sotuvlar: *{stats['all_sales_count']} ta*\n"
        f"• Jami sotilgan: *{stats['all_sold_m2']} m²*\n"
        f"• Jami umumiy tushum: *${stats['all_revenue']:.2f}*"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "📦 Ombor qoldig'i")
async def show_inventory(message: Message):
    role, branch_id = get_user_role(message.from_user.id)
    if role != "branch":
        return
    rolls = await get_all_active_rolls(branch_id=branch_id)
    b_name = BRANCH_NAMES.get(branch_id, "Filial")
    
    if not rolls:
        await message.answer(f"📦 {b_name} omborida mahsulot mavjud emas!")
        return

    lines = [f"📦 *{b_name} OMBOR QOLDIG'I ({len(rolls)} ta):*\n"]
    total_m2 = 0.0
    total_val = 0.0

    for idx, r in enumerate(rolls, start=1):
        total_m2 += r["area_m2"]
        total_val += r["total_price"]
        lines.append(
            f"{idx}. *{r['roll_code']}*: `{r['width']:g} x {r['current_length']} m` - *{r['color']}* "
            f"({r['area_m2']} m² | ${r['total_price']:.2f})"
        )

    lines.append(f"\n📐 *Jami hajm:* `{round(total_m2, 2)} m²`")
    lines.append(f"💰 *Jami qiymat:* `${round(total_val, 2):.2f}`")

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
            caption=f"📊 *{b_name} hisoboti*\n\n1. Ombor qoldig'i\n2. Sotuvlar tarixi\n3. Kassa amallari",
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
        f"📦 *Ombordagi tovar holati:*\n"
        f"• Faol rulonlar: *{stats['stock_rolls_count']} ta*\n"
        f"• Jami hajm: *{stats['stock_total_m2']} m²*\n"
        f"• Tovar qiymati ($8/m²): *${stats['stock_total_value']:.2f}*\n\n"
        f"💵 *Kassa holati:*\n"
        f"• Kassadagi naqd pul: *${stats['cash_balance']:.2f}*\n\n"
        f"📈 *Bugungi savdo:*\n"
        f"• Sotuvlar soni: *{stats['today_sales_count']} ta*\n"
        f"• Sotilgan maydon: *{stats['today_sold_m2']} m²*\n"
        f"• Bugungi tushum: *${stats['today_revenue']:.2f}*\n\n"
        f"🏆 *Umumiy statistika:*\n"
        f"• Jami sotuvlar: *{stats['all_sales_count']} ta*\n"
        f"• Jami sotilgan: *{stats['all_sold_m2']} m²*\n"
        f"• Jami umumiy tushum: *${stats['all_revenue']:.2f}*"
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
        f"📦 *Umumiy barcha omborlardagi tovar:*\n"
        f"• Jami faol rulonlar: *{stats['stock_rolls_count']} ta*\n"
        f"• Jami hajm: *{stats['stock_total_m2']} m²*\n"
        f"• Tovar umumiy qiymati ($8/m²): *${stats['stock_total_value']:.2f}*\n\n"
        f"💵 *Umumiy kassa (Barcha filiallar):*\n"
        f"• Jami naqd pul yig'indisi: *${stats['cash_balance']:.2f}*\n\n"
        f"📈 *Bugungi umumiy savdo:*\n"
        f"• Jami sotuvlar: *{stats['today_sales_count']} ta*\n"
        f"• Sotilgan maydon: *{stats['today_sold_m2']} m²*\n"
        f"• Bugungi umumiy tushum: *${stats['today_revenue']:.2f}*\n\n"
        f"🏆 *Umumiy statistika (Barcha davr):*\n"
        f"• Jami sotuvlar: *{stats['all_sales_count']} ta*\n"
        f"• Jami sotilgan hajm: *{stats['all_sold_m2']} m²*\n"
        f"• Jami umumiy tushum: *${stats['all_revenue']:.2f}*"
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
            caption=f"📊 *{b_name} hisoboti*\n\n1. Ombor qoldig'i\n2. Sotuvlar tarixi\n3. Kassa amallari",
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
            caption="🌐 *Barcha filiallar birlashgan Excel hisoboti*\n\nUshbu faylda 1-filial va 2-filialning barcha qoldiqlari, sotuvlari va kassa harakatlari alohida ustunda ko'rsatilgan.",
            parse_mode="Markdown"
        )
        await wait_msg.delete()
    except Exception as e:
        logger.error(f"Excel xatolik: {e}")
        await wait_msg.edit_text(f"❌ Xatolik: {e}")
