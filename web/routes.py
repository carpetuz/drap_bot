import json
import logging
from datetime import datetime
from aiohttp import web
from config import (
    BRANCH_NAMES, BRANCH_USERS, SUPER_ADMIN_IDS,
    BRANCH3_COLLECTIONS, BRANCH3_WIDTH, 
    AVAILABLE_WIDTHS, AVAILABLE_COLORS, LEATHER_COLORS, KAVRALAN_WIDTH
)
from database import local_db
from web.auth import (
    verify_telegram_webapp_data, create_session, get_session, delete_session,
    create_qr_request, QR_REQUESTS,
    resolve_user_id, create_otp_request, verify_otp_code, get_short_id_for_user, get_user_role_and_branch
)

logger = logging.getLogger(__name__)

def json_response(data, status=200):
    return web.json_response(data, status=status, dumps=json.dumps)

def get_current_user(request: web.Request):
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = request.cookies.get("crm_session")
        
    if not token:
        return None
    return get_session(token)

def auth_required(handler):
    async def middleware(request: web.Request):
        user = get_current_user(request)
        if not user:
            return json_response({"error": "Avtorizatsiyadan o'tilmagan"}, status=401)
        request["user"] = user
        return await handler(request)
    return middleware

# --- AUTH ENDPOINTS ---

async def api_auth_webapp(request: web.Request):
    """Telegram WebApp initData orqali kirish"""
    try:
        body = await request.json()
        init_data = body.get("initData", "")
        if not init_data:
            return json_response({"error": "initData talab qilinadi"}, status=400)
            
        user_info = verify_telegram_webapp_data(init_data)
        if not user_info:
            return json_response({"error": "Telegram ma'lumotlari haqiqiy emas yoki muddati o'tgan"}, status=403)
            
        user_id = user_info.get("id")
        session = create_session(user_id, user_info)
        if not session:
            return json_response({"error": "Sizga ushbu tizimdan foydalanishga ruxsat berilmagan (ID ro'yxatda yo'q)"}, status=403)
            
        resp = json_response({
            "success": True,
            "token": session["token"],
            "user": session,
            "branch_names": BRANCH_NAMES
        })
        resp.set_cookie("crm_session", session["token"], max_age=86400*30, path="/", httponly=False, samesite="Lax")
        return resp
    except Exception as e:
        logger.error(f"api_auth_webapp xatolik: {e}")
        return json_response({"error": str(e)}, status=500)

async def api_auth_qr_create(request: web.Request):
    """Kompyuter uchun QR token yaratish"""
    bot_info = request.app.get("bot_username", "drapgilambot")
    qr_data = create_qr_request()
    qr_token = qr_data["qr_token"]
    login_url = f"https://t.me/{bot_info}?start=login_{qr_token}"
    return json_response({
        "qr_token": qr_token,
        "login_url": login_url
    })

async def api_auth_qr_check(request: web.Request):
    """QR orqali kirish holatini tekshirish"""
    token = request.query.get("token")
    if not token or token not in QR_REQUESTS:
        return json_response({"status": "not_found"}, status=404)
        
    req = QR_REQUESTS[token]
    if req["status"] == "approved":
        session = get_session(req["session_token"])
        resp = json_response({
            "status": "approved",
            "token": req["session_token"],
            "user": session,
            "branch_names": BRANCH_NAMES
        })
        resp.set_cookie("crm_session", req["session_token"], max_age=86400*30, path="/", httponly=False, samesite="Lax")
        return resp
    elif req["status"] == "rejected":
        return json_response({
            "status": "rejected",
            "error": "❌ Ruxsat berilmagan Telegram hisob! Ushbu hisob xodimlar ro'yxatida yo'q."
        }, status=403)
    return json_response({"status": req["status"]})

async def api_auth_otp_send(request: web.Request):
    """Foydalanuvchi ID raqami bo'yicha Telegram botga 6 xonali OTP yuborish"""
    try:
        body = await request.json()
        id_input = str(body.get("id", "")).strip()
        if not id_input:
            return json_response({"error": "ID raqamingizni kiriting"}, status=400)

        user_id = resolve_user_id(id_input)
        if not user_id:
            return json_response({"error": "Bunday ID tizimda mavjud emas yoki ruxsat berilmagan"}, status=403)

        role, branch_id = get_user_role_and_branch(user_id)
        if not role:
            return json_response({"error": "Ushbu foydalanuvchiga tizimdan foydalanishga ruxsat berilmagan"}, status=403)

        code, err, old_msg_id = create_otp_request(user_id)
        if err:
            return json_response({"error": err}, status=429)

        bot = request.app.get("bot")
        if not bot:
            return json_response({"error": "Telegram bot servisi ulanmagan"}, status=500)

        # Oldingi ishlatilmagan OTP xabari bo'lsa, chat toza turishi uchun uni o'chirib yuboramiz
        if old_msg_id:
            try:
                await bot.delete_message(chat_id=user_id, message_id=old_msg_id)
            except Exception:
                pass

        branch_label = "Bosh Admin" if role == "superadmin" else f"{BRANCH_NAMES.get(branch_id, 'Filial')}"
        msg_text = (
            f"🔐 <b>DRAP ERP — Kirish kodi (OTP)</b>\n\n"
            f"Hurmatli xodim ({branch_label}), sizning bir martalik kirish kodingiz:\n\n"
            f"👉 <code>{code}</code>\n\n"
            f"⏱ Amal qilish muddati: <b>2 daqiqa</b>.\n"
            f"⚠️ Ushbu kodni hech kimga bermang!"
        )

        try:
            sent_msg = await bot.send_message(chat_id=user_id, text=msg_text, parse_mode="HTML")
            set_otp_message_id(user_id, sent_msg.message_id)
        except Exception as e:
            logger.error(f"OTP yuborishda bot xatosi (user_id={user_id}): {e}")
            return json_response({
                "error": "Telegram bot orqali kod yuborib bo'lmadi. Avval Telegramda @drapgilambot ga kirib /start bosing."
            }, status=400)

        short_id = get_short_id_for_user(user_id)
        # Telegram ID mask, e.g. ***8653
        str_uid = str(user_id)
        masked_id = f"***{str_uid[-4:]}" if len(str_uid) >= 4 else str_uid
        return json_response({
            "success": True,
            "message": "Kod Telegram botingizga yuborildi",
            "masked_id": masked_id,
            "short_id": short_id,
            "branch_name": branch_label
        })
    except Exception as e:
        logger.error(f"api_auth_otp_send xatolik: {e}")
        return json_response({"error": str(e)}, status=500)

async def api_auth_otp_verify(request: web.Request):
    """OTP kodini tekshirib tizimga kiritish"""
    try:
        body = await request.json()
        id_input = str(body.get("id", "")).strip()
        code = str(body.get("code", "")).strip()

        if not id_input or not code:
            return json_response({"error": "ID va tasdiqlash kodi talab qilinadi"}, status=400)

        user_id = resolve_user_id(id_input)
        if not user_id:
            return json_response({"error": "Bunday ID tizimda mavjud emas"}, status=403)

        success, msg, otp_msg_id = verify_otp_code(user_id, code)
        if not success:
            return json_response({"error": msg}, status=400)

        # OTP muvaffaqiyatli tasdiqlandi -> Telegram chatdan OTP xabarini darhol o'chirib yuboramiz
        if otp_msg_id:
            try:
                bot = request.app.get("bot")
                if bot:
                    await bot.delete_message(chat_id=user_id, message_id=otp_msg_id)
            except Exception as del_err:
                logger.debug(f"OTP xabarini o'chirishda xatolik: {del_err}")

        session = create_session(user_id)
        if not session:
            return json_response({"error": "Sessiya yaratib bo'lmadi"}, status=403)

        resp = json_response({
            "success": True,
            "token": session["token"],
            "user": session,
            "branch_names": BRANCH_NAMES
        })
        resp.set_cookie("crm_session", session["token"], max_age=86400*30, path="/", httponly=False, samesite="Lax")
        return resp
    except Exception as e:
        logger.error(f"api_auth_otp_verify xatolik: {e}")
        return json_response({"error": str(e)}, status=500)

@auth_required
async def api_auth_me(request: web.Request):
    """Joriy foydalanuvchi ma'lumotlari"""
    user = request["user"]
    return json_response({
        "user": user,
        "branch_names": BRANCH_NAMES,
        "collections": BRANCH3_COLLECTIONS
    })

async def api_auth_logout(request: web.Request):
    """Foydalanuvchi tizimdan chiqishi"""
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = request.cookies.get("crm_session")
    if token:
        delete_session(token)
    resp = json_response({"success": True})
    resp.del_cookie("crm_session", path="/")
    return resp

@auth_required
async def api_switch_branch(request: web.Request):
    """Super Admin uchun filialni almashtirish"""
    user = request["user"]
    if user["role"] != "superadmin":
        return json_response({"error": "Faqat Bosh Admin filialni almashtira oladi"}, status=403)
        
    body = await request.json()
    new_branch = int(body.get("branch_id", 1))
    if new_branch not in BRANCH_NAMES:
        return json_response({"error": "Bunday filial mavjud emas"}, status=400)
        
    user["active_branch"] = new_branch
    return json_response({
        "success": True,
        "active_branch": new_branch,
        "branch_name": BRANCH_NAMES[new_branch]
    })

# --- 3-FILIAL APIS ---

@auth_required
async def api_branch3_stats(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    stats = await local_db.get_branch3_stats(branch_id=branch_id)
    return json_response(stats)

@auth_required
async def api_branch3_sales(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    
    if request.method == "GET":
        limit = int(request.query.get("limit", 50))
        history = await local_db.get_branch3_sales_history(branch_id=branch_id, limit=limit)
        return json_response({"sales": history})
        
    elif request.method == "POST":
        body = await request.json()
        collection = body.get("collection_name")
        try:
            length = float(str(body.get("length", 0)).replace(",", "."))
            price_raw = body.get("price_per_m2")
            custom_price = float(str(price_raw).replace(",", ".")) if price_raw not in (None, "") else None
        except (TypeError, ValueError):
            return json_response({"error": "Uzunlik yoki narx noto'g'ri kiritildi"}, status=400)

        if not collection or collection not in BRANCH3_COLLECTIONS:
            return json_response({"error": "Noto'g'ri kolleksiya tanlandi"}, status=400)
        if length <= 0:
            return json_response({"error": "Uzunlik 0 dan katta bo'lishi kerak"}, status=400)
        if custom_price is not None and custom_price <= 0:
            return json_response({"error": "Narx 0 dan katta bo'lishi kerak"}, status=400)

        try:
            res = await local_db.make_branch3_sale(
                collection_name=collection,
                length=length,
                branch_id=branch_id,
                custom_price_per_m2=custom_price
            )
        except Exception as e:
            logger.error(f"3-Filial sotuvida xatolik: {e}")
            return json_response({"error": str(e)}, status=400)
        return json_response({"success": True, "sale": res})

# --- GILAM VA OMBOR APIS ---

@auth_required
async def api_get_stock(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    is_rezinka_only = (branch_id == 2 or user.get("user_id") == 317633066)
    
    rolls = await local_db.get_all_active_rolls(branch_id=branch_id)
    kavralan = [] if is_rezinka_only else await local_db.get_all_active_kavralan_rolls(branch_id=branch_id)
    leather = [] if is_rezinka_only else await local_db.get_leather_stock(branch_id=branch_id)
    
    return json_response({
        "branch_id": branch_id,
        "branch_name": BRANCH_NAMES.get(branch_id, "Filial"),
        "rolls": rolls,
        "kavralan_rolls": kavralan,
        "leather": leather,
        "config": {
            "available_widths": AVAILABLE_WIDTHS,
            "available_colors": AVAILABLE_COLORS,
            "leather_colors": LEATHER_COLORS if not is_rezinka_only else [],
            "kavralan_width": KAVRALAN_WIDTH,
            "branch3_collections": BRANCH3_COLLECTIONS
        }
    })

@auth_required
async def api_add_roll(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    is_rezinka_only = (branch_id == 2 or user.get("user_id") == 317633066)
    
    body = await request.json()
    product_type = body.get("product_type", "carpet") # carpet, kavralan, leather
    
    if is_rezinka_only and product_type != "carpet":
        return json_response({"error": "Sizning hisobingizda faqat rezinka gilam qabul qilinadi"}, status=403)
    
    try:
        if product_type == "carpet":
            width = float(body.get("width", 0))
            color = str(body.get("color", "")).strip()
            length = float(body.get("length", 0))
            price_per_m2 = float(body.get("price_per_m2", 8.0))
            cost_price_per_m2 = float(body.get("cost_price_per_m2", price_per_m2))
            if width <= 0 or length <= 0 or price_per_m2 <= 0 or cost_price_per_m2 <= 0 or not color:
                return json_response({"error": "Noto'g'ri o'lcham yoki narx kiritildi"}, status=400)
            res = await local_db.add_roll(width, color, length, branch_id, price_per_m2, cost_price_per_m2)
            return json_response({"success": True, "item": res})
        elif product_type == "kavralan":
            length = float(body.get("length", 0))
            price_per_m2 = float(body.get("price_per_m2", 30.0))
            cost_price_per_m2 = float(body.get("cost_price_per_m2", price_per_m2))
            width = float(body.get("width", 4.0))
            model = str(body.get("model", "")).strip()
            color = str(body.get("color", "")).strip()
            if length <= 0 or price_per_m2 <= 0 or cost_price_per_m2 <= 0 or width <= 0:
                return json_response({"error": "Noto'g'ri o'lcham yoki narx kiritildi"}, status=400)
            res = await local_db.add_kavralan_roll(length, branch_id, price_per_m2, cost_price_per_m2=cost_price_per_m2, model=model, color=color, width=width)
            return json_response({"success": True, "item": res})
        elif product_type == "leather":
            color = str(body.get("color", "")).strip()
            quantity = int(body.get("quantity", 0))
            price_per_item = float(body.get("price_per_item", 50.0))
            if quantity <= 0 or price_per_item <= 0 or not color:
                return json_response({"error": "Noto'g'ri miqdor yoki narx kiritildi"}, status=400)
            res = await local_db.add_leather(color, quantity, branch_id, price_per_item)
            return json_response({"success": True, "item": res})
        else:
            return json_response({"error": "Noma'lum mahsulot turi"}, status=400)
    except Exception as e:
        logger.error(f"Kirimda xatolik: {e}")
        return json_response({"error": str(e)}, status=400)

@auth_required
async def api_make_sale(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    is_rezinka_only = (branch_id == 2 or user.get("user_id") == 317633066)
    
    body = await request.json()
    product_type = body.get("product_type", "carpet")
    
    if is_rezinka_only and product_type != "carpet":
        return json_response({"error": "Sizning hisobingizda faqat rezinka gilam sotiladi"}, status=403)
    
    is_debt = bool(body.get("is_debt", False))
    customer_name = str(body.get("customer_name", "")).strip()
    customer_phone = str(body.get("customer_phone", "")).strip()
    due_date = str(body.get("due_date", "")).strip() or None
    customer_telegram_id = body.get("customer_telegram_id")
    initial_paid = float(body.get("initial_paid", 0.0))
    if initial_paid < 0:
        return json_response({"error": "Boshlang'ich to'lov manfiy bo'lishi mumkin emas"}, status=400)
    
    raw_total = str(body.get("total_price") or "").replace(",", ".").strip()
    custom_total_price = float(raw_total) if raw_total and float(raw_total) > 0 else None
    
    items = body.get("items")
    try:
        if items and isinstance(items, list) and len(items) > 0:
            if is_rezinka_only:
                for it in items:
                    if it.get("product_type", "carpet") != "carpet":
                        return json_response({"error": "Sizning hisobingizda faqat rezinka gilam sotiladi"}, status=403)
            res = await local_db.make_batch_sale(
                items=items,
                branch_id=branch_id,
                is_debt=is_debt,
                customer_name=customer_name,
                customer_phone=customer_phone,
                initial_paid=initial_paid,
                due_date=due_date,
                customer_telegram_id=customer_telegram_id
            )
            return json_response({"success": True, "sale": res})

        if product_type == "carpet":
            roll_id = int(body.get("roll_id", 0))
            sold_length = float(str(body.get("sold_length", 0)).replace(",", "."))
            price_per_m2 = float(str(body.get("price_per_m2", 0)).replace(",", "."))
            if roll_id <= 0 or sold_length <= 0 or price_per_m2 <= 0:
                return json_response({"error": "Sotuv parametri noto'g'ri kiritildi"}, status=400)
            res = await local_db.make_sale(
                roll_id=roll_id,
                sold_length=sold_length,
                branch_id=branch_id,
                price_per_m2=price_per_m2,
                custom_total_price=custom_total_price,
                is_debt=is_debt,
                customer_name=customer_name,
                customer_phone=customer_phone,
                initial_paid=initial_paid,
                due_date=due_date,
                customer_telegram_id=customer_telegram_id
            )
            return json_response({"success": True, "sale": res})
        elif product_type == "kavralan":
            roll_id = int(body.get("roll_id", 0))
            sold_length = float(body.get("sold_length", 0))
            price_per_m2 = float(body.get("price_per_m2", 0))
            if roll_id <= 0 or sold_length <= 0 or price_per_m2 <= 0:
                return json_response({"error": "Sotuv parametri noto'g'ri kiritildi"}, status=400)
            res = await local_db.make_kavralan_sale(
                roll_id=roll_id,
                sold_length=sold_length,
                branch_id=branch_id,
                price_per_m2=price_per_m2,
                custom_total_price=custom_total_price,
                is_debt=is_debt,
                customer_name=customer_name,
                customer_phone=customer_phone,
                initial_paid=initial_paid,
                due_date=due_date,
                customer_telegram_id=customer_telegram_id
            )
            return json_response({"success": True, "sale": res})
        elif product_type == "leather":
            color = str(body.get("color", "")).strip()
            quantity = int(body.get("quantity", 0))
            price_per_item = float(body.get("price_per_item", 0))
            if not color or quantity <= 0 or price_per_item <= 0:
                return json_response({"error": "Sotuv parametri noto'g'ri kiritildi"}, status=400)
            res = await local_db.make_leather_sale(
                color=color,
                quantity=quantity,
                branch_id=branch_id,
                price_per_item=price_per_item,
                custom_total_price=custom_total_price,
                is_debt=is_debt,
                customer_name=customer_name,
                customer_phone=customer_phone,
                initial_paid=initial_paid,
                due_date=due_date,
                customer_telegram_id=customer_telegram_id
            )
            return json_response({"success": True, "sale": res})
        else:
            return json_response({"error": "Noma'lum tovar turi"}, status=400)
    except Exception as e:
        logger.error(f"Sotuvda xatolik: {e}")
        return json_response({"error": str(e)}, status=400)

@auth_required
async def api_get_profit_loss(request: web.Request):
    user = request["user"]
    if user["role"] == "superadmin":
        branch_param = request.query.get("branch_id")
        if branch_param and branch_param != "all":
            branch_id = int(branch_param)
        else:
            branch_id = None
    else:
        branch_id = user["branch_id"]
        
    period = request.query.get("period", "current_month")
    date_from = request.query.get("date_from")
    date_to = request.query.get("date_to")
    category = request.query.get("category", "all")
    
    try:
        report = await local_db.get_profit_loss_report(
            branch_id=branch_id,
            period=period,
            date_from=date_from,
            date_to=date_to,
            category=category
        )
        return json_response(report)
    except Exception as e:
        logger.error(f"Foyda-zarar hisobotida xatolik: {e}")
        return json_response({"error": str(e)}, status=400)

# --- KASSA VA NASIYA APIS ---

@auth_required
async def api_get_cashbox(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    
    bal_carpet = await local_db.get_cash_balance(branch_id=branch_id, category="carpet")
    bal_leather = await local_db.get_cash_balance(branch_id=branch_id, category="leather")
    bal_kavralan = await local_db.get_cash_balance(branch_id=branch_id, category="kavralan")
    bal_b3 = await local_db.get_cash_balance(branch_id=branch_id, category="branch3")
    
    total = round(bal_carpet + bal_leather + bal_kavralan + bal_b3, 2)
    return json_response({
        "branch_id": branch_id,
        "balances": {
            "carpet": bal_carpet,
            "leather": bal_leather,
            "kavralan": bal_kavralan,
            "branch3": bal_b3,
            "total": total
        }
    })

@auth_required
async def api_withdraw_cash(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    
    body = await request.json()
    amount = float(body.get("amount", 0))
    if amount <= 0:
        return json_response({"error": "Yechib olinadigan summa musbat bo'lishi kerak"}, status=400)
    category = body.get("category", "carpet")
    note = body.get("note", "Kassa topshirildi")
    
    try:
        res = await local_db.withdraw_cash(amount=amount, branch_id=branch_id, category=category, note=note)
        return json_response({"success": True, "result": res})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@auth_required
async def api_get_debts(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    debts = await local_db.get_active_debts(branch_id=branch_id)
    return json_response({"debts": debts})

@auth_required
async def api_pay_debt(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    
    body = await request.json()
    debt_id = int(body.get("debt_id", 0))
    amount = float(body.get("amount", 0))
    if debt_id <= 0 or amount <= 0:
        return json_response({"error": "To'lov summasi musbat bo'lishi kerak"}, status=400)
    note = body.get("note", "")
    payment_method = str(body.get("payment_method", "cash")).strip()
    installment_id = body.get("installment_id")
    if installment_id:
        try:
            installment_id = int(installment_id)
        except ValueError:
            installment_id = None
    
    try:
        res = await local_db.pay_debt(
            debt_id=debt_id, 
            payment_amount=amount, 
            branch_id=branch_id, 
            note=note,
            payment_method=payment_method,
            installment_id=installment_id
        )
        return json_response({"success": True, "result": res})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@auth_required
async def api_get_debt_details(request: web.Request):
    user = request["user"]
    debt_id_raw = request.match_info.get("id") or request.query.get("id", "0")
    try:
        debt_id = int(debt_id_raw)
    except ValueError:
        return json_response({"error": "Noto'g'ri qarz ID-si"}, status=400)
        
    if debt_id <= 0:
        return json_response({"error": "Noto'g'ri qarz ID-si"}, status=400)
    try:
        details = await local_db.get_debt_full_details(debt_id)
        if user["role"] != "superadmin":
            user_branch = user["branch_id"]
            if details["branch_id"] != user_branch:
                return json_response({"error": "Ushbu qarz boshqa filialga tegishli"}, status=403)
        return json_response({"success": True, "debt": details})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@auth_required
async def api_setup_debt_installments(request: web.Request):
    debt_id_raw = request.match_info.get("id") or request.query.get("id", "0")
    try:
        debt_id = int(debt_id_raw)
    except ValueError:
        return json_response({"error": "Noto'g'ri qarz ID-si"}, status=400)
        
    body = await request.json()
    months = int(body.get("months", 3))
    start_date = body.get("start_date")
    try:
        insts = await local_db.setup_debt_installments(debt_id, months, start_date)
        return json_response({"success": True, "installments": insts})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@auth_required
async def api_cancel_debt_installments(request: web.Request):
    debt_id_raw = request.match_info.get("id") or request.query.get("id", "0")
    try:
        debt_id = int(debt_id_raw)
    except ValueError:
        return json_response({"error": "Noto'g'ri qarz ID-si"}, status=400)
    try:
        await local_db.cancel_debt_installments(debt_id)
        return json_response({"success": True})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@auth_required
async def api_edit_debt(request: web.Request):
    user = request["user"]
    branch_id = None if user["role"] == "superadmin" else user["branch_id"]
    
    debt_id_raw = request.match_info.get("id")
    try:
        body = await request.json()
    except Exception:
        body = {}
        
    debt_id = int(debt_id_raw) if debt_id_raw else int(body.get("debt_id", 0))
    
    try:
        new_total_amount = float(str(body.get("new_total_amount", 0)).replace(",", "."))
    except (ValueError, TypeError):
        return json_response({"error": "Yangi qarz summasi noto'g'ri kiritildi"}, status=400)
        
    if debt_id <= 0:
        return json_response({"error": "Noto'g'ri qarz ID-si"}, status=400)
    if new_total_amount <= 0:
        return json_response({"error": "Qarz summasi 0 dan katta bo'lishi kerak"}, status=400)
        
    customer_name = body.get("customer_name")
    customer_phone = body.get("customer_phone")
    due_date = body.get("due_date")
    note = body.get("note", "")
    
    try:
        res = await local_db.edit_debt(
            debt_id=debt_id,
            new_total_amount=new_total_amount,
            branch_id=branch_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            due_date=due_date,
            note=note
        )
        return json_response(res)
    except Exception as e:
        logger.error(f"Qarzni tahrirlashda xatolik: {e}")
        return json_response({"error": str(e)}, status=400)

# --- TRANSFER VA RASXOD (XARAJAT) APIS ---

@auth_required
async def api_transfer_roll(request: web.Request):
    user = request["user"]
    from_branch = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    
    body = await request.json()
    roll_id = int(body.get("roll_id", 0))
    to_branch = int(body.get("to_branch", 0))
    if roll_id <= 0:
        return json_response({"error": "Rulon tanlanmagan"}, status=400)
    if to_branch not in BRANCH_NAMES:
        return json_response({"error": "Noto'g'ri qabul qiluvchi filial"}, status=400)
    if to_branch == from_branch:
        return json_response({"error": "O'z filialingizga transfer qilib bo'lmaydi"}, status=400)
    note = body.get("note", "").strip()
    
    transfer_length_raw = body.get("transfer_length")
    transfer_length = None
    if transfer_length_raw is not None and str(transfer_length_raw).strip() != "":
        try:
            transfer_length = float(str(transfer_length_raw).replace(",", "."))
            if transfer_length <= 0:
                return json_response({"error": "O'tkaziladigan miqdor (uzunlik) musbat son bo'lishi kerak"}, status=400)
        except ValueError:
            return json_response({"error": "O'tkaziladigan miqdor noto'g'ri kiritildi"}, status=400)
    
    try:
        res = await local_db.create_transfer_request(
            roll_id=roll_id, 
            from_branch=from_branch, 
            to_branch=to_branch, 
            transfer_length=transfer_length,
            note=note
        )
        
        # Send Telegram notification with inline buttons to destination branch users & super admins
        bot = request.app.get("bot")
        if bot:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from_name = BRANCH_NAMES.get(from_branch, f"{from_branch}-Filial")
            to_name = BRANCH_NAMES.get(to_branch, f"{to_branch}-Filial")
            msg = (
                f"🔄 *YANGI REZINKA GILAM TRANSFERI!*\n\n"
                f"📍 *Jo'natuvchi:* {from_name}\n"
                f"📍 *Qabul qiluvchi:* {to_name}\n"
                f"📦 *Rulon kodi:* `{res.get('roll_code')}`\n"
                f"📏 *O'lchami:* {res.get('width')}m x {res.get('length')}m ({res.get('color')})\n"
                f"📝 *Izoh:* {note or 'Izohsiz'}\n\n"
                f"⏳ *Mahsulot jo'natildi!* Filialga yetib borgach, qabul qilib olishni tasdiqlang:"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"tr_accept:{res['transfer_id']}"),
                    InlineKeyboardButton(text="❌ Rad etish", callback_data=f"tr_reject:{res['transfer_id']}")
                ]
            ])
            recipients = [uid for uid, bid in BRANCH_USERS.items() if bid == to_branch]
            all_to_notify = set(recipients + SUPER_ADMIN_IDS)
            for uid in all_to_notify:
                try:
                    await bot.send_message(uid, msg, parse_mode="Markdown", reply_markup=kb)
                except Exception as e:
                    logger.error(f"Transfer bildirishnomasi yuborishda xatolik ({uid}): {e}")
                    
        return json_response({"success": True, "result": res})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@auth_required
async def api_get_transfers(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    limit = int(request.query.get("limit", 50))
    transfers = await local_db.get_transfers_history(branch_id=branch_id, limit=limit)
    pending_incoming = await local_db.get_pending_transfers(branch_id=branch_id, as_recipient=True)
    pending_outgoing = await local_db.get_pending_transfers(branch_id=branch_id, as_recipient=False)
    return json_response({
        "transfers": transfers,
        "pending_incoming": pending_incoming,
        "pending_outgoing": pending_outgoing
    })

@auth_required
async def api_accept_transfer(request: web.Request):
    user = request["user"]
    body = await request.json()
    transfer_id = int(body.get("transfer_id", 0))
    if transfer_id <= 0:
        return json_response({"error": "Noto'g'ri transfer ID"}, status=400)
        
    user_branch = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    user_name = user.get("first_name") or f"Filial-{user_branch} xodimi"
    
    try:
        res = await local_db.accept_transfer(transfer_id, accepted_by=f"{user_name} ({user['role']})")
        
        bot = request.app.get("bot")
        if bot:
            from_name = BRANCH_NAMES.get(res["from_branch"], f"{res['from_branch']}-Filial")
            to_name = BRANCH_NAMES.get(res["to_branch"], f"{res['to_branch']}-Filial")
            msg = (
                f"✅ *TRANSFER QABUL QILINDI!*\n\n"
                f"📍 *Qabul qiluvchi:* {to_name}\n"
                f"📍 *Jo'natuvchi:* {from_name}\n"
                f"📦 *Rulon:* {res.get('width')}m x {res.get('length')}m ({res.get('color')})\n"
                f"👤 *Qabul qildi:* {user_name}\n\n"
                f"🎉 Mahsulot {to_name} omboriga muvaffaqiyatli kirim qilindi va sotuvga tayyor!"
            )
            recipients = [uid for uid, bid in BRANCH_USERS.items() if bid in (res["from_branch"], res["to_branch"])]
            all_to_notify = set(recipients + SUPER_ADMIN_IDS)
            for uid in all_to_notify:
                try:
                    await bot.send_message(uid, msg, parse_mode="Markdown")
                except Exception as e:
                    logger.error(f"Transfer qabul bildirishnomasi ({uid}): {e}")
                    
        return json_response({"success": True, "result": res})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@auth_required
async def api_reject_transfer(request: web.Request):
    user = request["user"]
    body = await request.json()
    transfer_id = int(body.get("transfer_id", 0))
    reason = body.get("reason", "").strip()
    if transfer_id <= 0:
        return json_response({"error": "Noto'g'ri transfer ID"}, status=400)
        
    user_branch = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    user_name = user.get("first_name") or f"Filial-{user_branch} xodimi"
    
    try:
        tr = await local_db.reject_transfer(transfer_id, rejected_by=f"{user_name} ({user['role']})", reason=reason)
        bot = request.app.get("bot")
        if bot:
            from_name = BRANCH_NAMES.get(tr["from_branch"], f"{tr['from_branch']}-Filial")
            to_name = BRANCH_NAMES.get(tr["to_branch"], f"{tr['to_branch']}-Filial")
            msg = (
                f"❌ *TRANSFER RAD ETILDI!*\n\n"
                f"📍 *Rad etgan:* {to_name} ({user_name})\n"
                f"📍 *Jo'natuvchi:* {from_name}\n"
                f"📦 *Rulon:* {tr.get('width')}m x {tr.get('length')}m ({tr.get('color')})\n"
                f"📝 *Sabab:* {reason or 'Ko''rsatilmadi'}\n\n"
                f"ℹ️ Tovar {from_name} ombori balansida qoldi."
            )
            recipients = [uid for uid, bid in BRANCH_USERS.items() if bid in (tr["from_branch"], tr["to_branch"])]
            all_to_notify = set(recipients + SUPER_ADMIN_IDS)
            for uid in all_to_notify:
                try:
                    await bot.send_message(uid, msg, parse_mode="Markdown")
                except Exception as e:
                    logger.error(f"Transfer rad bildirishnomasi ({uid}): {e}")
                    
        return json_response({"success": True})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

@auth_required
async def api_cancel_transfer(request: web.Request):
    user = request["user"]
    body = await request.json()
    transfer_id = int(body.get("transfer_id", 0))
    if transfer_id <= 0:
        return json_response({"error": "Noto'g'ri transfer ID"}, status=400)
        
    user_branch = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    is_super = user["role"] == "superadmin"
    try:
        await local_db.cancel_transfer(transfer_id, user_branch=user_branch, is_superadmin=is_super)
        return json_response({"success": True})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

# --- SUPER ADMIN OMBOR TAHRIRLASH APIS ---

@auth_required
async def api_edit_roll(request: web.Request):
    user = request["user"]
    body = await request.json()
    roll_id = int(body["roll_id"])
    
    roll = await local_db.get_roll_by_id(roll_id)
    if not roll:
        return json_response({"error": "Rulon topilmadi"}, status=404)
        
    user_branch = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    if user["role"] != "superadmin" and roll["branch_id"] != user_branch:
        return json_response({"error": "Faqat o'z filialingizdagi tovarlarni tahrirlashingiz mumkin"}, status=403)

    width = float(body["width"])
    color = str(body["color"]).strip()
    current_length = float(body["current_length"])
    price_per_m2 = float(body["price_per_m2"])
    cost_price_per_m2 = float(body.get("cost_price_per_m2")) if body.get("cost_price_per_m2") else None
    res = await local_db.update_roll(roll_id, width, color, current_length, price_per_m2, cost_price_per_m2)
    return json_response(res)

@auth_required
async def api_delete_roll(request: web.Request):
    user = request["user"]
    body = await request.json()
    roll_id = int(body["roll_id"])
    
    roll = await local_db.get_roll_by_id(roll_id)
    if not roll:
        return json_response({"error": "Rulon topilmadi"}, status=404)
        
    user_branch = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    if user["role"] != "superadmin" and roll["branch_id"] != user_branch:
        return json_response({"error": "Faqat o'z filialingizdagi tovarlarni o'chirishingiz mumkin"}, status=403)

    await local_db.delete_roll(roll_id)
    return json_response({"success": True})

@auth_required
async def api_edit_leather(request: web.Request):
    user = request["user"]
    body = await request.json()
    user_branch = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    branch_id = int(body.get("branch_id", user_branch))
    if user["role"] != "superadmin" and branch_id != user_branch:
        return json_response({"error": "Faqat o'z filialingiz omborini tahrirlashingiz mumkin"}, status=403)

    color = str(body["color"]).strip()
    quantity = int(body["quantity"])
    price_per_item = float(body["price_per_item"])
    res = await local_db.update_leather_item(branch_id, color, quantity, price_per_item)
    return json_response(res)

@auth_required
async def api_edit_kavralan(request: web.Request):
    user = request["user"]
    body = await request.json()
    roll_id = int(body["roll_id"])
    
    kav = await local_db.get_kavralan_roll_by_id(roll_id)
    if not kav:
        return json_response({"error": "Kavralan topilmadi"}, status=404)
    user_branch = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    if user["role"] != "superadmin" and kav["branch_id"] != user_branch:
        return json_response({"error": "Faqat o'z filialingizdagi tovarlarni tahrirlashingiz mumkin"}, status=403)

    current_length = float(body["current_length"])
    price_per_m2 = float(body.get("price_per_m2", 30.0))
    cost_price_per_m2 = float(body.get("cost_price_per_m2", kav.get("cost_price_per_m2", 30.0)))
    width = float(body.get("width", kav.get("width", 4.0)))
    model = str(body.get("model", kav.get("model", ""))).strip()
    color = str(body.get("color", kav.get("color", ""))).strip()
    res = await local_db.update_kavralan_roll(roll_id, current_length, price_per_m2, cost_price_per_m2=cost_price_per_m2, width=width, model=model, color=color)
    return json_response(res)

@auth_required
async def api_delete_kavralan(request: web.Request):
    user = request["user"]
    body = await request.json()
    roll_id = int(body["roll_id"])
    
    kav = await local_db.get_kavralan_roll_by_id(roll_id)
    if not kav:
        return json_response({"error": "Kavralan topilmadi"}, status=404)
    user_branch = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    if user["role"] != "superadmin" and kav["branch_id"] != user_branch:
        return json_response({"error": "Faqat o'z filialingizdagi tovarlarni o'chirishingiz mumkin"}, status=403)

    await local_db.delete_kavralan_roll(roll_id)
    return json_response({"success": True})

@auth_required
async def api_get_expenses(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    expenses = await local_db.get_expenses(branch_id=branch_id)
    return json_response({"expenses": expenses})

@auth_required
async def api_get_cash_loans(request: web.Request):
    """Kassadan qarzga berilgan pullar ro'yxati va xulosasi (faqat joriy filial)."""
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    status = request.query.get("status", "open")
    if status not in ("open", "closed", "all"):
        status = "open"
    loans = await local_db.get_cash_loans(branch_id=branch_id, status=status)
    summary = await local_db.get_cash_loans_summary(branch_id=branch_id)
    return json_response({"loans": loans, "summary": summary})

@auth_required
async def api_give_cash_loan(request: web.Request):
    """Tanlangan kassadan qarzga pul berish (kassadan LOAN_OUT bilan chiqadi)."""
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    try:
        body = await request.json()
    except Exception:
        return json_response({"error": "So'rov noto'g'ri"}, status=400)
    try:
        res = await local_db.give_cash_loan(
            branch_id=branch_id,
            category=body.get("category", ""),
            borrower_name=body.get("borrower_name", ""),
            amount=body.get("amount", 0),
            borrower_phone=body.get("borrower_phone", ""),
            due_date=body.get("due_date") or None,
            note=body.get("note", ""),
            created_by=user.get("user_id"),
        )
        return json_response({"success": True, "result": res})
    except ValueError as e:
        return json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.exception("Qarz berishda xatolik")
        return json_response({"error": f"Qarz berishda xatolik: {e}"}, status=500)

@auth_required
async def api_return_cash_loan(request: web.Request):
    """Qarzga berilgan pulning qaytishi (to'liq yoki qisman) — o'sha kassaga LOAN_RETURN bilan qaytadi."""
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    try:
        loan_id = int(request.match_info.get("id", "0"))
        body = await request.json()
    except Exception:
        return json_response({"error": "So'rov noto'g'ri"}, status=400)
    try:
        res = await local_db.return_cash_loan(
            loan_id=loan_id,
            amount=body.get("amount", 0),
            branch_id=branch_id,
            note=body.get("note", ""),
            created_by=user.get("user_id"),
        )
        return json_response({"success": True, "result": res})
    except ValueError as e:
        return json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.exception("Qarzni qaytarishda xatolik")
        return json_response({"error": f"Qarzni qaytarishda xatolik: {e}"}, status=500)

@auth_required
async def api_add_expense(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    
    body = await request.json()
    amount = float(body.get("amount", 0))
    if amount <= 0:
        return json_response({"error": "Xarajat summasi musbat bo'lishi kerak"}, status=400)
    category = body.get("category", "carpet")
    expense_title = body.get("expense_title", "Xarajat")
    note = body.get("note", "")
    
    try:
        res = await local_db.add_expense(
            amount=amount,
            branch_id=branch_id,
            category=category,
            expense_title=expense_title,
            note=note
        )
        return json_response({"success": True, "result": res})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)

# ==================== KARTAL KASSA (HISOBOTI) ROUTES ====================

@auth_required
async def api_get_kartal_cashbox(request: web.Request):
    branch_id = 2
    month = request.query.get("month", datetime.now().strftime("%Y-%m"))
    summary = await local_db.get_kartal_summary(branch_id=branch_id, month=month)
    transactions = await local_db.get_kartal_transactions(branch_id=branch_id, status="active", month=month, limit=500)
    return json_response({
        "summary": summary,
        "transactions": transactions
    })

@auth_required
async def api_add_kartal_transaction(request: web.Request):
    body = await request.json()
    op_type = str(body.get("operation_type", "INCOME")).upper().strip()
    category = str(body.get("category", "")).strip()
    amount = float(body.get("amount", 0))
    note = str(body.get("note", "")).strip()

    if amount <= 0:
        return json_response({"error": "Summa musbat bo'lishi kerak"}, status=400)
    if not category:
        return json_response({"error": "Kategoriya tanlanishi shart"}, status=400)

    res = await local_db.add_kartal_transaction(
        operation_type=op_type,
        category=category,
        amount=amount,
        note=note,
        branch_id=2
    )
    summary = await local_db.get_kartal_summary(branch_id=2)
    return json_response({"success": True, "transaction": res, "summary": summary})

@auth_required
async def api_update_kartal_transaction(request: web.Request):
    trans_id = int(request.match_info.get("id", 0))
    if trans_id <= 0:
        return json_response({"error": "Amal ID noto'g'ri"}, status=400)
    body = await request.json()
    category = str(body.get("category", "")).strip()
    amount = float(body.get("amount", 0))
    note = str(body.get("note", "")).strip()

    if amount <= 0:
        return json_response({"error": "Summa musbat bo'lishi kerak"}, status=400)
    if not category:
        return json_response({"error": "Kategoriya tanlanishi shart"}, status=400)

    await local_db.update_kartal_transaction(trans_id=trans_id, category=category, amount=amount, note=note)
    summary = await local_db.get_kartal_summary(branch_id=2)
    return json_response({"success": True, "summary": summary})

@auth_required
async def api_delete_kartal_transaction(request: web.Request):
    trans_id = int(request.match_info.get("id", 0))
    if trans_id <= 0:
        return json_response({"error": "Amal ID noto'g'ri"}, status=400)

    await local_db.delete_kartal_transaction(trans_id=trans_id)
    summary = await local_db.get_kartal_summary(branch_id=2)
    return json_response({"success": True, "summary": summary})

@auth_required
async def api_get_kartal_lichniy(request: web.Request):
    status = request.query.get("status", "active")
    if status not in ["active", "deleted"]:
        status = "active"
    transactions = await local_db.get_kartal_lichniy_transactions(branch_id=2, status=status)
    return json_response({"transactions": transactions})



@auth_required

@auth_required
async def api_edit_sale(request: web.Request):
    user = request["user"]
    body = await request.json()
    sale_id = int(body.get("sale_id", 0))
    category = str(body.get("category", "")).strip()
    try:
        new_length = float(str(body.get("new_length", 0)).replace(",", "."))
        new_total_price = float(str(body.get("new_total_price", 0)).replace(",", "."))
    except Exception:
        return json_response({"error": "Uzunlik yoki summa noto'g'ri formatda"}, status=400)
    
    if sale_id <= 0 or not category or new_length <= 0 or new_total_price <= 0:
        return json_response({"error": "Sotuv ID, uzunlik yoki summa noto'g'ri kiritildi"}, status=400)
        
    branch_id = None if user["role"] == "superadmin" else user["branch_id"]
    try:
        res = await local_db.edit_sale(sale_id, category, new_length, new_total_price, branch_id)
        return json_response(res)
    except Exception as e:
        logger.error(f"Sotuvni tahrirlashda xatolik: {e}")
        return json_response({"error": str(e)}, status=400)


async def api_delete_sale(request: web.Request):
    user = request["user"]
    body = await request.json()
    sale_id = int(body.get("sale_id", 0))
    category = str(body.get("category", "")).strip()
    
    if sale_id <= 0 or not category:
        return json_response({"error": "Sotuv ID yoki toifa noto'g'ri"}, status=400)
        
    branch_id = None if user["role"] == "superadmin" else user["branch_id"]
    try:
        res = await local_db.delete_sale(sale_id, category, branch_id)
        return json_response(res)
    except Exception as e:
        logger.error(f"Sotuvni o'chirishda xatolik: {e}")
        return json_response({"error": str(e)}, status=400)


# ==================== NOTES / BLOKNOT (IPHONE NOTES USLUBIDA) ====================

@auth_required
async def api_get_notes(request: web.Request):
    user = request["user"]
    # Har doim joriy aktiv filial uchun eslatmalar qaytariladi
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    branch_id_param = request.query.get("branch_id")
    if branch_id_param is not None and branch_id_param != "":
        try:
            branch_id = int(branch_id_param)
        except Exception:
            pass
    notes = await local_db.get_notes(branch_id=branch_id)
    return json_response({"notes": notes, "branch_id": branch_id})

@auth_required
async def api_save_note(request: web.Request):
    user = request["user"]
    body = await request.json()
    note_id = body.get("id")
    if note_id:
        try:
            note_id = int(note_id)
        except Exception:
            note_id = None
            
    title = str(body.get("title", "")).strip()
    content = str(body.get("content", "")).strip()
    is_pinned = 1 if body.get("is_pinned") else 0
    color = str(body.get("color", "yellow")).strip()
    
    # Eslatma har doim joriy aktiv filialga biriktiriladi
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
        
    if not title and not content:
        return json_response({"error": "Eslatma matni yoki sarlavhasini kiriting"}, status=400)
        
    if not title:
        # iPhone Notes behavior: first line becomes title
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        title = lines[0][:50] if lines else "Nomsiz eslatma"
        
    author_name = user.get("first_name") or user.get("username") or f"Xodim #{user.get('user_id', '')}"
    user_id = user.get("user_id")

    saved = await local_db.save_note(
        note_id=note_id,
        branch_id=branch_id,
        user_id=user_id,
        author_name=author_name,
        title=title,
        content=content,
        is_pinned=is_pinned,
        color=color
    )
    return json_response({"success": True, "note": saved})

@auth_required
async def api_delete_note(request: web.Request):
    note_id = int(request.match_info.get("id", 0))
    if not note_id:
        return json_response({"error": "Eslatma ID ko'rsatilmadi"}, status=400)
    await local_db.delete_note(note_id)
    return json_response({"success": True})

@auth_required
async def api_toggle_pin_note(request: web.Request):
    note_id = int(request.match_info.get("id", 0))
    if not note_id:
        return json_response({"error": "Eslatma ID ko'rsatilmadi"}, status=400)
    new_pinned = await local_db.toggle_pin_note(note_id)
    return json_response({"success": True, "is_pinned": new_pinned})
