import json
import logging
from aiohttp import web
from config import (
    BRANCH_NAMES, BRANCH3_COLLECTIONS, BRANCH3_WIDTH, 
    AVAILABLE_WIDTHS, AVAILABLE_COLORS, LEATHER_COLORS, KAVRALAN_WIDTH
)
from database import local_db
from web.auth import (
    verify_telegram_webapp_data, create_session, get_session, delete_session,
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
            if length <= 0 or price_per_m2 <= 0:
                return json_response({"error": "Noto'g'ri o'lcham yoki narx kiritildi"}, status=400)
            res = await local_db.add_kavralan_roll(length, branch_id, price_per_m2)
            return json_response({"success": True, "item": res})
        elif product_type == "leather":
            color = str(body.get("color", "")).strip()
            quantity = int(body.get("quantity", 0))
            price_per_item = float(body.get("price_per_item", 50.0))
            if quantity <= 0 or price_per_item <= 0 or not color:
                return json_response({"error": "Noto'g'ri miqdor yoki narx kiritildi"}, status=400)
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
    is_rezinka_only = (branch_id == 2 or user.get("user_id") == 317633066)
    
    body = await request.json()
    product_type = body.get("product_type", "carpet")
    
    if is_rezinka_only and product_type != "carpet":
        return json_response({"error": "Sizning hisobingizda faqat rezinka gilam sotiladi"}, status=403)
    
    is_debt = bool(body.get("is_debt", False))
    customer_name = str(body.get("customer_name", "")).strip()
    customer_phone = str(body.get("customer_phone", "")).strip()
    initial_paid = float(body.get("initial_paid", 0.0))
    if initial_paid < 0:
        return json_response({"error": "Boshlang'ich to'lov manfiy bo'lishi mumkin emas"}, status=400)
    
    raw_total = body.get("total_price")
    custom_total_price = float(raw_total) if raw_total is not None and str(raw_total).strip() != "" and float(raw_total) > 0 else None
    
    try:
        if product_type == "carpet":
            roll_id = int(body.get("roll_id", 0))
            sold_length = float(body.get("sold_length", 0))
            price_per_m2 = float(body.get("price_per_m2", 0))
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
                initial_paid=initial_paid
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
                initial_paid=initial_paid
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
                initial_paid=initial_paid
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
        
    period = request.query.get("period", "today")
    date_from = request.query.get("date_from")
    date_to = request.query.get("date_to")
    
    try:
        report = await local_db.get_profit_loss_report(
            branch_id=branch_id,
            period=period,
            date_from=date_from,
            date_to=date_to
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
    
    try:
        res = await local_db.pay_debt(debt_id=debt_id, payment_amount=amount, branch_id=branch_id, note=note)
        return json_response({"success": True, "result": res})
    except Exception as e:
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
            transfer_length = float(transfer_length_raw)
            if transfer_length <= 0:
                return json_response({"error": "O'tkaziladigan miqdor (uzunlik) musbat son bo'lishi kerak"}, status=400)
        except ValueError:
            return json_response({"error": "O'tkaziladigan miqdor noto'g'ri kiritildi"}, status=400)
    
    try:
        res = await local_db.transfer_roll(
            roll_id=roll_id, 
            from_branch=from_branch, 
            to_branch=to_branch, 
            transfer_length=transfer_length,
            note=note
        )
        
        # Send Telegram notification to destination branch users & super admins
        bot = request.app.get("bot")
        if bot:
            from_name = BRANCH_NAMES.get(from_branch, f"{from_branch}-Filial")
            to_name = BRANCH_NAMES.get(to_branch, f"{to_branch}-Filial")
            msg = (
                f"🔄 *YANGI REZINKA GILAM TRANSFERI!*\n\n"
                f"📍 *Jo'natuvchi:* {from_name}\n"
                f"📍 *Qabul qiluvchi:* {to_name}\n"
                f"📦 *Rulon kodi:* `{res.get('roll_code')}`\n"
                f"📏 *O'lchami:* {res.get('width')}m x {res.get('current_length')}m ({res.get('color')})\n"
                f"📝 *Izoh:* {note or 'Izohsiz'}\n\n"
                f"✅ Ushbu rulon endi {to_name} omboriga muvaffaqiyatli qabul qilindi va sotuvga tayyor!"
            )
            recipients = [uid for uid, bid in BRANCH_USERS.items() if bid == to_branch]
            all_to_notify = set(recipients + SUPER_ADMIN_IDS)
            for uid in all_to_notify:
                try:
                    await bot.send_message(uid, msg, parse_mode="Markdown")
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
    return json_response({"transfers": transfers})

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
    res = await local_db.update_kavralan_roll(roll_id, current_length, price_per_m2)
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

