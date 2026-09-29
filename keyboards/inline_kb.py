from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import AVAILABLE_WIDTHS, AVAILABLE_COLORS, LEATHER_COLORS

# --- GILAM TUGMALARI ---
def get_width_kb(action_prefix="import_width"):
    buttons = []
    row = []
    for w in AVAILABLE_WIDTHS:
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
        label = f"{r['roll_code']}: {r['width']:g}x{r['current_length']}m - {r['color']}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"sale_roll:{r['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Boshqa rang tanlash", callback_data="sale_back_to_color")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_sale_kb():
    buttons = [
        [
            InlineKeyboardButton(text="💵 Naqd to'lov", callback_data="confirm_sale_cash"),
            InlineKeyboardButton(text="📝 Nasiya (Qarz)", callback_data="sale_debt_start")
        ],
        [
            InlineKeyboardButton(text="✏️ O'zgartirish", callback_data="retry_sale"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- TERI TUGMALARI ---
def get_leather_colors_kb(action_prefix="leather_import_color"):
    buttons = []
    for c in LEATHER_COLORS:
        buttons.append([InlineKeyboardButton(text=f"🐑 {c}", callback_data=f"{action_prefix}:{c}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_available_leather_colors_kb(colors_stock: list[dict]):
    buttons = []
    for item in colors_stock:
        # Masalan: "🐑 Oppoq (7 dona)"
        label = f"🐑 {item['color']} ({item['quantity']} dona mavjud)"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"leather_sale_color:{item['color']}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_leather_import_kb():
    buttons = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_leather_import"),
            InlineKeyboardButton(text="✏️ Qayta kiritish", callback_data="retry_leather_import")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_leather_sale_kb():
    buttons = [
        [
            InlineKeyboardButton(text="💵 Naqd to'lov", callback_data="confirm_leather_sale_cash"),
            InlineKeyboardButton(text="📝 Nasiya (Qarz)", callback_data="leather_debt_start")
        ],
        [
            InlineKeyboardButton(text="✏️ O'zgartirish", callback_data="retry_leather_sale"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ASL KAVRALAN TUGMALARI ---
def get_confirm_kavralan_import_kb():
    buttons = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_kavralan_import"),
            InlineKeyboardButton(text="✏️ Qayta kiritish", callback_data="retry_kavralan_import")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_kavralan_rolls_selection_kb(rolls: list[dict]):
    buttons = []
    for r in rolls:
        label = f"{r['roll_code']}: 4x{r['current_length']}m ({r['area_m2']} m²)"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"kavralan_sale_roll:{r['id']}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_kavralan_sale_kb():
    buttons = [
        [
            InlineKeyboardButton(text="💵 Naqd to'lov", callback_data="confirm_kavralan_sale_cash"),
            InlineKeyboardButton(text="📝 Nasiya (Qarz)", callback_data="kavralan_debt_start")
        ],
        [
            InlineKeyboardButton(text="✏️ O'zgartirish", callback_data="retry_kavralan_sale"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- NASIYA (QARZ) TUGMALARI ---
def get_confirm_debt_sale_kb(category="carpet"):
    prefix = "carpet" if category == "carpet" else ("leather" if category == "leather" else "kavralan")
    buttons = [
        [
            InlineKeyboardButton(text="✅ Nasiyani tasdiqlash", callback_data=f"confirm_{prefix}_debt_final"),
            InlineKeyboardButton(text="✏️ Qayta kiritish", callback_data=f"retry_{prefix}_debt")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_debts_main_kb(is_superadmin=False):
    buttons = [
        [InlineKeyboardButton(text="📋 Faol Nasiyalar ro'yxati", callback_data="debts_active_list")],
        [InlineKeyboardButton(text="💰 Qarz to'lovini qabul qilish", callback_data="debts_pay_start")],
        [InlineKeyboardButton(text="📜 Yopilgan qarzlar tarixi", callback_data="debts_history")],
        [InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_debts_selection_kb(debts: list[dict]):
    buttons = []
    for d in debts:
        cat_emoji = "🌀" if d["category"] == "carpet" else ("🐑" if d["category"] == "leather" else "🧶")
        label = f"{cat_emoji} {d['customer_name']} (${d['remaining_amount']:.2f} qarz)"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"debt_pay_select:{d['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="debts_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_pay_debt_kb(debt_id: int):
    buttons = [
        [
            InlineKeyboardButton(text="✅ To'lovni tasdiqlash", callback_data=f"confirm_pay_debt:{debt_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- KASSA TUGMALARI (ALOHIDA BO'LINGAN) ---
def get_cash_categories_kb():
    buttons = [
        [InlineKeyboardButton(text="📤 🌀 Gilam kassasini topshirish", callback_data="withdraw_cat:carpet")],
        [InlineKeyboardButton(text="📤 🐑 Teri kassasini topshirish", callback_data="withdraw_cat:leather")],
        [InlineKeyboardButton(text="📤 🧶 Kavralan kassasini topshirish", callback_data="withdraw_cat:kavralan")],
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

# --- 3-FILIAL TUGMALARI ---
def get_branch3_collections_kb():
    buttons = [
        [InlineKeyboardButton(text="💎 Laughton ($30 / m²)", callback_data="b3_coll:Laughton")],
        [InlineKeyboardButton(text="✨ Craft ($45 / m²)", callback_data="b3_coll:Craft")],
        [InlineKeyboardButton(text="🌸 Pretty ($38 / m²)", callback_data="b3_coll:Pretty")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_branch3_confirm_sale_kb():
    buttons = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="b3_confirm_sale"),
            InlineKeyboardButton(text="✏️ Qayta kiritish", callback_data="b3_retry_sale")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_branch3_report_kb():
    buttons = [
        [InlineKeyboardButton(text="📜 Sotuvlar tarixi", callback_data="b3_history")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


