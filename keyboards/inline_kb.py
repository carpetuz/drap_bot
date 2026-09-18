from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import AVAILABLE_WIDTHS, AVAILABLE_COLORS

def get_width_kb(action_prefix="import_width"):
    buttons = []
    row = []
    for w in AVAILABLE_WIDTHS:
        # Masalan 0.8x, 1x, 1.2x, 1.6x, 2x
        label = f"{w:g}x"
        row.append(InlineKeyboardButton(text=label, callback_data=f"{action_prefix}:{w}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_color_kb(action_prefix="import_color"):
    buttons = []
    row = []
    for c in AVAILABLE_COLORS:
        row.append(InlineKeyboardButton(text=c, callback_data=f"{action_prefix}:{c}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_import_kb():
    buttons = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_import"),
            InlineKeyboardButton(text="✏️ Qayta kiritish", callback_data="retry_import")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_available_widths_kb(widths: list[float]):
    buttons = []
    row = []
    for w in widths:
        label = f"{w:g}x"
        row.append(InlineKeyboardButton(text=label, callback_data=f"sale_width:{w}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_available_colors_kb(colors: list[str]):
    buttons = []
    row = []
    for c in colors:
        row.append(InlineKeyboardButton(text=c, callback_data=f"sale_color:{c}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Boshqa eni tanlash", callback_data="sale_back_to_width")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_rolls_selection_kb(rolls: list[dict]):
    buttons = []
    for r in rolls:
        # Masalan: #1001: 1.6x10.95m - Kofe
        label = f"{r['roll_code']}: {r['width']:g}x{r['current_length']}m - {r['color']}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"sale_roll:{r['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Boshqa rang tanlash", callback_data="sale_back_to_color")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_sale_kb():
    buttons = [
        [
            InlineKeyboardButton(text="✅ Sotuvni tasdiqlash", callback_data="confirm_sale"),
            InlineKeyboardButton(text="✏️ O'zgartirish", callback_data="retry_sale")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cash_menu_kb():
    buttons = [
        [InlineKeyboardButton(text="📤 Kassa topshirish (Chiqim)", callback_data="cash_withdraw")],
        [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_withdraw_kb():
    buttons = [
        [
            InlineKeyboardButton(text="✅ Topshirishni tasdiqlash", callback_data="confirm_withdraw"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
