import hmac
import hashlib
import json
import time
import secrets
import urllib.parse
from typing import Optional, Dict
from config import BOT_TOKEN, SUPER_ADMIN_IDS, BRANCH_USERS, BRANCH_NAMES

# Session storage in-memory: token -> session_data
SESSIONS: Dict[str, dict] = {}

# QR Auth requests: qr_token -> qr_state
QR_REQUESTS: Dict[str, dict] = {}

def get_user_role_and_branch(user_id: int):
    """Foydalanuvchi roli va filialini aniqlash"""
    if user_id in SUPER_ADMIN_IDS:
        return "superadmin", 1
    if user_id in BRANCH_USERS:
        return "branch", BRANCH_USERS[user_id]
    return None, None

def verify_telegram_webapp_data(init_data: str) -> Optional[dict]:
    """
    Telegram WebApp initData ni tekshirish (HMAC-SHA256).
    Muvaffaqiyatli bo'lsa user ma'lumotlarini dict ko'rinishida qaytaradi.
    Replay attack oldini olish uchun 24 soatlik muddat tekshiriladi.
    """
    if not init_data or not BOT_TOKEN:
        return None

    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data))
        if "hash" not in parsed_data:
            return None
        received_hash = parsed_data.pop("hash")

        # Replay attack himoyasi (auth_date 24 soatdan oshgan bo'lmasligi kerak)
        auth_date = int(parsed_data.get("auth_date", 0))
        if auth_date > 0 and (time.time() - auth_date > 86400):
            return None

        # Kalitlarni alifbo bo'yicha saralash
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))

        # Secret key = HMAC_SHA256("WebAppData", BOT_TOKEN)
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
        
        # Expected hash = HMAC_SHA256(secret_key, data_check_string)
        expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if hmac.compare_digest(received_hash, expected_hash):
            user_json = parsed_data.get("user")
            if user_json:
                return json.loads(user_json)
        return None
    except Exception as e:
        print(f"Telegram initData tekshirishda xatolik: {e}")
        return None

def create_session(user_id: int, user_info: Optional[dict] = None) -> Optional[dict]:
    """Foydalanuvchi uchun xavfsiz sessiya tokeni yaratish"""
    role, default_branch = get_user_role_and_branch(user_id)
    if not role:
        return None

    session_token = secrets.token_urlsafe(32)
    first_name = (user_info or {}).get("first_name", "") or (user_info or {}).get("name", "Foydalanuvchi")
    username = (user_info or {}).get("username", "")

    session = {
        "token": session_token,
        "user_id": user_id,
        "role": role,
        "branch_id": default_branch,
        "active_branch": default_branch,
        "first_name": first_name,
        "username": username,
        "created_at": time.time(),
        "expires_at": time.time() + (86400 * 30) # 30 kun
    }
    SESSIONS[session_token] = session
    return session

def get_session(token: str) -> Optional[dict]:
    """Sessiya ma'lumotlarini olish"""
    if not token or token not in SESSIONS:
        return None
    session = SESSIONS[token]
    if time.time() > session["expires_at"]:
        del SESSIONS[token]
        return None
    return session

def create_qr_request() -> dict:
    """Kompyuter orqali kirish uchun QR so'rov yaratish"""
    qr_token = secrets.token_urlsafe(24)
    QR_REQUESTS[qr_token] = {
        "status": "pending",
        "created_at": time.time(),
        "user_id": None,
        "session_token": None
    }
    # Eski so'rovlarni tozalash (10 daqiqadan oshgan)
    now = time.time()
    for k in list(QR_REQUESTS.keys()):
        if now - QR_REQUESTS[k]["created_at"] > 600:
            QR_REQUESTS.pop(k, None)
            
    return {"qr_token": qr_token}

def approve_qr_request(qr_token: str, user_id: int, user_info: Optional[dict] = None) -> bool:
    """Telegram bot orqali QR kirishni tasdiqlash"""
    if qr_token not in QR_REQUESTS:
        return False
    
    req = QR_REQUESTS[qr_token]
    if req["status"] != "pending":
        return False

    session = create_session(user_id, user_info)
    if not session:
        return False

    req["status"] = "approved"
    req["user_id"] = user_id
    req["session_token"] = session["token"]
    return True
