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
from handlers import common, import_goods, sales, cashbox, dashboard
from utils.excel_export import generate_excel_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def start_dummy_web_server():
    port = int(os.getenv("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="DRAP BOT is running!"))
    app.router.add_get("/health", lambda r: web.Response(text="OK"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Healthcheck web server {port}-portda ishga tushdi.")

async def send_weekly_backup(bot: Bot):
    logger.info("Haftalik backup faqat Bosh Adminga yuborilmoqda...")
    now_str = datetime.now().strftime("%Y-%m-%d")
    for admin_id in SUPER_ADMIN_IDS:
        try:
            # 1. Umumiy Excel hisobot
            excel_file = f"CRM_Umumiy_{now_str}.xlsx"
            await generate_excel_report(excel_file, branch_id=None)
            await bot.send_document(
                chat_id=admin_id,
                document=FSInputFile(excel_file),
                caption=f"🔔 *Haftalik Umumiy Birlashgan Excel hisobot* ({now_str})\nBarcha filiallarning ombor qoldig'i, sotuvlar va kassalari to'liq jamlangan.",
                parse_mode="Markdown"
            )
            
            # 2. SQLite baza nusxasi (data.db)
            if os.path.exists(DB_PATH):
                await bot.send_document(
                    chat_id=admin_id,
                    document=FSInputFile(DB_PATH, filename=f"backup_data_{now_str}.db"),
                    caption=f"🛡 *Haftalik xavfsiz zaxira nusxa (data.db)*\nSana: {now_str}\n\nBarcha filiallarning ma'lumotlar bazasi zaxira nusxasi.",
                    parse_mode="Markdown"
                )
            logger.info(f"Super Admin {admin_id} ga backup yuborildi.")
        except Exception as e:
            logger.error(f"Backup yuborishda xatolik ({admin_id}): {e}")

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN ko'rsatilmagan! .env faylini tekshiring.")
        return

    # 1. Bazani initsializatsiya qilish
    await init_db()
    logger.info("SQLite bazasi tayyor!")

    # 2. Bot va Dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # 3. Routerlarni ro'yxatdan o'tkazish
    dp.include_router(common.router)
    dp.include_router(import_goods.router)
    dp.include_router(sales.router)
    dp.include_router(cashbox.router)
    dp.include_router(dashboard.router)

    # 4. Haftalik zaxira vazifasi (Har yakshanba 23:59 da faqat Super Adminga)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_weekly_backup,
        trigger="cron",
        day_of_week="sun",
        hour=23,
        minute=59,
        args=[bot]
    )
    scheduler.start()
    logger.info("Haftalik backup scheduler (Yakshanba 23:59) faqat Super Adminga ulandi!")

    # 5. Render bepul web service uchun healthcheck server
    await start_dummy_web_server()

    logger.info("Bot polling rejimida ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
