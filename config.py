import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Super Admin (Barcha filiallarni nazorat qiluvchi)
SUPER_ADMIN_IDS = [8525787653]

# Filial sotuvchilari (faqat o'z filialini ko'radi):
BRANCH_USERS = {
    8350493371: 1,  # 1-Filial xodimi
    317633066: 2,   # 2-Filial xodimi
    5539220491: 3   # 3-Filial xodimi
}

BRANCH_NAMES = {
    1: "1-Filial",
    2: "2-Filial",
    3: "3-Filial"
}

# 1. Rezinka gilam parametrlari
PRICE_PER_M2 = float(os.getenv("PRICE_PER_M2", "8.0"))
AVAILABLE_WIDTHS = [0.8, 1.0, 1.2, 1.6, 2.0]
AVAILABLE_COLORS = [
    "Seriy",
    "Kofe",
    "Qizil",
    "Bordo",
    "Qora",
    "Yashil",
    "Ko'k"
]

# 2. Teri parametrlari
LEATHER_PRICE = 50.0  # 1 dona = $50
LEATHER_COLORS = [
    "Oppoq",
    "Bejiviy",
    "Seriy"
]

# 3. Asl Kavralan parametrlari
KAVRALAN_PRICE = float(os.getenv("KAVRALAN_PRICE", "30.0"))  # 1 m² = $30
KAVRALAN_WIDTH = 4.0  # Doimiy eni 4 metr (4x)

# 4. 3-Filial mahsulotlari (Omborsiz to'g'ridan-to'g'ri sotuv, eni 4 metr)
BRANCH3_WIDTH = 4.0
BRANCH3_COLLECTIONS = {
    "Laughton": 30.0,  # $30 / m²
    "Craft": 45.0,     # $45 / m²
    "Pretty": 38.0     # $38 / m²
}


