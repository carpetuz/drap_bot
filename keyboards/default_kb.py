from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    kb = [
        [KeyboardButton(text="📥 Import (Kirim)"), KeyboardButton(text="🛒 Sotuv qilish")],
        [KeyboardButton(text="📦 Ombor qoldig'i"), KeyboardButton(text="💵 Kassa")],
        [KeyboardButton(text="📊 Dashboard"), KeyboardButton(text="📑 Excel hisobot")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cancel_menu():
    kb = [
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
