import os
import asyncio
import logging
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, SUPER_ADMIN_IDS
from database.local_db import init_db, DB_PATH
from handlers import common
from utils.excel_export import generate_excel_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from web.server import start_web_server

async def send_weekly_backup(bot: Bot):
    logger.info("Haftalik backup faqat Bosh Adminga yuborilmoqda...")
    now_str = datetime.now().strftime("%Y-%m-%d")
    for admin_id in SUPER_ADMIN_IDS:
        try:
            excel_file = f"CRM_Umumiy_{now_str}.xlsx"
            await generate_excel_report(excel_file, branch_id=None)
            await bot.send_document(
                chat_id=admin_id,
                document=FSInputFile(excel_file),
                caption=f"🔔 *Haftalik Umumiy Birlashgan Excel hisobot* ({now_str})\nGilam va Teri ombori, sotuvlar va alohida kassalar to'liq jamlangan.",
                parse_mode="Markdown"
            )
            if os.path.exists(DB_PATH):
                await bot.send_document(
                    chat_id=admin_id,
                    document=FSInputFile(DB_PATH, filename=f"backup_data_{now_str}.db"),
                    caption=f"🛡 *Haftalik xavfsiz zaxira nusxa (data.db)*\nSana: {now_str}\n\nBarcha filiallarning to'liq ma'lumotlar bazasi.",
                    parse_mode="Markdown"
                )
            logger.info(f"Super Admin {admin_id} ga backup yuborildi.")
        except Exception as e:
            logger.error(f"Backup yuborishda xatolik ({admin_id}): {e}")

async def send_daily_debt_reminders(bot: Bot):
    logger.info("Kundalik qarz eslatmalari tekshirilmoqda...")
    try:
        from database.local_db import get_due_debts_for_reminders
        from config import BRANCH_USERS, BRANCH_NAMES
        
        due_data = await get_due_debts_for_reminders()
        if not due_data:
            logger.info("Bugun to'lov muddati kelgan faol qarzlar yo'q.")
            return

        for branch_id, cat_data in due_data.items():
            today_list = cat_data.get("today", [])
            tomorrow_list = cat_data.get("tomorrow", [])
            overdue_list = cat_data.get("overdue", [])

            if not (today_list or tomorrow_list or overdue_list):
                continue

            branch_name = BRANCH_NAMES.get(branch_id, f"{branch_id}-Filial")
            lines = [
                f"🔔 *Nasiya (Qarz) to'lov muddati eslatmasi*",
                f"🏢 *Filial:* {branch_name}\n"
            ]

            if today_list:
                lines.append("⚠️ *Bugun to'lanishi kerak bo'lgan qarzlar:*")
                for d in today_list:
                    name = d.get("customer_name", "Mijoz")
                    phone = d.get("customer_phone") or "-"
                    amt = d.get("amount") or d.get("remaining_amount", 0)
                    m_info = f" ({d['month_number']}-oylik to'lov)" if "month_number" in d else ""
                    item_info = f" | {d.get('item_details', '')}" if d.get('item_details') else ""
                    lines.append(f"• *{name}* ({phone}): *${amt:.2f}*{m_info}{item_info}")
                lines.append("")

            if tomorrow_list:
                lines.append("⏳ *Ertaga muddati keladigan qarzlar:*")
                for d in tomorrow_list:
                    name = d.get("customer_name", "Mijoz")
                    phone = d.get("customer_phone") or "-"
                    amt = d.get("amount") or d.get("remaining_amount", 0)
                    m_info = f" ({d['month_number']}-oylik to'lov)" if "month_number" in d else ""
                    lines.append(f"• *{name}* ({phone}): *${amt:.2f}*{m_info}")
                lines.append("")

            if overdue_list:
                lines.append("🚨 *Muddati o'tgan qarzlar:*")
                for d in overdue_list[:5]:
                    name = d.get("customer_name", "Mijoz")
                    phone = d.get("customer_phone") or "-"
                    amt = d.get("amount") or d.get("remaining_amount", 0)
                    due = d.get("due_date", "-")
                    lines.append(f"• *{name}* ({phone}): *${amt:.2f}* (Muddat: {due})")
                if len(overdue_list) > 5:
                    lines.append(f"  _...va yana {len(overdue_list) - 5} ta qarz_")
                lines.append("")

            msg_text = "\n".join(lines)

            # Faqatgina qarz tegishli bo'lgan filial xodimlariga yuboriladi
            branch_recipients = [uid for uid, bid in BRANCH_USERS.items() if bid == branch_id]
            for uid in branch_recipients:
                try:
                    await bot.send_message(chat_id=uid, text=msg_text, parse_mode="Markdown")
                    logger.info(f"Qarz eslatmasi filial {branch_id} xodimi {uid} ga yuborildi.")
                except Exception as e:
                    logger.error(f"Xodimga ({uid}) eslatma yuborishda xatolik: {e}")

            # Kelajakda mijozning o'ziga ham telegram bot/sms ko'rinishida eslatma yuborish hook-i:
            # for d in today_list:
            #     if d.get("customer_telegram_id"):
            #         # await send_customer_reminder(bot, d["customer_telegram_id"], d)
            #         pass
    except Exception as e:
        logger.error(f"Kundalik qarz eslatmalarida xatolik: {e}")

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN ko'rsatilmagan! .env faylini tekshiring.")
        return

    # 1. Bazani initsializatsiya qilish
    await init_db()
    logger.info("SQLite bazasi tayyor (Gilam, Teri va alohida kassalar)!")

    # 2. Bot va Dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # 3. Routerlarni ro'yxatdan o'tkazish (Faqat avtorizatsiya va bildirishnomalar)
    dp.include_router(common.router)

    # 4. Haftalik zaxira (Har yakshanba 23:59 da faqat Super Adminga)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_weekly_backup,
        trigger="cron",
        day_of_week="sun",
        hour=23,
        minute=59,
        args=[bot]
    )
    # 5. Kundalik qarz eslatmalari (Har kuni 09:00 da filial xodimlariga)
    scheduler.add_job(
        send_daily_debt_reminders,
        trigger="cron",
        hour=9,
        minute=0,
        args=[bot]
    )
    scheduler.start()
    logger.info("Haftalik backup va kundalik qarz eslatmalari scheduler faol!")

    # 5. DRAP ERP Ghost-style Web Server (8080-port)
    await start_web_server(bot)

    logger.info("Bot polling rejimida ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
