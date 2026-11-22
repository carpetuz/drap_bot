import os
import logging
from aiohttp import web
from aiogram import Bot
from web.routes import (
    api_auth_webapp, api_auth_qr_create, api_auth_qr_check, api_auth_me, api_auth_logout, api_switch_branch, api_auth_otp_send, api_auth_otp_verify,
    api_branch3_stats, api_branch3_sales,
    api_get_stock, api_add_roll, api_make_sale,
    api_get_cashbox, api_withdraw_cash,
    api_get_debts, api_pay_debt, api_get_debt_details, api_setup_debt_installments, api_cancel_debt_installments, api_edit_debt,
    api_transfer_roll, api_get_transfers, api_accept_transfer, api_reject_transfer, api_cancel_transfer,
    api_get_expenses, api_add_expense,
    api_edit_roll, api_delete_roll, api_edit_leather, api_edit_kavralan, api_delete_kavralan, api_delete_sale, api_edit_sale,
    api_get_profit_loss,
    api_get_kartal_cashbox, api_add_kartal_transaction, api_update_kartal_transaction,
    api_delete_kartal_transaction, api_get_kartal_lichniy,
    api_get_notes, api_save_note, api_delete_note, api_toggle_pin_note
)

logger = logging.getLogger(__name__)

async def serve_index(request: web.Request):
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    resp = web.FileResponse(index_path)
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

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
    app.router.add_post("/api/auth/otp/send", api_auth_otp_send)
    app.router.add_post("/api/auth/otp/verify", api_auth_otp_verify)
    app.router.add_get("/api/auth/me", api_auth_me)
    app.router.add_post("/api/auth/logout", api_auth_logout)
    app.router.add_post("/api/switch-branch", api_switch_branch)

    # 3-Filial routes
    app.router.add_get("/api/branch3/stats", api_branch3_stats)
    app.router.add_get("/api/branch3/sales", api_branch3_sales)
    app.router.add_post("/api/branch3/sales", api_branch3_sales)

    # Inventory & Sales
    app.router.add_get("/api/stock", api_get_stock)
    app.router.add_post("/api/rolls", api_add_roll)
    app.router.add_post("/api/sales", api_make_sale)
    app.router.add_post("/api/sales/delete", api_delete_sale)
    app.router.add_post("/api/sales/edit", api_edit_sale)

    # Cashbox & Debts
    app.router.add_get("/api/cashbox", api_get_cashbox)
    app.router.add_post("/api/cashbox/withdraw", api_withdraw_cash)
    app.router.add_get("/api/debts", api_get_debts)
    app.router.add_get("/api/debts/{id}", api_get_debt_details)
    app.router.add_get("/api/debts/{id}/details", api_get_debt_details)
    app.router.add_post("/api/debts/{id}/installments", api_setup_debt_installments)
    app.router.add_post("/api/debts/{id}/cancel-installments", api_cancel_debt_installments)
    app.router.add_post("/api/debts/pay", api_pay_debt)
    app.router.add_post("/api/debts/edit", api_edit_debt)
    app.router.add_post("/api/debts/{id}/edit", api_edit_debt)

    # Transfer & Expenses (Rasxod)
    app.router.add_post("/api/transfer", api_transfer_roll)
    app.router.add_get("/api/transfers", api_get_transfers)
    app.router.add_post("/api/transfer/accept", api_accept_transfer)
    app.router.add_post("/api/transfer/reject", api_reject_transfer)
    app.router.add_post("/api/transfer/cancel", api_cancel_transfer)
    app.router.add_get("/api/expenses", api_get_expenses)
    app.router.add_post("/api/expenses", api_add_expense)

    # Super Admin Stock Management
    app.router.add_post("/api/stock/edit-roll", api_edit_roll)
    app.router.add_post("/api/stock/delete-roll", api_delete_roll)
    app.router.add_post("/api/stock/edit-leather", api_edit_leather)
    app.router.add_post("/api/stock/edit-kavralan", api_edit_kavralan)
    app.router.add_post("/api/stock/delete-kavralan", api_delete_kavralan)

    # Reports (Hisobot: Foyda va Zarar)
    app.router.add_get("/api/reports/profit-loss", api_get_profit_loss)

    # Kartal Kassa & Hisoboti (Alohida baza)
    app.router.add_get("/api/kartal/cashbox", api_get_kartal_cashbox)
    app.router.add_post("/api/kartal/cashbox", api_add_kartal_transaction)
    app.router.add_put("/api/kartal/cashbox/{id}", api_update_kartal_transaction)
    app.router.add_delete("/api/kartal/cashbox/{id}", api_delete_kartal_transaction)
    app.router.add_get("/api/kartal/lichniy", api_get_kartal_lichniy)

    # Notes (Bloknot / Eslatmalar - iPhone Notes uslubida)
    app.router.add_get("/api/notes", api_get_notes)
    app.router.add_post("/api/notes", api_save_note)
    app.router.add_delete("/api/notes/{id}", api_delete_note)
    app.router.add_post("/api/notes/{id}/pin", api_toggle_pin_note)

    # Static files directory
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.router.add_static("/static/", static_dir)

    return app

async def start_web_server(bot: Bot = None):
    port = int(os.getenv("PORT", 8080))
    app = setup_web_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    logger.info(f"Ghost-style DRAP ERP Web Server {port}-portda ishga tushdi!")
    return runner
