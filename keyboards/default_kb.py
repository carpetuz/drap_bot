from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_branch_menu(branch_name: str = "Filial"):
    kb = [
        [KeyboardButton(text="🌀 Rezinka Gilam"), KeyboardButton(text="🐑 Teri Bo'limi")],
        [KeyboardButton(text="🧶 Asl Kavralan"), KeyboardButton(text="📦 Umumiy Ombor")],
        [KeyboardButton(text="💵 Kassa"), KeyboardButton(text="📒 Nasiya / Qarzlar")],
        [KeyboardButton(text="📊 Dashboard"), KeyboardButton(text="📑 Excel hisobot")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_carpet_submenu():
    kb = [
        [KeyboardButton(text="📥 Gilam Kirim"), KeyboardButton(text="🛒 Gilam Sotuv")],
        [KeyboardButton(text="📦 Gilam Ombori"), KeyboardButton(text="🔙 Bosh menyu")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_leather_submenu():
    kb = [
        [KeyboardButton(text="📥 Teri Kirim"), KeyboardButton(text="🛒 Teri Sotuv")],
        [KeyboardButton(text="📦 Teri Ombori"), KeyboardButton(text="🔙 Bosh menyu")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_kavralan_submenu():
    kb = [
        [KeyboardButton(text="📥 Kavralan Kirim"), KeyboardButton(text="🛒 Kavralan Sotuv")],
        [KeyboardButton(text="📦 Kavralan Ombori"), KeyboardButton(text="🔙 Bosh menyu")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_branch3_menu():
    kb = [
        [KeyboardButton(text="🛒 Sotuv"), KeyboardButton(text="📊 Hisobot")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_superadmin_menu():
    kb = [
        [KeyboardButton(text="🏢 1-Filial hisoboti"), KeyboardButton(text="🏢 2-Filial hisoboti")],
        [KeyboardButton(text="🏢 3-Filial hisoboti"), KeyboardButton(text="🌐 Barcha filiallar statistikasi")],
        [KeyboardButton(text="📒 Nasiya / Qarzlar"), KeyboardButton(text="📊 Umumiy Birlashgan Excel")],
        [KeyboardButton(text="📑 1-Filial Excel"), KeyboardButton(text="📑 2-Filial Excel")],
        [KeyboardButton(text="📑 3-Filial Excel")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cancel_menu():
    kb = [
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
