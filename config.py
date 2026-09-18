import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Super Admin (Barcha filiallarni nazorat qiluvchi)
SUPER_ADMIN_IDS = [8525787653]

# Filial sotuvchilari (faqat o'z filialini ko'radi):
BRANCH_USERS = {
    8350493371: 1,  # 1-Filial xodimi
    317633066: 2    # 2-Filial xodimi
}

BRANCH_NAMES = {
    1: "1-Filial",
    2: "2-Filial"
}

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
