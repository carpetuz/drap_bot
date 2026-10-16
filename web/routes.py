import json
import logging
from aiohttp import web
from config import (
    BRANCH_NAMES, BRANCH3_COLLECTIONS, BRANCH3_WIDTH, 
    AVAILABLE_WIDTHS, AVAILABLE_COLORS, LEATHER_COLORS, KAVRALAN_WIDTH
)
from database import local_db
from web.auth import (
    verify_telegram_webapp_data, create_session, get_session, 
    create_qr_request, QR_REQUESTS
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
        # Query parameter fallback (for easy dev or Telegram Mini App)
        token = request.query.get("token")
        
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
            "user": session
        })
        resp.set_cookie("crm_session", session["token"], max_age=86400*30, httponly=False)
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
            "user": session
        })
        resp.set_cookie("crm_session", req["session_token"], max_age=86400*30, httponly=False)
        return resp
    return json_response({"status": req["status"]})

@auth_required
async def api_auth_me(request: web.Request):
    """Joriy foydalanuvchi ma'lumotlari"""
    user = request["user"]
    return json_response({
        "user": user,
        "branch_names": BRANCH_NAMES,
        "collections": BRANCH3_COLLECTIONS
    })

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
        length = float(body.get("length", 0))
        price_per_m2 = body.get("price_per_m2")
        
        if not collection or collection not in BRANCH3_COLLECTIONS:
            return json_response({"error": "Noto'g'ri kolleksiya tanlandi"}, status=400)
        if length <= 0:
            return json_response({"error": "Uzunlik 0 dan katta bo'lishi kerak"}, status=400)
            
        custom_price = float(price_per_m2) if price_per_m2 else None
        res = await local_db.add_branch3_sale(
            collection_name=collection,
            length=length,
            branch_id=branch_id,
            custom_price_per_m2=custom_price
        )
        return json_response({"success": True, "sale": res})

# --- GILAM VA OMBOR APIS ---

@auth_required
async def api_get_stock(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    
    rolls = await local_db.get_all_active_rolls(branch_id=branch_id)
    kavralan = await local_db.get_all_active_kavralan_rolls(branch_id=branch_id)
    leather = await local_db.get_leather_stock(branch_id=branch_id)
    
    return json_response({
        "branch_id": branch_id,
        "branch_name": BRANCH_NAMES.get(branch_id, "Filial"),
        "rolls": rolls,
        "kavralan_rolls": kavralan,
        "leather": leather,
        "config": {
            "available_widths": AVAILABLE_WIDTHS,
            "available_colors": AVAILABLE_COLORS,
            "leather_colors": LEATHER_COLORS,
            "kavralan_width": KAVRALAN_WIDTH,
            "branch3_collections": BRANCH3_COLLECTIONS
        }
    })

@auth_required
async def api_add_roll(request: web.Request):
    user = request["user"]
    branch_id = user["active_branch"] if user["role"] == "superadmin" else user["branch_id"]
    
    body = await request.json()
    product_type = body.get("product_type", "carpet") # carpet, kavralan, leather
    
    try:
        if product_type == "carpet":
            width = float(body["width"])
            color = str(body["color"]).strip()
            length = float(body["length"])
            price_per_m2 = float(body.get("price_per_m2", 8.0))
            res = await local_db.add_roll(width, color, length, branch_id, price_per_m2)
            return json_response({"success": True, "item": res})
        elif product_type == "kavralan":
            length = float(body["length"])
            price_per_m2 = float(body.get("price_per_m2", 30.0))
            res = await local_db.add_kavralan_roll(length, branch_id, price_per_m2)
            return json_response({"success": True, "item": res})
        elif product_type == "leather":
            color = str(body["color"]).strip()
            quantity = int(body["quantity"])
            price_per_item = float(body.get("price_per_item", 50.0))
            res = await local_db.add_leather_stock(color, quantity, branch_id, price_per_item)
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
    
    body = await request.json()
    product_type = body.get("product_type", "carpet")
    is_debt = bool(body.get("is_debt", False))
    customer_name = str(body.get("customer_name", "")).strip()
    customer_phone = str(body.get("customer_phone", "")).strip()
    initial_paid = float(body.get("initial_paid", 0.0))
    
    try:
        if product_type == "carpet":
            roll_id = int(body["roll_id"])
            sold_length = float(body["sold_length"])
            price_per_m2 = float(body["price_per_m2"])
            res = await local_db.make_sale(
                roll_id=roll_id,
                sold_length=sold_length,
                branch_id=branch_id,
                price_per_m2=price_per_m2,
                is_debt=is_debt,
                customer_name=customer_name,
                customer_phone=customer_phone,
                initial_paid=initial_paid
            )
            return json_response({"success": True, "sale": res})
        elif product_type == "kavralan":
            roll_id = int(body["roll_id"])
            sold_length = float(body["sold_length"])
            price_per_m2 = float(body["price_per_m2"])
            res = await local_db.make_kavralan_sale(
                roll_id=roll_id,
                sold_length=sold_length,
                branch_id=branch_id,
                price_per_m2=price_per_m2,
                is_debt=is_debt,
                customer_name=customer_name,
                customer_phone=customer_phone,
                initial_paid=initial_paid
            )
            return json_response({"success": True, "sale": res})
        elif product_type == "leather":
            color = str(body["color"]).strip()
            quantity = int(body["quantity"])
            price_per_item = float(body["price_per_item"])
            res = await local_db.make_leather_sale(
                color=color,
                quantity=quantity,
                branch_id=branch_id,
                price_per_item=price_per_item,
                is_debt=is_debt,
                customer_name=customer_name,
                customer_phone=customer_phone,
                initial_paid=initial_paid
            )
            return json_response({"success": True, "sale": res})
        else:
            return json_response({"error": "Noma'lum tovar turi"}, status=400)
    except Exception as e:
        logger.error(f"Sotuvda xatolik: {e}")
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
    debt_id = int(body["debt_id"])
    amount = float(body["amount"])
    note = body.get("note", "")
    
    try:
        res = await local_db.pay_debt(debt_id=debt_id, payment_amount=amount, branch_id=branch_id, note=note)
        return json_response({"success": True, "result": res})
    except Exception as e:
        return json_response({"error": str(e)}, status=400)
