import os
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from config import ADMIN_IDS
from database.local_db import get_dashboard_stats, get_all_active_rolls
from utils.excel_export import generate_excel_report

router = Router()
logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(F.text == "📊 Dashboard")
async def show_dashboard(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = await get_dashboard_stats()
    
    text = (
        "📊 *OMBOR VA BIZNES DASHBOARDI*\n\n"
        "📦 *Ombordagi tovar holati:*\n"
        f"• Faol rulonlar: *{stats['stock_rolls_count']} ta*\n"
        f"• Jami hajm: *{stats['stock_total_m2']} m²*\n"
        f"• Tovar qiymati ($8/m²): *${stats['stock_total_value']:.2f}*\n\n"
        "💵 *Kassa holati:*\n"
        f"• Kassadagi naqd pul: *${stats['cash_balance']:.2f}*\n\n"
        "📈 *Bugungi savdo:*\n"
        f"• Sotuvlar soni: *{stats['today_sales_count']} ta*\n"
        f"• Sotilgan maydon: *{stats['today_sold_m2']} m²*\n"
        f"• Bugungi tushum: *${stats['today_revenue']:.2f}*\n\n"
        "🏆 *Umumiy statistika:*\n"
        f"• Jami sotuvlar soni: *{stats['all_sales_count']} ta*\n"
        f"• Jami sotilgan hajm: *{stats['all_sold_m2']} m²*\n"
        f"• Jami umumiy tushum: *${stats['all_revenue']:.2f}*"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "📦 Ombor qoldig'i")
async def show_inventory(message: Message):
    if not is_admin(message.from_user.id):
        return
    rolls = await get_all_active_rolls()
    if not rolls:
        await message.answer("Omborda mahsulot mavjud emas!")
        return

    lines = [f"📦 *OMBORDAGI MAVJUD RULONLAR ({len(rolls)} ta):*\n"]
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
    if not is_admin(message.from_user.id):
        return
    wait_msg = await message.answer("⏳ Excel hisobot tayyorlanmoqda, iltimos kuting...")
    try:
        report_path = "CRM_Hisobot.xlsx"
        await generate_excel_report(report_path)
        doc = FSInputFile(report_path, filename=f"CRM_Hisobot_{datetime.now().strftime('%Y-%m-%d')}.xlsx")
        await message.answer_document(
            document=doc,
            caption="📊 *Rezinka gilam CRM hisoboti*\n\nUshbu faylda:\n1. Ombor qoldig'i\n2. Sotuvlar tarixi\n3. Kassa amallari\njamlangan.",
            parse_mode="Markdown"
        )
        await wait_msg.delete()
    except Exception as e:
        logger.error(f"Excel yaratishda xatolik: {e}")
        await wait_msg.edit_text(f"❌ Xatolik yuz berdi: {e}")
