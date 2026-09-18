from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_branch_menu(branch_name: str = "Filial"):
    kb = [
        [KeyboardButton(text="📥 Import (Kirim)"), KeyboardButton(text="🛒 Sotuv qilish")],
        [KeyboardButton(text="📦 Ombor qoldig'i"), KeyboardButton(text="💵 Kassa")],
        [KeyboardButton(text="📊 Dashboard"), KeyboardButton(text="📑 Excel hisobot")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_superadmin_menu():
    kb = [
        [KeyboardButton(text="🏢 1-Filial hisoboti"), KeyboardButton(text="🏢 2-Filial hisoboti")],
        [KeyboardButton(text="🌐 Barcha filiallar statistikasi")],
        [KeyboardButton(text="📑 1-Filial Excel"), KeyboardButton(text="📑 2-Filial Excel")],
        [KeyboardButton(text="📊 Umumiy Birlashgan Excel")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cancel_menu():
    kb = [
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
