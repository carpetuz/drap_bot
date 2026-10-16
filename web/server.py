import os
import logging
from aiohttp import web
from aiogram import Bot
from web.routes import (
    api_auth_webapp, api_auth_qr_create, api_auth_qr_check, api_auth_me, api_switch_branch,
    api_branch3_stats, api_branch3_sales,
    api_get_stock, api_add_roll, api_make_sale,
    api_get_cashbox, api_withdraw_cash,
    api_get_debts, api_pay_debt,
    api_transfer_roll, api_get_expenses, api_add_expense
)

logger = logging.getLogger(__name__)

async def serve_index(request: web.Request):
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return web.FileResponse(index_path)

def setup_web_app(bot: Bot = None) -> web.Application:
    app = web.Application()
    if bot:
        app["bot"] = bot
        app["bot_username"] = "drapgilambot"

    # Static HTML
    app.router.add_get("/", serve_index)
    app.router.add_get("/login", serve_index)
    app.router.add_get("/health", lambda r: web.Response(text="OK"))

    # Auth routes
    app.router.add_post("/api/auth/webapp", api_auth_webapp)
    app.router.add_post("/api/auth/qr/create", api_auth_qr_create)
    app.router.add_get("/api/auth/qr/check", api_auth_qr_check)
    app.router.add_get("/api/auth/me", api_auth_me)
    app.router.add_post("/api/switch-branch", api_switch_branch)

    # 3-Filial routes
    app.router.add_get("/api/branch3/stats", api_branch3_stats)
    app.router.add_get("/api/branch3/sales", api_branch3_sales)
    app.router.add_post("/api/branch3/sales", api_branch3_sales)

    # Inventory & Sales
    app.router.add_get("/api/stock", api_get_stock)
    app.router.add_post("/api/rolls", api_add_roll)
    app.router.add_post("/api/sales", api_make_sale)

    # Cashbox & Debts
    app.router.add_get("/api/cashbox", api_get_cashbox)
    app.router.add_post("/api/cashbox/withdraw", api_withdraw_cash)
    app.router.add_get("/api/debts", api_get_debts)
    app.router.add_post("/api/debts/pay", api_pay_debt)

    # Transfer & Expenses (Rasxod)
    app.router.add_post("/api/transfer", api_transfer_roll)
    app.router.add_get("/api/expenses", api_get_expenses)
    app.router.add_post("/api/expenses", api_add_expense)

    # Static files directory
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.router.add_static("/static/", static_dir)

    return app

async def start_web_server(bot: Bot = None):
    port = int(os.getenv("PORT", 8080))
    app = setup_web_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Ghost-style DRAP CRM Web Server {port}-portda ishga tushdi!")
    return runner
