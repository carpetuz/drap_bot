import os
import aiosqlite
from datetime import datetime
from config import PRICE_PER_M2, LEATHER_PRICE, BRANCH_NAMES, LEATHER_COLORS, KAVRALAN_PRICE, KAVRALAN_WIDTH, BRANCH3_WIDTH, BRANCH3_COLLECTIONS

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Gilam ombori
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rolls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL DEFAULT 1,
                roll_code TEXT UNIQUE,
                width REAL NOT NULL,
                color TEXT NOT NULL,
                initial_length REAL NOT NULL,
                current_length REAL NOT NULL,
                area_m2 REAL NOT NULL,
                price_per_m2 REAL NOT NULL DEFAULT 8.0,
                total_price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL
            )
        """)
        # 2. Gilam sotuvlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL DEFAULT 1,
                roll_id INTEGER NOT NULL,
                roll_code TEXT NOT NULL,
                width REAL NOT NULL,
                color TEXT NOT NULL,
                sold_length REAL NOT NULL,
                area_m2 REAL NOT NULL,
                price_per_m2 REAL NOT NULL,
                total_price REAL NOT NULL,
                cost_price REAL DEFAULT 0.0,
                profit REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (roll_id) REFERENCES rolls (id)
            )
        """)
        # 3. Teri ombori
        await db.execute("""
            CREATE TABLE IF NOT EXISTS leather_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL,
                color TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                price_per_item REAL NOT NULL DEFAULT 50.0,
                updated_at TEXT NOT NULL,
                UNIQUE(branch_id, color)
            )
        """)
        # 4. Teri sotuvlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS leather_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL,
                color TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_item REAL NOT NULL,
                total_price REAL NOT NULL,
                cost_price REAL DEFAULT 0.0,
                profit REAL DEFAULT 0.0,
                created_at TEXT NOT NULL
            )
        """)
        # 5. Kassa (category ustuni bilan: 'carpet' yoki 'leather')
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cashbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL DEFAULT 1,
                category TEXT NOT NULL DEFAULT 'carpet',
                operation_type TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                balance_after REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # 6. Nasiya (Qarz) daftari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL DEFAULT 1,
                category TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                item_details TEXT NOT NULL,
                total_amount REAL NOT NULL,
                initial_paid REAL NOT NULL DEFAULT 0.0,
                paid_amount REAL NOT NULL DEFAULT 0.0,
                remaining_amount REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'unpaid',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # 7. Qarz to'lovlari tarixi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS debt_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                debt_id INTEGER NOT NULL,
                branch_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (debt_id) REFERENCES debts (id)
            )
        """)
        
        # 8. Asl Kavralan ombori (4x rulonlar)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS kavralan_rolls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL DEFAULT 1,
                roll_code TEXT UNIQUE,
                model TEXT DEFAULT '',
                color TEXT DEFAULT '',
                width REAL NOT NULL DEFAULT 4.0,
                initial_length REAL NOT NULL,
                current_length REAL NOT NULL,
                area_m2 REAL NOT NULL,
                total_price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL
            )
        """)
        
        # 9. Asl Kavralan sotuvlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS kavralan_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL DEFAULT 1,
                roll_id INTEGER NOT NULL,
                roll_code TEXT NOT NULL,
                width REAL NOT NULL DEFAULT 4.0,
                sold_length REAL NOT NULL,
                area_m2 REAL NOT NULL,
                price_per_m2 REAL NOT NULL DEFAULT 30.0,
                total_price REAL NOT NULL,
                cost_price REAL DEFAULT 0.0,
                profit REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (roll_id) REFERENCES kavralan_rolls (id)
            )
        """)
        
        # 10. 3-Filial sotuvlari (Omborsiz)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS branch3_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL DEFAULT 3,
                collection_name TEXT NOT NULL,
                width REAL NOT NULL DEFAULT 4.0,
                length REAL NOT NULL,
                area_m2 REAL NOT NULL,
                price_per_m2 REAL NOT NULL,
                total_price REAL NOT NULL,
                cost_price REAL DEFAULT 0.0,
                profit REAL DEFAULT 0.0,
                payment_type TEXT NOT NULL DEFAULT 'cash',
                created_at TEXT NOT NULL
            )
        """)
        
        # 11. Transfers
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_id INTEGER NOT NULL,
                roll_code TEXT NOT NULL,
                from_branch INTEGER NOT NULL,
                to_branch INTEGER NOT NULL,
                width REAL NOT NULL,
                color TEXT NOT NULL,
                length REAL NOT NULL,
                note TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                target_roll_id INTEGER,
                target_roll_code TEXT,
                accepted_at TEXT,
                accepted_by TEXT,
                rejected_at TEXT,
                rejected_by TEXT,
                created_at TEXT NOT NULL
            )
        """)

        try:
            async with db.execute("PRAGMA table_info(transfers)") as cur:
                cols = [row[1] for row in await cur.fetchall()]
                if "status" not in cols:
                    await db.execute("ALTER TABLE transfers ADD COLUMN status TEXT NOT NULL DEFAULT 'accepted'")
                if "target_roll_id" not in cols:
                    await db.execute("ALTER TABLE transfers ADD COLUMN target_roll_id INTEGER")
                if "target_roll_code" not in cols:
                    await db.execute("ALTER TABLE transfers ADD COLUMN target_roll_code TEXT")
                if "accepted_at" not in cols:
                    await db.execute("ALTER TABLE transfers ADD COLUMN accepted_at TEXT")
                if "accepted_by" not in cols:
                    await db.execute("ALTER TABLE transfers ADD COLUMN accepted_by TEXT")
                if "rejected_at" not in cols:
                    await db.execute("ALTER TABLE transfers ADD COLUMN rejected_at TEXT")
                if "rejected_by" not in cols:
                    await db.execute("ALTER TABLE transfers ADD COLUMN rejected_by TEXT")
        except Exception:
            pass
        
        # 12. Nasiyani muddatli to'lash (Bo'lib to'lash grafiki)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS debt_installments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                debt_id INTEGER NOT NULL,
                branch_id INTEGER NOT NULL,
                month_number INTEGER NOT NULL,
                due_date TEXT NOT NULL,
                amount REAL NOT NULL,
                paid_amount REAL NOT NULL DEFAULT 0.0,
                status TEXT NOT NULL DEFAULT 'pending',
                paid_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (debt_id) REFERENCES debts (id) ON DELETE CASCADE
            )
        """)

        # Nasiya va to'lovlar jadvallari uchun yangi ustunlar
        try:
            async with db.execute("PRAGMA table_info(debts)") as cur:
                cols = [row[1] for row in await cur.fetchall()]
                if "due_date" not in cols:
                    await db.execute("ALTER TABLE debts ADD COLUMN due_date TEXT")
                if "is_installment" not in cols:
                    await db.execute("ALTER TABLE debts ADD COLUMN is_installment INTEGER NOT NULL DEFAULT 0")
                if "installment_months" not in cols:
                    await db.execute("ALTER TABLE debts ADD COLUMN installment_months INTEGER NOT NULL DEFAULT 1")
                if "customer_telegram_id" not in cols:
                    await db.execute("ALTER TABLE debts ADD COLUMN customer_telegram_id INTEGER")
        except Exception:
            pass

        try:
            async with db.execute("PRAGMA table_info(debt_payments)") as cur:
                cols = [row[1] for row in await cur.fetchall()]
                if "payment_method" not in cols:
                    await db.execute("ALTER TABLE debt_payments ADD COLUMN payment_method TEXT NOT NULL DEFAULT 'cash'")
                if "installment_id" not in cols:
                    await db.execute("ALTER TABLE debt_payments ADD COLUMN installment_id INTEGER")
        except Exception:
            pass

        # Xavfsiz avtomatik migratsiyalar
        for tbl in ["rolls", "sales", "cashbox", "debts", "kavralan_rolls", "kavralan_sales", "branch3_sales"]:
            try:
                async with db.execute(f"PRAGMA table_info({tbl})") as cur:
                    cols = [row[1] for row in await cur.fetchall()]
                    if "branch_id" not in cols:
                        await db.execute(f"ALTER TABLE {tbl} ADD COLUMN branch_id INTEGER NOT NULL DEFAULT 1")
            except Exception:
                pass

        for tbl in ["sales", "leather_sales", "kavralan_sales", "branch3_sales"]:
            try:
                async with db.execute(f"PRAGMA table_info({tbl})") as cur:
                    cols = [row[1] for row in await cur.fetchall()]
                    if "cost_price" not in cols:
                        await db.execute(f"ALTER TABLE {tbl} ADD COLUMN cost_price REAL DEFAULT 0.0")
                    if "profit" not in cols:
                        await db.execute(f"ALTER TABLE {tbl} ADD COLUMN profit REAL DEFAULT 0.0")
            except Exception:
                pass

        try:
            async with db.execute("PRAGMA table_info(kavralan_rolls)") as cur:
                cols = [row[1] for row in await cur.fetchall()]
                if "model" not in cols:
                    await db.execute("ALTER TABLE kavralan_rolls ADD COLUMN model TEXT DEFAULT ''")
                if "color" not in cols:
                    await db.execute("ALTER TABLE kavralan_rolls ADD COLUMN color TEXT DEFAULT ''")
                if "cost_price_per_m2" not in cols:
                    await db.execute("ALTER TABLE kavralan_rolls ADD COLUMN cost_price_per_m2 REAL DEFAULT 30.0")
                if "price_per_m2" not in cols:
                    await db.execute("ALTER TABLE kavralan_rolls ADD COLUMN price_per_m2 REAL DEFAULT 30.0")
            await db.execute("UPDATE kavralan_rolls SET cost_price_per_m2 = 30.0 WHERE cost_price_per_m2 IS NULL OR cost_price_per_m2 = 0.0")
            await db.execute("UPDATE kavralan_rolls SET price_per_m2 = 30.0 WHERE price_per_m2 IS NULL OR price_per_m2 = 0.0")
        except Exception:
            pass

        try:
            async with db.execute("PRAGMA table_info(kavralan_sales)") as cur:
                cols = [row[1] for row in await cur.fetchall()]
                if "model" not in cols:
                    await db.execute("ALTER TABLE kavralan_sales ADD COLUMN model TEXT DEFAULT ''")
                if "color" not in cols:
                    await db.execute("ALTER TABLE kavralan_sales ADD COLUMN color TEXT DEFAULT ''")
            await db.execute("""
                UPDATE kavralan_sales
                SET model = (SELECT model FROM kavralan_rolls WHERE kavralan_rolls.id = kavralan_sales.roll_id),
                    color = (SELECT color FROM kavralan_rolls WHERE kavralan_rolls.id = kavralan_sales.roll_id)
                WHERE (model = '' OR model IS NULL) AND EXISTS (SELECT 1 FROM kavralan_rolls WHERE kavralan_rolls.id = kavralan_sales.roll_id)
            """)
        except Exception:
            pass

        try:
            async with db.execute("PRAGMA table_info(cashbox)") as cur:
                cols = [row[1] for row in await cur.fetchall()]
                if "category" not in cols:
                    await db.execute("ALTER TABLE cashbox ADD COLUMN category TEXT NOT NULL DEFAULT 'carpet'")
        except Exception:
            pass

        try:
            async with db.execute("PRAGMA table_info(rolls)") as cur:
                cols = [row[1] for row in await cur.fetchall()]
                if "price_per_m2" not in cols:
                    await db.execute("ALTER TABLE rolls ADD COLUMN price_per_m2 REAL NOT NULL DEFAULT 8.0")
                if "cost_price_per_m2" not in cols:
                    await db.execute("ALTER TABLE rolls ADD COLUMN cost_price_per_m2 REAL DEFAULT 0.0")
                    await db.execute("UPDATE rolls SET cost_price_per_m2 = price_per_m2 WHERE cost_price_per_m2 IS NULL OR cost_price_per_m2 = 0.0")
        except Exception:
            pass

        # Tarixiy sotuvlar uchun tannarx va foydani to'ldirish (agar 0 bo'lsa)
        try:
            await db.execute("""
                UPDATE sales
                SET cost_price = ROUND(area_m2 * (
                    SELECT COALESCE(rolls.price_per_m2, 8.0) FROM rolls WHERE rolls.id = sales.roll_id
                ), 2)
                WHERE cost_price IS NULL OR cost_price = 0.0
            """)
            await db.execute("""
                UPDATE sales
                SET profit = ROUND(total_price - cost_price, 2)
                WHERE profit IS NULL OR profit = 0.0
            """)
            await db.execute("""
                UPDATE leather_sales
                SET cost_price = ROUND(quantity * 50.0, 2)
                WHERE cost_price IS NULL OR cost_price = 0.0
            """)
            await db.execute("""
                UPDATE leather_sales
                SET profit = ROUND(total_price - cost_price, 2)
                WHERE profit IS NULL OR profit = 0.0
            """)
            await db.execute("""
                UPDATE kavralan_sales
                SET cost_price = ROUND(area_m2 * 30.0, 2)
                WHERE cost_price IS NULL OR cost_price = 0.0
            """)
            await db.execute("""
                UPDATE kavralan_sales
                SET profit = ROUND(total_price - cost_price, 2)
                WHERE profit IS NULL OR profit = 0.0
            """)
        except Exception:
            pass

        # 13. Kartal hisoboti uchun alohida ma'lumotlar ombori
        await db.execute("""
            CREATE TABLE IF NOT EXISTS kartal_cashbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL DEFAULT 2,
                operation_type TEXT NOT NULL, -- 'INCOME' / 'EXPENSE'
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active', -- 'active' / 'deleted'
                created_at TEXT NOT NULL,
                updated_at TEXT,
                deleted_at TEXT
            )
        """)

        # Boshlang'ich amallarni to'ldirish (agar bo'sh bo'lsa)
        async with db.execute("SELECT COUNT(*) FROM kartal_cashbox") as cur:
            row = await cur.fetchone()
            if row and row[0] == 0:
                demo_ops = [
                    (2, 'INCOME', 'Tushum', 350.0, 'Gilam savdosidan kirim\nKassa naqd to\'lovi', '2026-10-19 18:42:00'),
                    (2, 'EXPENSE', 'Logistika', 45.0, 'Transport va yetkazib berish xarajati\nDostavka xizmati', '2026-10-19 17:15:00'),
                    (2, 'INCOME', 'Boshqa', 1200.0, 'Bosh kassadan to\'ldirish\nFilial aylanma mablag\'i', '2026-10-19 15:30:00'),
                    (2, 'EXPENSE', "Do'kon rasxod", 120.0, 'Do\'kon xo\'jalik xarajatlari\nKommunal va tozalash', '2026-10-18 19:10:00'),
                    (2, 'INCOME', 'Tushum', 500.0, 'Nasiya (qarz) to\'lovi qabul qilindi\nQarz qaytarilishi', '2026-10-18 14:05:00')
                ]
                for dop in demo_ops:
                    await db.execute("""
                        INSERT INTO kartal_cashbox (branch_id, operation_type, category, amount, note, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                    """, (dop[0], dop[1], dop[2], dop[3], dop[4], dop[5], dop[5]))
            
        
        # 14. Eslatmalar (Bloknot - iPhone Notes uslubida)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL DEFAULT 1,
                user_id INTEGER,
                author_name TEXT,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                is_pinned INTEGER NOT NULL DEFAULT 0,
                color TEXT DEFAULT 'yellow',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        await db.commit()

# ==================== KARTAL HISOBOTI (ALOHIDA MA'LUMOTLAR OMBORI) ====================

VALID_KARTAL_INCOME_CATS = ["Tushum", "Boshqa"]
VALID_KARTAL_EXPENSE_CATS = [
    "Obed",
    "Do'kon rasxod",
    "Benzin",
    "Logistika",
    "Lichniy",
    "Shivir",
    "Gruzchik",
    "Moshina usta",
    "Oylik",
    "Arenda"
]

async def add_kartal_transaction(
    operation_type: str,
    category: str,
    amount: float,
    note: str = "",
    branch_id: int = 2
) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    amount = round(float(amount), 2)
    operation_type = operation_type.upper().strip()
    category = category.strip()
    note = note.strip()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            INSERT INTO kartal_cashbox (branch_id, operation_type, category, amount, note, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
        """, (branch_id, operation_type, category, amount, note, created_at, created_at)) as cursor:
            new_id = cursor.lastrowid
        await db.commit()
    
    return {
        "id": new_id,
        "branch_id": branch_id,
        "operation_type": operation_type,
        "category": category,
        "amount": amount,
        "note": note,
        "status": "active",
        "created_at": created_at
    }

async def update_kartal_transaction(
    trans_id: int,
    category: str,
    amount: float,
    note: str = ""
) -> bool:
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    amount = round(float(amount), 2)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE kartal_cashbox 
            SET category = ?, amount = ?, note = ?, updated_at = ?
            WHERE id = ?
        """, (category.strip(), amount, note.strip(), updated_at, trans_id))
        await db.commit()
    return True

async def delete_kartal_transaction(trans_id: int) -> bool:
    deleted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE kartal_cashbox 
            SET status = 'deleted', deleted_at = ?
            WHERE id = ?
        """, (deleted_at, trans_id))
        await db.commit()
    return True

async def get_kartal_transactions(branch_id: int = 2, status: str = "active", month: str | None = None, limit: int = 500) -> list[dict]:
    if not month:
        month = datetime.now().strftime("%Y-%m")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if month == 'all':
            query = "SELECT * FROM kartal_cashbox WHERE branch_id = ? AND status = ? ORDER BY id DESC LIMIT ?"
            params = (branch_id, status, limit)
        else:
            query = "SELECT * FROM kartal_cashbox WHERE branch_id = ? AND status = ? AND strftime('%Y-%m', created_at) = ? ORDER BY id DESC LIMIT ?"
            params = (branch_id, status, month, limit)
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_kartal_lichniy_transactions(branch_id: int = 2, status: str = "active") -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM kartal_cashbox 
            WHERE branch_id = ? AND category = 'Lichniy' AND status = ?
            ORDER BY id DESC
        """, (branch_id, status)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_kartal_summary(branch_id: int = 2, month: str | None = None) -> dict:
    if not month:
        month = datetime.now().strftime("%Y-%m")
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Doimiy o'zgarmas kassa qoldig'i (Umuman davriy emas, barcha faol amallar)
        async with db.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN operation_type = 'INCOME' AND status = 'active' THEN amount ELSE 0 END), 0.0),
                COALESCE(SUM(CASE WHEN operation_type = 'EXPENSE' AND status = 'active' THEN amount ELSE 0 END), 0.0)
            FROM kartal_cashbox
            WHERE branch_id = ?
        """, (branch_id,)) as cursor:
            row = await cursor.fetchone()
            all_time_income = round(row[0] or 0.0, 2)
            all_time_expense = round(row[1] or 0.0, 2)
            all_time_balance = round(all_time_income - all_time_expense, 2)

        # 2. Bir oylik davr bo'yicha kirim va chiqim (01.MM dan 31.MM gacha)
        async with db.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN operation_type = 'INCOME' AND status = 'active' THEN amount ELSE 0 END), 0.0),
                COALESCE(SUM(CASE WHEN operation_type = 'EXPENSE' AND status = 'active' THEN amount ELSE 0 END), 0.0)
            FROM kartal_cashbox
            WHERE branch_id = ? AND strftime('%Y-%m', created_at) = ?
        """, (branch_id, month)) as cursor:
            row_m = await cursor.fetchone()
            month_income = round(row_m[0] or 0.0, 2)
            month_expense = round(row_m[1] or 0.0, 2)

        return {
            "balance": all_time_balance,
            "total_income": all_time_income,
            "total_expense": all_time_expense,
            "month": month,
            "month_income": month_income,
            "month_expense": month_expense
        }

# --- KASSA FUNKSIYALARI (ALOHIDA KATEGORIYALAR) ---

async def get_cash_balance(branch_id: int | None = None, category: str = "carpet") -> float:
    async with aiosqlite.connect(DB_PATH) as db:
        if branch_id is not None:
            async with db.execute(
                "SELECT balance_after FROM cashbox WHERE branch_id = ? AND category = ? ORDER BY id DESC LIMIT 1", 
                (branch_id, category)
            ) as cursor:
                row = await cursor.fetchone()
                return round(row[0], 2) if row else 0.0
        else:
            # Barcha filiallar bo'yicha shu toifaning umumiy qoldig'i
            total = 0.0
            for b_id in BRANCH_NAMES.keys():
                async with db.execute(
                    "SELECT balance_after FROM cashbox WHERE branch_id = ? AND category = ? ORDER BY id DESC LIMIT 1", 
                    (b_id, category)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        total += row[0]
            return round(total, 2)

async def withdraw_cash(amount: float, branch_id: int = 1, category: str = "carpet", note: str = "Kassa topshirildi") -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_balance = await get_cash_balance(branch_id=branch_id, category=category)
    
    if amount <= 0:
        raise ValueError("Chiqim summasi 0 dan katta bo'lishi kerak!")
    if amount > current_balance:
        cat_name = "Gilam" if category == "carpet" else ("Teri" if category == "leather" else ("Kavralan" if category == "kavralan" else "3-Filial"))
        raise ValueError(f"{cat_name} kassasida yetarli mablag' yo'q! Mavjud: ${current_balance:.2f}")
        
    new_balance = round(current_balance - amount, 2)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
            VALUES (?, ?, 'WITHDRAWAL', ?, ?, ?, ?)
        """, (branch_id, category, amount, note, new_balance, created_at))
        await db.commit()
        
    return {
        "amount": amount,
        "branch_id": branch_id,
        "category": category,
        "old_balance": current_balance,
        "new_balance": new_balance,
        "note": note,
        "created_at": created_at
    }

async def add_expense(amount: float, branch_id: int = 1, category: str = "carpet", expense_title: str = "Xarajat", note: str = "") -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_balance = await get_cash_balance(branch_id=branch_id, category=category)
    if amount <= 0:
        raise ValueError("Xarajat summasi 0 dan katta bo'lishi kerak!")
    if amount > current_balance:
        raise ValueError(f"Kassada yetarli mablag' yo'q! Mavjud: ${current_balance:.2f}")
    new_balance = round(current_balance - amount, 2)
    full_note = f"Rasxod [{expense_title}]: {note}".strip(": ")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
            VALUES (?, ?, 'EXPENSE', ?, ?, ?, ?)
        """, (branch_id, category, amount, full_note, new_balance, created_at))
        await db.commit()
    return {
        "amount": amount,
        "expense_title": expense_title,
        "category": category,
        "new_balance": new_balance,
        "note": full_note,
        "created_at": created_at
    }

async def get_expenses(branch_id: int = 1, limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM cashbox 
            WHERE branch_id = ? AND operation_type = 'EXPENSE'
            ORDER BY id DESC LIMIT ?
        """, (branch_id, limit)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

async def create_transfer_request(
    roll_id: int, 
    from_branch: int, 
    to_branch: int, 
    transfer_length: float | None = None, 
    note: str = ""
) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM rolls WHERE id = ? AND branch_id = ? AND status = 'active'", (roll_id, from_branch)) as cur:
            roll = await cur.fetchone()
            if not roll:
                raise ValueError("Rulon topilmadi yoki ushbu filialga tegishli emas!")
                
        curr_len = float(roll["current_length"])
        # Mavjud kutilayotgan (pending) transferlarni tekshirish
        async with db.execute("SELECT COALESCE(SUM(length), 0.0) FROM transfers WHERE roll_id = ? AND status = 'pending'", (roll_id,)) as cur_p:
            p_row = await cur_p.fetchone()
            already_pending = float(p_row[0] or 0.0)
            
        avail_to_transfer = round(curr_len - already_pending, 2)
        if avail_to_transfer <= 0:
            raise ValueError("Ushbu rulon to'liq boshqa filialga transfer qilinishi kutilmoqda!")
            
        if transfer_length is None or float(transfer_length) <= 0:
            transfer_length = avail_to_transfer
        else:
            transfer_length = round(float(transfer_length), 2)
            
        if transfer_length > avail_to_transfer:
            raise ValueError(f"O'tkaziladigan miqdor mavjud qoldiqdan ({avail_to_transfer} m) ko'p bo'lishi mumkin emas!")

        # DIQQAT: rolls jadvali o'zgarmaydi! Tovar qabul qilinguncha jo'natuvchi filial balansida turadi.
        cur_ins = await db.execute("""
            INSERT INTO transfers (roll_id, roll_code, from_branch, to_branch, width, color, length, note, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (roll_id, roll["roll_code"], from_branch, to_branch, roll["width"], roll["color"], transfer_length, note, created_at))
        transfer_id = cur_ins.lastrowid
        await db.commit()
        
        return {
            "transfer_id": transfer_id,
            "roll_id": roll_id,
            "roll_code": roll["roll_code"],
            "from_branch": from_branch,
            "to_branch": to_branch,
            "width": roll["width"],
            "color": roll["color"],
            "length": transfer_length,
            "current_length": transfer_length,
            "note": note,
            "status": "pending",
            "created_at": created_at
        }

async def transfer_roll(roll_id: int, from_branch: int, to_branch: int, transfer_length: float | None = None, note: str = "") -> dict:
    """Moslik uchun wrapper: transfer so'rovini yaratadi (avtomatik qabul qilinmaydi)"""
    return await create_transfer_request(roll_id, from_branch, to_branch, transfer_length, note)

async def accept_transfer(transfer_id: int, accepted_by: str = "") -> dict:
    """Qabul qiluvchi filial xodimi tomonidan transferni tasdiqlash va omborga qabul qilish"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM transfers WHERE id = ?", (transfer_id,)) as cur:
            tr = await cur.fetchone()
            if not tr:
                raise ValueError("Transfer topilmadi!")
            if tr["status"] != "pending":
                raise ValueError(f"Ushbu transfer allaqachon '{tr['status']}' holatida!")
                
        roll_id = tr["roll_id"]
        from_branch = tr["from_branch"]
        to_branch = tr["to_branch"]
        transfer_len = float(tr["length"])
        
        async with db.execute("SELECT * FROM rolls WHERE id = ? AND branch_id = ?", (roll_id, from_branch)) as cur_r:
            roll = await cur_r.fetchone()
            if not roll:
                raise ValueError("Jo'natuvchi filialdagi asl rulon topilmadi!")
                
        curr_len = float(roll["current_length"])
        if transfer_len > curr_len:
            raise ValueError(f"Jo'natuvchi filialdagi rulonda yetarli metr qolmagan (mavjud: {curr_len} m)!")
            
        if transfer_len >= curr_len:
            # Butun rulon to'liq qabul qiluvchi filialga o'tadi
            await db.execute("UPDATE rolls SET branch_id = ? WHERE id = ?", (to_branch, roll_id))
            target_roll_id = roll_id
            target_roll_code = roll["roll_code"]
        else:
            # Qisman transfer: Jo'natuvchidagi rulon metrajini kamaytirish
            new_source_len = round(curr_len - transfer_len, 2)
            new_source_area = round(float(roll["width"]) * new_source_len, 2)
            new_source_total = round(new_source_area * float(roll["price_per_m2"]), 2)
            await db.execute("""
                UPDATE rolls
                SET current_length = ?, area_m2 = ?, total_price = ?
                WHERE id = ?
            """, (new_source_len, new_source_area, new_source_total, roll_id))
            
            # Qabul qiluvchida yangi rulon ochish
            async with db.execute("SELECT MAX(id) FROM rolls") as cursor:
                row = await cursor.fetchone()
                next_id = (row[0] or 0) + 1
                target_roll_code = f"#F{to_branch}-{1000 + next_id}"
                
            target_area = round(float(roll["width"]) * transfer_len, 2)
            target_total = round(target_area * float(roll["price_per_m2"]), 2)
            cost_pr = roll["cost_price_per_m2"] if ("cost_price_per_m2" in roll.keys() and roll["cost_price_per_m2"]) else roll["price_per_m2"]
            
            cur_ins = await db.execute("""
                INSERT INTO rolls (branch_id, roll_code, width, color, initial_length, current_length, area_m2, price_per_m2, cost_price_per_m2, total_price, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
            """, (to_branch, target_roll_code, roll["width"], roll["color"], transfer_len, transfer_len, target_area, roll["price_per_m2"], cost_pr, target_total, now_str))
            target_roll_id = cur_ins.lastrowid
            
        await db.execute("""
            UPDATE transfers
            SET status = 'accepted', target_roll_id = ?, target_roll_code = ?, accepted_at = ?, accepted_by = ?
            WHERE id = ?
        """, (target_roll_id, target_roll_code, now_str, accepted_by, transfer_id))
        await db.commit()
        
        return {
            "transfer_id": transfer_id,
            "target_roll_id": target_roll_id,
            "target_roll_code": target_roll_code,
            "from_branch": from_branch,
            "to_branch": to_branch,
            "width": tr["width"],
            "color": tr["color"],
            "length": transfer_len,
            "accepted_at": now_str,
            "accepted_by": accepted_by,
            "status": "accepted"
        }

async def reject_transfer(transfer_id: int, rejected_by: str = "", reason: str = "") -> dict:
    """Qabul qiluvchi filial xodimi tomonidan transferni rad etish"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM transfers WHERE id = ?", (transfer_id,)) as cur:
            tr = await cur.fetchone()
            if not tr:
                raise ValueError("Transfer topilmadi!")
            if tr["status"] != "pending":
                raise ValueError(f"Ushbu transfer allaqachon '{tr['status']}' holatida!")
                
        note_append = f" [Rad etildi: {reason}]" if reason else " [Rad etildi]"
        await db.execute("""
            UPDATE transfers
            SET status = 'rejected', rejected_at = ?, rejected_by = ?, note = COALESCE(note, '') || ?
            WHERE id = ?
        """, (now_str, rejected_by, note_append, transfer_id))
        await db.commit()
        return dict(tr)

async def cancel_transfer(transfer_id: int, user_branch: int = None, is_superadmin: bool = False) -> dict:
    """Transferni jo'natgan filial tomonidan bekor qilish"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM transfers WHERE id = ?", (transfer_id,)) as cur:
            tr = await cur.fetchone()
            if not tr:
                raise ValueError("Transfer topilmadi!")
            if tr["status"] != "pending":
                raise ValueError(f"Ushbu transfer allaqachon '{tr['status']}' holatida!")
            if not is_superadmin and user_branch is not None and tr["from_branch"] != user_branch:
                raise ValueError("Faqat transferni jo'natgan filial uni bekor qilishi mumkin!")
                
        await db.execute("""
            UPDATE transfers
            SET status = 'cancelled', rejected_at = ?, rejected_by = 'Jo''natuvchi tomonidan bekor qilindi'
            WHERE id = ?
        """, (now_str, transfer_id))
        await db.commit()
        return dict(tr)

async def get_pending_transfers(branch_id: int | None = None, as_recipient: bool = True) -> list[dict]:
    """Kutilayotgan (pending) transferlar ro'yxati"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if branch_id is not None:
            if as_recipient:
                query = "SELECT * FROM transfers WHERE to_branch = ? AND status = 'pending' ORDER BY id DESC"
                params = (branch_id,)
            else:
                query = "SELECT * FROM transfers WHERE from_branch = ? AND status = 'pending' ORDER BY id DESC"
                params = (branch_id,)
        else:
            query = "SELECT * FROM transfers WHERE status = 'pending' ORDER BY id DESC"
            params = ()
        async with db.execute(query, params) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

async def get_transfers_history(branch_id: int = None, limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if branch_id:
            query = "SELECT * FROM transfers WHERE from_branch = ? OR to_branch = ? ORDER BY id DESC LIMIT ?"
            params = (branch_id, branch_id, limit)
        else:
            query = "SELECT * FROM transfers ORDER BY id DESC LIMIT ?"
            params = (limit,)
        async with db.execute(query, params) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

async def update_roll(roll_id: int, width: float, color: str, current_length: float, price_per_m2: float, cost_price_per_m2: float | None = None) -> dict:
    area_m2 = round(width * current_length, 2)
    total_price = round(area_m2 * price_per_m2, 2)
    async with aiosqlite.connect(DB_PATH) as db:
        if cost_price_per_m2 is not None and float(cost_price_per_m2) > 0:
            await db.execute("""
                UPDATE rolls
                SET width = ?, color = ?, current_length = ?, area_m2 = ?, price_per_m2 = ?, cost_price_per_m2 = ?, total_price = ?
                WHERE id = ?
            """, (width, color, current_length, area_m2, price_per_m2, float(cost_price_per_m2), total_price, roll_id))
        else:
            await db.execute("""
                UPDATE rolls
                SET width = ?, color = ?, current_length = ?, area_m2 = ?, price_per_m2 = ?, total_price = ?
                WHERE id = ?
            """, (width, color, current_length, area_m2, price_per_m2, total_price, roll_id))
        await db.commit()
    return {"success": True, "roll_id": roll_id, "width": width, "color": color, "current_length": current_length, "area_m2": area_m2, "price_per_m2": price_per_m2, "total_price": total_price}

async def delete_roll(roll_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE rolls SET status = 'deleted' WHERE id = ?", (roll_id,))
        await db.commit()
    return True

async def update_leather_item(branch_id: int, color: str, quantity: int, price_per_item: float) -> dict:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO leather_inventory (branch_id, color, quantity, price_per_item, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(branch_id, color) DO UPDATE SET
                quantity = excluded.quantity,
                price_per_item = excluded.price_per_item,
                updated_at = excluded.updated_at
        """, (branch_id, color, quantity, price_per_item, now_str))
        await db.commit()
    return {"success": True, "branch_id": branch_id, "color": color, "quantity": quantity, "price_per_item": price_per_item}

async def update_kavralan_roll(roll_id: int, current_length: float, price_per_m2: float, cost_price_per_m2: float | None = None, width: float = 4.0, model: str = "", color: str = "") -> dict:
    area_m2 = round(width * current_length, 2)
    total_price = round(area_m2 * price_per_m2, 2)
    async with aiosqlite.connect(DB_PATH) as db:
        if cost_price_per_m2 is not None and float(cost_price_per_m2) > 0:
            cost_pr = float(cost_price_per_m2)
            await db.execute("""
                UPDATE kavralan_rolls
                SET width = ?, model = ?, color = ?, current_length = ?, area_m2 = ?, price_per_m2 = ?, cost_price_per_m2 = ?, total_price = ?
                WHERE id = ?
            """, (width, model, color, current_length, area_m2, price_per_m2, cost_pr, total_price, roll_id))
        else:
            await db.execute("""
                UPDATE kavralan_rolls
                SET width = ?, model = ?, color = ?, current_length = ?, area_m2 = ?, price_per_m2 = ?, total_price = ?
                WHERE id = ?
            """, (width, model, color, current_length, area_m2, price_per_m2, total_price, roll_id))
        await db.commit()
    return {"success": True, "roll_id": roll_id, "width": width, "model": model, "color": color, "current_length": current_length, "area_m2": area_m2, "price_per_m2": price_per_m2, "cost_price_per_m2": cost_price_per_m2, "total_price": total_price}

async def delete_kavralan_roll(roll_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE kavralan_rolls SET status = 'deleted' WHERE id = ?", (roll_id,))
        await db.commit()
    return True


# --- GILAM FUNKSIYALARI ---

async def add_roll(
    width: float, 
    color: str, 
    length: float, 
    branch_id: int = 1, 
    price_per_m2: float = PRICE_PER_M2,
    cost_price_per_m2: float | None = None
) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    area_m2 = round(width * length, 2)
    total_price = round(area_m2 * price_per_m2, 2)
    
    if cost_price_per_m2 is None or float(cost_price_per_m2) <= 0:
        cost_price_per_m2 = price_per_m2
    else:
        cost_price_per_m2 = float(cost_price_per_m2)
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT MAX(id) FROM rolls") as cursor:
            row = await cursor.fetchone()
            next_id = (row[0] or 0) + 1
            roll_code = f"#F{branch_id}-{1000 + next_id}"
        
        await db.execute("""
            INSERT INTO rolls (branch_id, roll_code, width, color, initial_length, current_length, area_m2, price_per_m2, cost_price_per_m2, total_price, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
        """, (branch_id, roll_code, width, color, length, length, area_m2, price_per_m2, cost_price_per_m2, total_price, created_at))
        await db.commit()
        
        return {
            "id": next_id,
            "branch_id": branch_id,
            "roll_code": roll_code,
            "width": width,
            "color": color,
            "initial_length": length,
            "current_length": length,
            "area_m2": area_m2,
            "price_per_m2": price_per_m2,
            "cost_price_per_m2": cost_price_per_m2,
            "total_price": total_price,
            "created_at": created_at
        }

async def get_available_widths(branch_id: int = 1) -> list[float]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT DISTINCT width FROM rolls 
            WHERE branch_id = ? AND current_length > 0 AND status = 'active' 
            ORDER BY width ASC
        """, (branch_id,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_available_colors(width: float, branch_id: int = 1) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT DISTINCT color FROM rolls 
            WHERE branch_id = ? AND width = ? AND current_length > 0 AND status = 'active' 
            ORDER BY color ASC
        """, (branch_id, width)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_available_rolls(width: float, color: str, branch_id: int = 1) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM rolls 
            WHERE branch_id = ? AND width = ? AND color = ? AND current_length > 0 AND status = 'active'
            ORDER BY current_length ASC
        """, (branch_id, width, color)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_all_active_rolls(branch_id: int | None = None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if branch_id is not None:
            query = """
                SELECT r.*,
                       COALESCE((SELECT SUM(t.length) FROM transfers t WHERE t.roll_id = r.id AND t.status = 'pending'), 0.0) as pending_length,
                       (SELECT t.to_branch FROM transfers t WHERE t.roll_id = r.id AND t.status = 'pending' ORDER BY t.id DESC LIMIT 1) as pending_to_branch
                FROM rolls r
                WHERE r.branch_id = ? AND r.current_length > 0 AND r.status = 'active'
                ORDER BY r.width ASC, r.current_length DESC
            """
            params = (branch_id,)
        else:
            query = """
                SELECT r.*,
                       COALESCE((SELECT SUM(t.length) FROM transfers t WHERE t.roll_id = r.id AND t.status = 'pending'), 0.0) as pending_length,
                       (SELECT t.to_branch FROM transfers t WHERE t.roll_id = r.id AND t.status = 'pending' ORDER BY t.id DESC LIMIT 1) as pending_to_branch
                FROM rolls r
                WHERE r.current_length > 0 AND r.status = 'active'
                ORDER BY r.branch_id ASC, r.width ASC, r.current_length DESC
            """
            params = ()
            
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_roll_by_id(roll_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM rolls WHERE id = ?", (roll_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def make_sale(
    roll_id: int, 
    sold_length: float, 
    branch_id: int = 1, 
    price_per_m2: float = PRICE_PER_M2,
    custom_total_price: float | None = None,
    is_debt: bool = False,
    customer_name: str = "",
    customer_phone: str = "",
    initial_paid: float = 0.0,
    due_date: str | None = None,
    customer_telegram_id: int | None = None
) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM rolls WHERE id = ? AND branch_id = ?", (roll_id, branch_id)) as cursor:
            roll = await cursor.fetchone()
            if not roll:
                raise ValueError("Rulon topilmadi yoki boshqa filialga tegishli!")
            
            # Kutilayotgan transfer tekshiruvi
            async with db.execute("SELECT COALESCE(SUM(length), 0.0) FROM transfers WHERE roll_id = ? AND status = 'pending'", (roll_id,)) as cur_p:
                p_row = await cur_p.fetchone()
                pending_len = float(p_row[0] or 0.0)
                
            avail_len = round(roll["current_length"] - pending_len, 2)
            if sold_length > avail_len:
                if pending_len > 0:
                    raise ValueError(f"Rulondan {pending_len} m boshqa filialga transfer kutilmoqda! Sotish uchun mavjud: {avail_len} m")
                else:
                    raise ValueError(f"Rulonda yetarli uzunlik yo'q! Mavjud qoldiq: {roll['current_length']} m")
        
        roll_price_per_m2 = float(roll["price_per_m2"]) if ("price_per_m2" in roll.keys() and roll["price_per_m2"]) else 8.0
        roll_cost_price = float(roll["cost_price_per_m2"]) if ("cost_price_per_m2" in roll.keys() and roll["cost_price_per_m2"] and float(roll["cost_price_per_m2"]) > 0) else roll_price_per_m2
        new_length = round(roll["current_length"] - sold_length, 2)
        new_area = round(roll["width"] * new_length, 2)
        new_total_price = round(new_area * roll_price_per_m2, 2)
        new_status = "finished" if new_length <= 0 else "active"
        
        await db.execute("""
            UPDATE rolls 
            SET current_length = ?, area_m2 = ?, total_price = ?, status = ?
            WHERE id = ?
        """, (new_length, new_area, new_total_price, new_status, roll_id))
        
        sold_area = round(roll["width"] * sold_length, 2)
        
        # Agar foydalanuvchi umumiy summa kiritgan bo'lsa
        if custom_total_price is not None and float(custom_total_price) > 0:
            sale_total_price = round(float(custom_total_price), 2)
            actual_price_per_m2 = round(sale_total_price / sold_area, 2) if sold_area > 0 else price_per_m2
        else:
            actual_price_per_m2 = price_per_m2
            sale_total_price = round(sold_area * actual_price_per_m2, 2)
            
        cost_price = round(sold_area * roll_cost_price, 2)
        profit = round(sale_total_price - cost_price, 2)
        
        async with db.execute("""
            INSERT INTO sales (branch_id, roll_id, roll_code, width, color, sold_length, area_m2, price_per_m2, total_price, cost_price, profit, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (branch_id, roll_id, roll["roll_code"], roll["width"], roll["color"], sold_length, sold_area, actual_price_per_m2, sale_total_price, cost_price, profit, created_at)) as cursor:
            sale_id = cursor.lastrowid
        
        debt_id = None
        if is_debt:
            initial_paid = round(float(initial_paid), 2)
            remaining_amount = round(sale_total_price - initial_paid, 2)
            debt_status = "partial" if initial_paid > 0 else "unpaid"
            
            item_desc = f"Rezinka Gilam {roll['roll_code']} ({roll['width']:g}x{sold_length}m = {sold_area} m², {roll['color']})"
            async with db.execute("""
                INSERT INTO debts (branch_id, category, customer_name, customer_phone, item_details, total_amount, initial_paid, paid_amount, remaining_amount, status, due_date, customer_telegram_id, created_at, updated_at)
                VALUES (?, 'carpet', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (branch_id, customer_name, customer_phone, item_desc, sale_total_price, initial_paid, initial_paid, remaining_amount, debt_status, due_date, customer_telegram_id, created_at, created_at)) as cursor:
                debt_id = cursor.lastrowid
                
            current_balance = await get_cash_balance(branch_id=branch_id, category="carpet")
            if initial_paid > 0:
                new_balance = round(current_balance + initial_paid, 2)
                await db.execute("""
                    INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
                    VALUES (?, 'carpet', 'INCOME', ?, ?, ?, ?)
                """, (branch_id, initial_paid, f"Nasiya boshlang'ich to'lov (Gilam): {customer_name} (#{debt_id})", new_balance, created_at))
                
                await db.execute("""
                    INSERT INTO debt_payments (debt_id, branch_id, category, amount, note, created_at)
                    VALUES (?, ?, 'carpet', ?, ?, ?)
                """, (debt_id, branch_id, initial_paid, "Boshlang'ich to'lov", created_at))
            else:
                new_balance = current_balance
        else:
            # Gilam kassasiga tushum
            current_balance = await get_cash_balance(branch_id=branch_id, category="carpet")
            new_balance = round(current_balance + sale_total_price, 2)
            await db.execute("""
                INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
                VALUES (?, 'carpet', 'INCOME', ?, ?, ?, ?)
            """, (branch_id, sale_total_price, f"Sotuv (Gilam): {roll['roll_code']} ({roll['width']:g}x{sold_length}m - {roll['color']})", new_balance, created_at))
        
        await db.commit()
        
        return {
            "sale_id": sale_id,
            "debt_id": debt_id,
            "branch_id": branch_id,
            "roll_code": roll["roll_code"],
            "width": roll["width"],
            "color": roll["color"],
            "sold_length": sold_length,
            "sold_area": sold_area,
            "price_per_m2": actual_price_per_m2,
            "sale_total_price": sale_total_price,
            "cost_price": cost_price,
            "profit": profit,
            "remaining_length": new_length,
            "is_debt": is_debt,
            "initial_paid": initial_paid if is_debt else sale_total_price,
            "remaining_debt": remaining_amount if is_debt else 0.0,
            "customer_name": customer_name,
            "created_at": created_at,
            "new_cash_balance": new_balance
        }

async def make_batch_sale(
    items: list[dict],
    branch_id: int = 1,
    is_debt: bool = False,
    customer_name: str = "",
    customer_phone: str = "",
    initial_paid: float = 0.0,
    due_date: str | None = None,
    customer_telegram_id: int | None = None
) -> dict:
    if not items or len(items) == 0:
        raise ValueError("Chekda kamida bitta mahsulot bo'lishi kerak!")
        
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        batch_total = 0.0
        batch_cost = 0.0
        batch_profit = 0.0
        item_descriptions = []
        sale_records = []
        # Har bir toifa o'z kassasiga: gilam / teri / kavralan pullari aralashmasligi uchun alohida yig'amiz
        cat_totals = {"carpet": 0.0, "leather": 0.0, "kavralan": 0.0}
        cat_descriptions = {"carpet": [], "leather": [], "kavralan": []}

        # 1. Oldindan barcha mahsulotlarni tekshirib chiqish
        # Bir xil rulon / rangdan chekda bir nechta qator bo'lsa, umumiy so'ralgan miqdorni yig'ib tekshiramiz
        roll_requested_lens = {}
        leather_requested_qty = {}
        kavralan_requested_lens = {}
        for item in items:
            p_type = item.get("product_type", "carpet")
            if p_type == "carpet":
                r_id = int(item["roll_id"])
                s_len = float(str(item["sold_length"]).replace(",", "."))
                if s_len <= 0:
                    raise ValueError("Sotiladigan uzunlik 0 dan katta bo'lishi kerak!")
                roll_requested_lens[r_id] = roll_requested_lens.get(r_id, 0.0) + s_len
            elif p_type == "leather":
                color = str(item.get("color", "")).strip()
                qty = int(item.get("quantity", 0))
                if qty <= 0:
                    raise ValueError("Teri soni 0 dan katta bo'lishi kerak!")
                leather_requested_qty[color] = leather_requested_qty.get(color, 0) + qty
            elif p_type == "kavralan":
                r_id = int(item["roll_id"])
                s_len = float(str(item["sold_length"]).replace(",", "."))
                if s_len <= 0:
                    raise ValueError("Kavralan uzunligi 0 dan katta bo'lishi kerak!")
                kavralan_requested_lens[r_id] = kavralan_requested_lens.get(r_id, 0.0) + s_len
            else:
                raise ValueError(f"Noma'lum mahsulot turi: {p_type}")

        # Teri qoldiqlarini rang bo'yicha chekdagi jami miqdor bilan tekshirish
        for color, total_qty in leather_requested_qty.items():
            async with db.execute("SELECT quantity FROM leather_inventory WHERE branch_id = ? AND color = ?", (branch_id, color)) as cur:
                row = await cur.fetchone()
                curr_qty = row[0] if row else 0
            if total_qty > curr_qty:
                raise ValueError(f"Omborda yetarli teri yo'q! ({color}: mavjud {curr_qty} dona, chekda jami so'ralgan: {total_qty} dona)")

        # Kavralan rulonlarini chekdagi jami uzunlik bilan tekshirish
        for r_id, total_req_len in kavralan_requested_lens.items():
            async with db.execute("SELECT * FROM kavralan_rolls WHERE id = ? AND branch_id = ?", (r_id, branch_id)) as cur:
                k_roll = await cur.fetchone()
            if not k_roll:
                raise ValueError(f"Kavralan ruloni (ID: {r_id}) topilmadi yoki boshqa filialga tegishli!")
            if round(total_req_len, 2) > round(float(k_roll["current_length"]), 2):
                raise ValueError(f"Kavralan rulonida ({k_roll['roll_code']}) yetarli uzunlik yo'q! Mavjud: {k_roll['current_length']}m, chekda jami so'ralgan: {round(total_req_len, 2)}m")

        # Gilam rulonlari bo'yicha qoldiqlarni tekshirish
        for r_id, total_req_len in roll_requested_lens.items():
            async with db.execute("SELECT * FROM rolls WHERE id = ? AND branch_id = ?", (r_id, branch_id)) as cur:
                roll = await cur.fetchone()
                if not roll:
                    raise ValueError(f"Rulon (ID: {r_id}) topilmadi yoki boshqa filialga tegishli!")
            async with db.execute("SELECT COALESCE(SUM(length), 0.0) FROM transfers WHERE roll_id = ? AND status = 'pending'", (r_id,)) as cur_p:
                p_row = await cur_p.fetchone()
                pending_len = float(p_row[0] or 0.0)
            avail_len = round(roll["current_length"] - pending_len, 2)
            if round(total_req_len, 2) > avail_len:
                raise ValueError(f"Rulonda ({roll['roll_code']} {roll['width']}x {roll['color']}) yetarli uzunlik yo'q! Mavjud: {avail_len}m, chekda jami so'ralgan: {total_req_len}m")

        # 2. Barcha mahsulotlarni sotuvga chiqarish
        for item in items:
            p_type = item.get("product_type", "carpet")
            if p_type == "carpet":
                roll_id = int(item["roll_id"])
                sold_length = float(str(item["sold_length"]).replace(",", "."))
                raw_price = item.get("price_per_m2", 8.0)
                price_per_m2 = float(str(raw_price).replace(",", ".")) if raw_price else 8.0
                raw_custom = item.get("total_price") or item.get("custom_total_price")
                custom_total = float(str(raw_custom).replace(",", ".")) if raw_custom and float(str(raw_custom).replace(",", ".")) > 0 else None
                
                async with db.execute("SELECT * FROM rolls WHERE id = ?", (roll_id,)) as cur:
                    roll = await cur.fetchone()
                    
                roll_price_per_m2 = float(roll["price_per_m2"]) if ("price_per_m2" in roll.keys() and roll["price_per_m2"]) else 8.0
                roll_cost_price = float(roll["cost_price_per_m2"]) if ("cost_price_per_m2" in roll.keys() and roll["cost_price_per_m2"] and float(roll["cost_price_per_m2"]) > 0) else roll_price_per_m2
                
                new_length = round(roll["current_length"] - sold_length, 2)
                new_area = round(roll["width"] * new_length, 2)
                new_total_price = round(new_area * roll_price_per_m2, 2)
                new_status = "finished" if new_length <= 0 else "active"
                
                await db.execute("""
                    UPDATE rolls 
                    SET current_length = ?, area_m2 = ?, total_price = ?, status = ?
                    WHERE id = ?
                """, (new_length, new_area, new_total_price, new_status, roll_id))
                
                sold_area = round(roll["width"] * sold_length, 2)
                if custom_total is not None and custom_total > 0:
                    sale_total_price = round(custom_total, 2)
                    actual_price_per_m2 = round(sale_total_price / sold_area, 2) if sold_area > 0 else price_per_m2
                else:
                    actual_price_per_m2 = price_per_m2
                    sale_total_price = round(sold_area * actual_price_per_m2, 2)
                    
                cost_price = round(sold_area * roll_cost_price, 2)
                profit = round(sale_total_price - cost_price, 2)
                
                async with db.execute("""
                    INSERT INTO sales (branch_id, roll_id, roll_code, width, color, sold_length, area_m2, price_per_m2, total_price, cost_price, profit, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (branch_id, roll_id, roll["roll_code"], roll["width"], roll["color"], sold_length, sold_area, actual_price_per_m2, sale_total_price, cost_price, profit, created_at)) as cur_s:
                    sale_id = cur_s.lastrowid
                    
                batch_total += sale_total_price
                batch_cost += cost_price
                batch_profit += profit
                desc = f"Rezinka Gilam {roll['roll_code']} ({roll['width']:g}x{sold_length}m = {sold_area} m², {roll['color']})"
                item_descriptions.append(desc)
                cat_totals["carpet"] += sale_total_price
                cat_descriptions["carpet"].append(desc)
                sale_records.append({
                    "sale_id": sale_id,
                    "product_type": "carpet",
                    "roll_code": roll["roll_code"],
                    "width": roll["width"],
                    "color": roll["color"],
                    "sold_length": sold_length,
                    "sold_area": sold_area,
                    "sale_total_price": sale_total_price,
                    "profit": profit
                })
            elif p_type == "leather":
                color = str(item.get("color", "")).strip()
                qty = int(item.get("quantity", 0))
                pr_item = float(str(item.get("price_per_item", 50.0)).replace(",", "."))
                raw_custom = item.get("total_price") or item.get("custom_total_price")
                custom_total = float(str(raw_custom).replace(",", ".")) if raw_custom and float(str(raw_custom).replace(",", ".")) > 0 else None
                
                await db.execute("""
                    UPDATE leather_inventory
                    SET quantity = quantity - ?, updated_at = ?
                    WHERE branch_id = ? AND color = ?
                """, (qty, created_at, branch_id, color))
                
                if custom_total is not None and custom_total > 0:
                    item_total = round(custom_total, 2)
                    actual_price_per_item = round(item_total / qty, 2) if qty > 0 else pr_item
                else:
                    actual_price_per_item = pr_item
                    item_total = round(qty * actual_price_per_item, 2)
                    
                item_cost = round(qty * 50.0, 2)
                item_profit = round(item_total - item_cost, 2)
                
                async with db.execute("""
                    INSERT INTO leather_sales (branch_id, color, quantity, price_per_item, total_price, cost_price, profit, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (branch_id, color, qty, actual_price_per_item, item_total, item_cost, item_profit, created_at)) as cur_l:
                    sale_id = cur_l.lastrowid
                    
                batch_total += item_total
                batch_cost += item_cost
                batch_profit += item_profit
                desc = f"{qty} dona {color} teri"
                item_descriptions.append(desc)
                cat_totals["leather"] += item_total
                cat_descriptions["leather"].append(desc)
                sale_records.append({
                    "sale_id": sale_id,
                    "product_type": "leather",
                    "color": color,
                    "quantity": qty,
                    "sale_total_price": item_total,
                    "profit": item_profit
                })
            elif p_type == "kavralan":
                roll_id = int(item["roll_id"])
                sold_len = float(str(item["sold_length"]).replace(",", "."))
                pr_m2 = float(str(item.get("price_per_m2", 30.0)).replace(",", "."))
                raw_custom = item.get("total_price") or item.get("custom_total_price")
                custom_total = float(str(raw_custom).replace(",", ".")) if raw_custom and float(str(raw_custom).replace(",", ".")) > 0 else None
                
                async with db.execute("SELECT * FROM kavralan_rolls WHERE id = ?", (roll_id,)) as cur:
                    k_row = await cur.fetchone()
                    k_roll = dict(k_row) if k_row else {}
                    
                new_len = round(k_roll["current_length"] - sold_len, 2)
                new_area = round(4.0 * new_len, 2)
                new_tot = round(new_area * 30.0, 2)
                new_stat = "finished" if new_len <= 0 else "active"
                
                await db.execute("""
                    UPDATE kavralan_rolls
                    SET current_length = ?, area_m2 = ?, total_price = ?, status = ?
                    WHERE id = ?
                """, (new_len, new_area, new_tot, new_stat, roll_id))
                
                sold_area = round(4.0 * sold_len, 2)
                if custom_total is not None and custom_total > 0:
                    sale_total_price = round(custom_total, 2)
                    actual_price_per_m2 = round(sale_total_price / sold_area, 2) if sold_area > 0 else pr_m2
                else:
                    actual_price_per_m2 = pr_m2
                    sale_total_price = round(sold_area * actual_price_per_m2, 2)
                    
                roll_cost_price = k_roll.get("cost_price_per_m2") if k_roll.get("cost_price_per_m2") is not None and k_roll.get("cost_price_per_m2") > 0 else (k_roll.get("price_per_m2") or 30.0)
                item_cost = round(sold_area * roll_cost_price, 2)
                item_profit = round(sale_total_price - item_cost, 2)
                
                model_val = k_roll.get("model") or ""
                color_val = k_roll.get("color") or ""
                
                async with db.execute("""
                    INSERT INTO kavralan_sales (branch_id, roll_id, roll_code, width, sold_length, area_m2, price_per_m2, total_price, cost_price, profit, model, color, created_at)
                    VALUES (?, ?, ?, 4.0, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (branch_id, roll_id, k_roll["roll_code"], sold_len, sold_area, actual_price_per_m2, sale_total_price, item_cost, item_profit, model_val, color_val, created_at)) as cur_k:
                    sale_id = cur_k.lastrowid
                    
                batch_total += sale_total_price
                batch_cost += item_cost
                batch_profit += item_profit
                desc = f"4.0x{sold_len}m Kavralan"
                item_descriptions.append(desc)
                cat_totals["kavralan"] += sale_total_price
                cat_descriptions["kavralan"].append(desc)
                sale_records.append({
                    "sale_id": sale_id,
                    "product_type": "kavralan",
                    "roll_code": k_roll["roll_code"],
                    "sold_length": sold_len,
                    "sale_total_price": sale_total_price,
                    "profit": item_profit
                })

        batch_total = round(batch_total, 2)
        batch_cost = round(batch_cost, 2)
        batch_profit = round(batch_profit, 2)
        items_summary = ", ".join(item_descriptions)
        cat_totals = {c: round(v, 2) for c, v in cat_totals.items()}
        cat_titles = {"carpet": "Gilam", "leather": "Teri", "kavralan": "Kavralan"}
        present_cats = [c for c in ("carpet", "leather", "kavralan") if cat_descriptions[c]]
        is_mixed = len(present_cats) > 1

        # Nasiyada boshlang'ich to'lovni toifalar summasiga mutanosib taqsimlash
        # (sent qoldig'i oxirgi toifaga), shunda har bir toifa qarzi o'z kassasiga yopiladi
        cat_paid = {}
        if is_debt:
            initial_paid = round(float(initial_paid), 2)
            allocated = 0.0
            for idx, c in enumerate(present_cats):
                if idx == len(present_cats) - 1:
                    share = round(initial_paid - allocated, 2)
                else:
                    share = round(initial_paid * cat_totals[c] / batch_total, 2) if batch_total > 0 else 0.0
                    share = min(share, round(initial_paid - allocated, 2))
                cat_paid[c] = share
                allocated = round(allocated + share, 2)

        debt_ids = []
        new_balances = {}
        for c in present_cats:
            cat_summary = ", ".join(cat_descriptions[c])
            # Qoldiqni shu ulanish orqali o'qiymiz (tranzaksiya ichida)
            async with db.execute(
                "SELECT balance_after FROM cashbox WHERE branch_id = ? AND category = ? ORDER BY id DESC LIMIT 1",
                (branch_id, c)
            ) as cur_b:
                b_row = await cur_b.fetchone()
                cur_bal = round(b_row[0], 2) if b_row else 0.0

            if is_debt:
                paid = cat_paid[c]
                remaining_amount = round(cat_totals[c] - paid, 2)
                debt_status = "partial" if paid > 0 else "unpaid"
                details = (f"Chek ({len(items)} ta, {cat_titles[c]} qismi): {cat_summary}" if is_mixed
                           else f"Chek ({len(items)} ta): {items_summary}")

                async with db.execute("""
                    INSERT INTO debts (branch_id, category, customer_name, customer_phone, item_details, total_amount, initial_paid, paid_amount, remaining_amount, status, due_date, customer_telegram_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (branch_id, c, customer_name, customer_phone, details, cat_totals[c], paid, paid, remaining_amount, debt_status, due_date, customer_telegram_id, created_at, created_at)) as cur_d:
                    debt_id = cur_d.lastrowid
                debt_ids.append(debt_id)

                if paid > 0:
                    new_bal = round(cur_bal + paid, 2)
                    await db.execute("""
                        INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
                        VALUES (?, ?, 'INCOME', ?, ?, ?, ?)
                    """, (branch_id, c, paid, f"Nasiya boshlang'ich to'lov (Chek #{debt_id}, {cat_titles[c]}): {customer_name}", new_bal, created_at))

                    await db.execute("""
                        INSERT INTO debt_payments (debt_id, branch_id, category, amount, note, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (debt_id, branch_id, c, paid, "Boshlang'ich to'lov", created_at))
                else:
                    new_bal = cur_bal
            else:
                new_bal = round(cur_bal + cat_totals[c], 2)
                note = (f"Savdo (Chek: {len(items)} ta mahsulot, {cat_titles[c]} qismi: {cat_summary})" if is_mixed
                        else f"Savdo (Chek: {len(items)} ta mahsulot: {items_summary})")
                await db.execute("""
                    INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
                    VALUES (?, ?, 'INCOME', ?, ?, ?, ?)
                """, (branch_id, c, cat_totals[c], note, new_bal, created_at))
            new_balances[c] = new_bal

        await db.commit()

        return {
            "success": True,
            "total_amount": batch_total,
            "cost_price": batch_cost,
            "profit": batch_profit,
            "items_count": len(items),
            "debt_id": debt_ids[0] if debt_ids else None,
            "debt_ids": debt_ids,
            "is_debt": is_debt,
            "items_summary": items_summary,
            "sales": sale_records,
            "totals_by_category": {c: cat_totals[c] for c in present_cats},
            "new_cash_balances": new_balances
        }

# --- TERI FUNKSIYALARI ($50 / DONA) ---

async def add_leather(color: str, quantity: int, branch_id: int = 1, price_per_item: float = LEATHER_PRICE) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO leather_inventory (branch_id, color, quantity, price_per_item, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(branch_id, color) DO UPDATE SET
                quantity = quantity + excluded.quantity,
                updated_at = excluded.updated_at
        """, (branch_id, color, quantity, price_per_item, created_at))
        await db.commit()
        
        async with db.execute("SELECT quantity FROM leather_inventory WHERE branch_id = ? AND color = ?", (branch_id, color)) as cursor:
            row = await cursor.fetchone()
            total_qty = row[0]
            
    total_val = round(total_qty * price_per_item, 2)
    return {
        "branch_id": branch_id,
        "color": color,
        "added_quantity": quantity,
        "total_quantity": total_qty,
        "price_per_item": price_per_item,
        "total_value": total_val,
        "created_at": created_at
    }

async def get_leather_stock(branch_id: int | None = None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if branch_id is not None:
            query = "SELECT * FROM leather_inventory WHERE branch_id = ? AND quantity > 0 ORDER BY color ASC"
            params = (branch_id,)
        else:
            query = "SELECT * FROM leather_inventory WHERE quantity > 0 ORDER BY branch_id ASC, color ASC"
            params = ()
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_available_leather_colors(branch_id: int = 1) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT color, quantity FROM leather_inventory 
            WHERE branch_id = ? AND quantity > 0 
            ORDER BY color ASC
        """, (branch_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def make_leather_sale(
    color: str, 
    quantity: int, 
    branch_id: int = 1, 
    price_per_item: float = LEATHER_PRICE,
    custom_total_price: float | None = None,
    is_debt: bool = False,
    customer_name: str = "",
    customer_phone: str = "",
    initial_paid: float = 0.0,
    due_date: str | None = None,
    customer_telegram_id: int | None = None
) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT quantity FROM leather_inventory WHERE branch_id = ? AND color = ?", (branch_id, color)) as cursor:
            row = await cursor.fetchone()
            if not row or row["quantity"] < quantity:
                avail = row["quantity"] if row else 0
                raise ValueError(f"Omborda yetarli {color} teri yo'q! Mavjud: {avail} dona")
                
        new_qty = row["quantity"] - quantity
        await db.execute("""
            UPDATE leather_inventory 
            SET quantity = ?, updated_at = ? 
            WHERE branch_id = ? AND color = ?
        """, (new_qty, created_at, branch_id, color))
        
        if custom_total_price is not None and float(custom_total_price) > 0:
            sale_total_price = round(float(custom_total_price), 2)
            actual_price_per_item = round(sale_total_price / quantity, 2) if quantity > 0 else price_per_item
        else:
            actual_price_per_item = price_per_item
            sale_total_price = round(quantity * actual_price_per_item, 2)
            
        cost_price = round(quantity * LEATHER_PRICE, 2)
        profit = round(sale_total_price - cost_price, 2)
        
        async with db.execute("""
            INSERT INTO leather_sales (branch_id, color, quantity, price_per_item, total_price, cost_price, profit, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (branch_id, color, quantity, actual_price_per_item, sale_total_price, cost_price, profit, created_at)) as cursor:
            sale_id = cursor.lastrowid
            
        debt_id = None
        if is_debt:
            initial_paid = round(float(initial_paid), 2)
            remaining_amount = round(sale_total_price - initial_paid, 2)
            debt_status = "partial" if initial_paid > 0 else "unpaid"
            
            item_desc = f"Teri - {color} ({quantity} dona)"
            async with db.execute("""
                INSERT INTO debts (branch_id, category, customer_name, customer_phone, item_details, total_amount, initial_paid, paid_amount, remaining_amount, status, due_date, customer_telegram_id, created_at, updated_at)
                VALUES (?, 'leather', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (branch_id, customer_name, customer_phone, item_desc, sale_total_price, initial_paid, initial_paid, remaining_amount, debt_status, due_date, customer_telegram_id, created_at, created_at)) as cursor:
                debt_id = cursor.lastrowid
                
            current_balance = await get_cash_balance(branch_id=branch_id, category="leather")
            if initial_paid > 0:
                new_balance = round(current_balance + initial_paid, 2)
                await db.execute("""
                    INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
                    VALUES (?, 'leather', 'INCOME', ?, ?, ?, ?)
                """, (branch_id, initial_paid, f"Nasiya boshlang'ich to'lov (Teri): {customer_name} (#{debt_id})", new_balance, created_at))
                
                await db.execute("""
                    INSERT INTO debt_payments (debt_id, branch_id, category, amount, note, created_at)
                    VALUES (?, ?, 'leather', ?, ?, ?)
                """, (debt_id, branch_id, initial_paid, "Boshlang'ich to'lov", created_at))
            else:
                new_balance = current_balance
        else:
            # Teri kassasiga to'liq naqd tushum
            current_balance = await get_cash_balance(branch_id=branch_id, category="leather")
            new_balance = round(current_balance + sale_total_price, 2)
            await db.execute("""
                INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
                VALUES (?, 'leather', 'INCOME', ?, ?, ?, ?)
            """, (branch_id, sale_total_price, f"Sotuv (Teri): {quantity} dona - {color}", new_balance, created_at))
            
        await db.commit()
        
    return {
        "sale_id": sale_id,
        "debt_id": debt_id,
        "branch_id": branch_id,
        "color": color,
        "sold_quantity": quantity,
        "price_per_item": actual_price_per_item,
        "sale_total_price": sale_total_price,
        "cost_price": cost_price,
        "profit": profit,
        "remaining_quantity": new_qty,
        "is_debt": is_debt,
        "initial_paid": initial_paid if is_debt else sale_total_price,
        "remaining_debt": remaining_amount if is_debt else 0.0,
        "customer_name": customer_name,
        "created_at": created_at,
        "new_leather_cash_balance": new_balance
    }

# --- ASL KAVRALAN FUNKSIYALARI (4x, $30 / m²) ---

async def add_kavralan_roll(
    length: float, 
    branch_id: int = 1, 
    price_per_m2: float = KAVRALAN_PRICE, 
    cost_price_per_m2: float | None = None,
    model: str = "", 
    color: str = "", 
    width: float = KAVRALAN_WIDTH
) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    area_m2 = round(width * length, 2)
    if cost_price_per_m2 is None or float(cost_price_per_m2) <= 0:
        cost_price_per_m2 = price_per_m2
    else:
        cost_price_per_m2 = float(cost_price_per_m2)
    total_price = round(area_m2 * price_per_m2, 2)
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT MAX(id) FROM kavralan_rolls") as cursor:
            row = await cursor.fetchone()
            next_id = (row[0] or 0) + 1001
            
        roll_code = f"#K{branch_id}-{next_id}"
        
        await db.execute("""
            INSERT INTO kavralan_rolls (branch_id, roll_code, model, color, width, initial_length, current_length, area_m2, price_per_m2, cost_price_per_m2, total_price, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
        """, (branch_id, roll_code, model, color, width, length, length, area_m2, price_per_m2, cost_price_per_m2, total_price, created_at))
        await db.commit()
        
        return {
            "id": next_id,
            "branch_id": branch_id,
            "roll_code": roll_code,
            "model": model,
            "color": color,
            "width": width,
            "initial_length": length,
            "current_length": length,
            "area_m2": area_m2,
            "price_per_m2": price_per_m2,
            "cost_price_per_m2": cost_price_per_m2,
            "total_price": total_price,
            "created_at": created_at
        }

async def get_available_kavralan_rolls(branch_id: int = 1) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM kavralan_rolls 
            WHERE branch_id = ? AND current_length > 0 AND status = 'active'
            ORDER BY current_length ASC
        """, (branch_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_all_active_kavralan_rolls(branch_id: int | None = None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if branch_id is not None:
            query = "SELECT * FROM kavralan_rolls WHERE branch_id = ? AND current_length > 0 AND status = 'active' ORDER BY current_length DESC"
            params = (branch_id,)
        else:
            query = "SELECT * FROM kavralan_rolls WHERE current_length > 0 AND status = 'active' ORDER BY branch_id ASC, current_length DESC"
            params = ()
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_kavralan_roll_by_id(roll_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM kavralan_rolls WHERE id = ?", (roll_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def make_kavralan_sale(
    roll_id: int, 
    sold_length: float, 
    branch_id: int = 1, 
    price_per_m2: float = KAVRALAN_PRICE,
    custom_total_price: float | None = None,
    is_debt: bool = False,
    customer_name: str = "",
    customer_phone: str = "",
    initial_paid: float = 0.0,
    due_date: str | None = None,
    customer_telegram_id: int | None = None
) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    width = KAVRALAN_WIDTH
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM kavralan_rolls WHERE id = ? AND branch_id = ?", (roll_id, branch_id)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise ValueError("Kavralan ruloni topilmadi yoki boshqa filialga tegishli!")
            roll = dict(row)
            if sold_length > roll["current_length"]:
                raise ValueError(f"Rulonda yetarli uzunlik yo'q! Mavjud qoldiq: {roll['current_length']} m")
                
        new_length = round(roll["current_length"] - sold_length, 2)
        new_area = round(width * new_length, 2)
        new_total_price = round(new_area * price_per_m2, 2)
        new_status = "finished" if new_length <= 0 else "active"
        
        await db.execute("""
            UPDATE kavralan_rolls 
            SET current_length = ?, area_m2 = ?, total_price = ?, status = ?
            WHERE id = ?
        """, (new_length, new_area, new_total_price, new_status, roll_id))
        
        sold_area = round(width * sold_length, 2)
        if custom_total_price is not None and float(custom_total_price) > 0:
            sale_total_price = round(float(custom_total_price), 2)
            actual_price_per_m2 = round(sale_total_price / sold_area, 2) if sold_area > 0 else price_per_m2
        else:
            actual_price_per_m2 = price_per_m2
            sale_total_price = round(sold_area * actual_price_per_m2, 2)
            
        roll_cost_price = roll.get("cost_price_per_m2") if roll.get("cost_price_per_m2") is not None and roll.get("cost_price_per_m2") > 0 else (roll.get("price_per_m2") or KAVRALAN_PRICE)
        cost_price = round(sold_area * roll_cost_price, 2)
        profit = round(sale_total_price - cost_price, 2)
        
        model_val = roll.get("model") or ""
        color_val = roll.get("color") or ""
        
        async with db.execute("""
            INSERT INTO kavralan_sales (branch_id, roll_id, roll_code, width, sold_length, area_m2, price_per_m2, total_price, cost_price, profit, model, color, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (branch_id, roll_id, roll["roll_code"], width, sold_length, sold_area, actual_price_per_m2, sale_total_price, cost_price, profit, model_val, color_val, created_at)) as cursor:
            sale_id = cursor.lastrowid
            
        debt_id = None
        if is_debt:
            initial_paid = round(float(initial_paid), 2)
            remaining_amount = round(sale_total_price - initial_paid, 2)
            debt_status = "partial" if initial_paid > 0 else "unpaid"
            
            item_desc = f"Kavralan: {roll['roll_code']} (4x{sold_length}m = {sold_area} m²)"
            async with db.execute("""
                INSERT INTO debts (branch_id, category, customer_name, customer_phone, item_details, total_amount, initial_paid, paid_amount, remaining_amount, status, due_date, customer_telegram_id, created_at, updated_at)
                VALUES (?, 'kavralan', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (branch_id, customer_name, customer_phone, item_desc, sale_total_price, initial_paid, initial_paid, remaining_amount, debt_status, due_date, customer_telegram_id, created_at, created_at)) as cursor:
                debt_id = cursor.lastrowid
                
            current_balance = await get_cash_balance(branch_id=branch_id, category="kavralan")
            if initial_paid > 0:
                new_balance = round(current_balance + initial_paid, 2)
                await db.execute("""
                    INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
                    VALUES (?, 'kavralan', 'INCOME', ?, ?, ?, ?)
                """, (branch_id, initial_paid, f"Nasiya boshlang'ich to'lov (Kavralan): {customer_name} (#{debt_id})", new_balance, created_at))
                
                await db.execute("""
                    INSERT INTO debt_payments (debt_id, branch_id, category, amount, note, created_at)
                    VALUES (?, ?, 'kavralan', ?, ?, ?)
                """, (debt_id, branch_id, initial_paid, "Boshlang'ich to'lov", created_at))
            else:
                new_balance = current_balance
        else:
            # Kavralan kassasiga to'liq tushum
            current_balance = await get_cash_balance(branch_id=branch_id, category="kavralan")
            new_balance = round(current_balance + sale_total_price, 2)
            await db.execute("""
                INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
                VALUES (?, 'kavralan', 'INCOME', ?, ?, ?, ?)
            """, (branch_id, sale_total_price, f"Sotuv (Kavralan): {roll['roll_code']} (4x{sold_length}m = {sold_area} m²)", new_balance, created_at))
            
        await db.commit()
        
    return {
        "sale_id": sale_id,
        "debt_id": debt_id,
        "branch_id": branch_id,
        "roll_code": roll["roll_code"],
        "width": width,
        "sold_length": sold_length,
        "sold_area": sold_area,
        "price_per_m2": actual_price_per_m2,
        "sale_total_price": sale_total_price,
        "cost_price": cost_price,
        "profit": profit,
        "remaining_length": new_length,
        "is_debt": is_debt,
        "initial_paid": initial_paid if is_debt else sale_total_price,
        "remaining_debt": remaining_amount if is_debt else 0.0,
        "customer_name": customer_name,
        "created_at": created_at,
        "new_kavralan_cash_balance": new_balance
    }

# --- NASIYA (QARZ) FUNKSIYALARI ---

async def pay_debt(
    debt_id: int, 
    payment_amount: float, 
    branch_id: int, 
    note: str = "",
    payment_method: str = "cash",
    installment_id: int | None = None
) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM debts WHERE id = ?", (debt_id,)) as cursor:
            debt = await cursor.fetchone()
            if not debt:
                raise ValueError("Nasiya yozuvi topilmadi!")
                
        payment_amount = round(payment_amount, 2)
        if payment_amount <= 0:
            raise ValueError("To'lov summasi 0 dan katta bo'lishi kerak!")
            
        remaining_now = round(debt["remaining_amount"], 2)
        if payment_amount > remaining_now:
            raise ValueError(f"To'lov summasi mavjud qarzdan (${remaining_now:.2f}) ko'p bo'lishi mumkin emas!")
            
        new_paid = round(debt["paid_amount"] + payment_amount, 2)
        new_remaining = round(remaining_now - payment_amount, 2)
        new_status = "paid" if new_remaining <= 0.001 else "partial"
        
        await db.execute("""
            UPDATE debts 
            SET paid_amount = ?, remaining_amount = ?, status = ?, updated_at = ?
            WHERE id = ?
        """, (new_paid, new_remaining, new_status, created_at, debt_id))
        
        # Muddatli to'lov (Installment) holatini yangilash
        if installment_id:
            async with db.execute("SELECT * FROM debt_installments WHERE id = ? AND debt_id = ?", (installment_id, debt_id)) as cur_inst:
                inst = await cur_inst.fetchone()
                if inst:
                    inst_new_paid = round(inst["paid_amount"] + payment_amount, 2)
                    inst_status = "paid" if inst_new_paid >= round(inst["amount"] - 0.001, 2) else "partial"
                    inst_paid_at = created_at if inst_status == "paid" else inst["paid_at"]
                    await db.execute("""
                        UPDATE debt_installments
                        SET paid_amount = ?, status = ?, paid_at = ?
                        WHERE id = ?
                    """, (inst_new_paid, inst_status, inst_paid_at, installment_id))
        elif "is_installment" in debt.keys() and debt["is_installment"] == 1:
            # Avtomatik ravishda navbatdagi to'lanmagan oylik grafiklariga taqsimlash
            async with db.execute("""
                SELECT * FROM debt_installments 
                WHERE debt_id = ? AND status != 'paid' 
                ORDER BY month_number ASC
            """, (debt_id,)) as cur_insts:
                unpaid_insts = await cur_insts.fetchall()
                
            rem_alloc = payment_amount
            for u_inst in unpaid_insts:
                needed = round(u_inst["amount"] - u_inst["paid_amount"], 2)
                if needed <= 0:
                    continue
                alloc_amount = min(rem_alloc, needed)
                inst_new_paid = round(u_inst["paid_amount"] + alloc_amount, 2)
                inst_status = "paid" if inst_new_paid >= round(u_inst["amount"] - 0.001, 2) else "partial"
                inst_paid_at = created_at if inst_status == "paid" else u_inst["paid_at"]
                await db.execute("""
                    UPDATE debt_installments
                    SET paid_amount = ?, status = ?, paid_at = ?
                    WHERE id = ?
                """, (inst_new_paid, inst_status, inst_paid_at, u_inst["id"]))
                rem_alloc = round(rem_alloc - alloc_amount, 2)
                if rem_alloc <= 0:
                    break
        
        # Qarz to'lovlari tarixiga kiritish
        pay_method_label = "Karta" if payment_method.lower() in ("card", "karta", "click") else "Naqd"
        full_note = f"{note} ({pay_method_label})" if note else f"Qarz to'lovi ({pay_method_label})"
        await db.execute("""
            INSERT INTO debt_payments (debt_id, branch_id, category, amount, note, payment_method, installment_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (debt_id, debt["branch_id"], debt["category"], payment_amount, full_note, payment_method, installment_id, created_at))
        
        # Tegishli tovar kassasiga kirim qilish
        current_balance = await get_cash_balance(branch_id=debt["branch_id"], category=debt["category"])
        new_balance = round(current_balance + payment_amount, 2)
        cat_title = "Gilam" if debt["category"] == "carpet" else ("Teri" if debt["category"] == "leather" else "Kavralan")
        await db.execute("""
            INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
            VALUES (?, ?, 'INCOME', ?, ?, ?, ?)
        """, (debt["branch_id"], debt["category"], payment_amount, f"Qarz to'lovi ({cat_title}, {pay_method_label}): {debt['customer_name']} (#{debt_id})", new_balance, created_at))
        
        await db.commit()
        
        return {
            "debt_id": debt_id,
            "customer_name": debt["customer_name"],
            "customer_phone": debt["customer_phone"],
            "item_details": debt["item_details"],
            "category": debt["category"],
            "branch_id": debt["branch_id"],
            "payment_amount": payment_amount,
            "remaining_amount": new_remaining,
            "status": new_status,
            "payment_method": payment_method,
            "new_cash_balance": new_balance,
            "created_at": created_at
        }

async def edit_debt(
    debt_id: int, 
    new_total_amount: float, 
    branch_id: int | None = None,
    customer_name: str | None = None,
    customer_phone: str | None = None,
    due_date: str | None = None,
    note: str = ""
) -> dict:
    new_total_amount = round(float(new_total_amount), 2)
    if new_total_amount <= 0:
        raise ValueError("Qarz summasi 0 dan katta bo'lishi kerak!")
        
    created_at_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM debts WHERE id = ?", (debt_id,)) as cursor:
            debt = await cursor.fetchone()
            if not debt:
                raise ValueError("Nasiya yozuvi topilmadi!")
                
        if branch_id is not None and debt["branch_id"] != branch_id:
            raise ValueError("Faqat o'z filialingiz qarzini tahrirlashingiz mumkin!")
            
        d_branch = debt["branch_id"]
        d_category = debt["category"]
        d_created_at = debt["created_at"]
        old_total = round(float(debt["total_amount"]), 2)
        paid_amount = round(float(debt["paid_amount"]), 2)
        
        if new_total_amount < paid_amount - 0.001:
            raise ValueError(f"Yangi summa to'langan summadan (${paid_amount:.2f}) kam bo'lishi mumkin emas!")
            
        new_remaining = round(new_total_amount - paid_amount, 2)
        if new_remaining <= 0.001:
            new_status = "paid"
            new_remaining = 0.0
        elif paid_amount > 0:
            new_status = "partial"
        else:
            new_status = "unpaid"
            
        upd_name = customer_name.strip() if customer_name and customer_name.strip() else debt["customer_name"]
        upd_phone = customer_phone.strip() if customer_phone and customer_phone.strip() else (debt["customer_phone"] or "")
        upd_due_date = due_date.strip() if due_date and due_date.strip() else debt["due_date"]
        
        # 1. debts jadvalini yangilash
        await db.execute("""
            UPDATE debts 
            SET total_amount = ?, remaining_amount = ?, status = ?, customer_name = ?, customer_phone = ?, due_date = ?, updated_at = ?
            WHERE id = ?
        """, (new_total_amount, new_remaining, new_status, upd_name, upd_phone, upd_due_date, created_at_now, debt_id))
        
        # 2. Muddatli to'lov (Installments) mavjud bo'lsa, qolgan to'lanmagan oylarni qayta hisoblash
        if "is_installment" in debt.keys() and debt["is_installment"] == 1:
            async with db.execute("""
                SELECT * FROM debt_installments 
                WHERE debt_id = ? AND status != 'paid' 
                ORDER BY month_number ASC
            """, (debt_id,)) as cur_inst:
                unpaid_insts = [dict(r) for r in await cur_inst.fetchall()]
                
            if unpaid_insts:
                if new_remaining <= 0:
                    await db.execute("""
                        UPDATE debt_installments 
                        SET status = 'paid', paid_at = ? 
                        WHERE debt_id = ? AND status != 'paid'
                    """, (created_at_now, debt_id))
                else:
                    k = len(unpaid_insts)
                    per_inst = round(new_remaining / k, 2)
                    allocated = 0.0
                    for idx, inst in enumerate(unpaid_insts):
                        if idx == k - 1:
                            inst_amount = round(new_remaining - allocated, 2)
                        else:
                            inst_amount = per_inst
                            allocated = round(allocated + inst_amount, 2)
                        await db.execute("""
                            UPDATE debt_installments 
                            SET amount = ?, paid_amount = 0.0, status = 'pending' 
                            WHERE id = ?
                        """, (inst_amount, inst["id"]))

        # 3. UMUMIY HISOB-KITOB BILAN BOG'LASH: Bog'langan sotuv (Sale) ni yangilash
        # (Foyda va zarar, tushum va sof foyda to'g'ri hisoblanishi uchun)
        sale_updated = False
        sale_info = None

        if d_category == 'kavralan':
            async with db.execute("""
                SELECT * FROM kavralan_sales 
                WHERE branch_id = ? AND created_at = ?
                LIMIT 1
            """, (d_branch, d_created_at)) as cur_s:
                s_row = await cur_s.fetchone()

            if not s_row and debt.get("item_details"):
                import re
                m = re.search(r'#?([A-Za-z0-9_-]+)', debt["item_details"])
                if m:
                    async with db.execute("""
                        SELECT * FROM kavralan_sales 
                        WHERE branch_id = ? AND roll_code = ?
                        ORDER BY id DESC LIMIT 1
                    """, (d_branch, m.group(1))) as cur_s2:
                        s_row = await cur_s2.fetchone()

            if s_row:
                sale = dict(s_row)
                s_area = sale.get("area_m2") or 0.0
                s_cost = sale.get("cost_price") or 0.0
                new_pr_m2 = round(new_total_amount / s_area, 2) if s_area > 0 else (sale.get("price_per_m2") or 30.0)
                new_profit = round(new_total_amount - s_cost, 2)

                await db.execute("""
                    UPDATE kavralan_sales 
                    SET total_price = ?,
                        price_per_m2 = ?,
                        profit = ?
                    WHERE id = ?
                """, (new_total_amount, new_pr_m2, new_profit, sale["id"]))
                sale_updated = True
                sale_info = {"table": "kavralan_sales", "sale_id": sale["id"], "old_price": sale["total_price"], "new_price": new_total_amount, "new_profit": new_profit}

        elif d_category == 'carpet':
            async with db.execute("""
                SELECT * FROM sales 
                WHERE branch_id = ? AND created_at = ?
                LIMIT 1
            """, (d_branch, d_created_at)) as cur_s:
                s_row = await cur_s.fetchone()

            if not s_row and debt.get("item_details"):
                import re
                m = re.search(r'#?([A-Za-z0-9_-]+)', debt["item_details"])
                if m:
                    async with db.execute("""
                        SELECT * FROM sales 
                        WHERE branch_id = ? AND roll_code = ?
                        ORDER BY id DESC LIMIT 1
                    """, (d_branch, m.group(1))) as cur_s2:
                        s_row = await cur_s2.fetchone()

            if s_row:
                sale = dict(s_row)
                s_area = sale.get("area_m2") or 0.0
                s_cost = sale.get("cost_price") or 0.0
                new_pr_m2 = round(new_total_amount / s_area, 2) if s_area > 0 else (sale.get("price_per_m2") or 8.0)
                new_profit = round(new_total_amount - s_cost, 2)

                await db.execute("""
                    UPDATE sales 
                    SET total_price = ?,
                        price_per_m2 = ?,
                        profit = ?
                    WHERE id = ?
                """, (new_total_amount, new_pr_m2, new_profit, sale["id"]))
                sale_updated = True
                sale_info = {"table": "sales", "sale_id": sale["id"], "old_price": sale["total_price"], "new_price": new_total_amount, "new_profit": new_profit}

        elif d_category == 'leather':
            async with db.execute("""
                SELECT * FROM leather_sales 
                WHERE branch_id = ? AND created_at = ?
                LIMIT 1
            """, (d_branch, d_created_at)) as cur_s:
                s_row = await cur_s.fetchone()

            if s_row:
                sale = dict(s_row)
                s_qty = sale.get("quantity") or 1.0
                s_cost = sale.get("cost_price") or 0.0
                new_pr_item = round(new_total_amount / s_qty, 2) if s_qty > 0 else 50.0
                new_profit = round(new_total_amount - s_cost, 2)

                await db.execute("""
                    UPDATE leather_sales 
                    SET total_price = ?,
                        price_per_item = ?,
                        profit = ?
                    WHERE id = ?
                """, (new_total_amount, new_pr_item, new_profit, sale["id"]))
                sale_updated = True
                sale_info = {"table": "leather_sales", "sale_id": sale["id"], "old_price": sale["total_price"], "new_price": new_total_amount, "new_profit": new_profit}

        await db.commit()

        return {
            "success": True,
            "debt_id": debt_id,
            "old_total_amount": old_total,
            "new_total_amount": new_total_amount,
            "paid_amount": paid_amount,
            "remaining_amount": new_remaining,
            "status": new_status,
            "sale_updated": sale_updated,
            "sale_info": sale_info,
            "message": f"Nasiya summasi ${new_total_amount:.2f} qilib o'zgartirildi (Qolgan qarz: ${new_remaining:.2f})"
        }

async def setup_debt_installments(debt_id: int, months: int, start_date: str | None = None) -> list[dict]:
    import calendar
    from datetime import date, timedelta
    
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM debts WHERE id = ?", (debt_id,)) as cur:
            debt = await cur.fetchone()
            if not debt:
                raise ValueError("Nasiya topilmadi!")
                
        remaining = round(debt["remaining_amount"], 2)
        if remaining <= 0:
            raise ValueError("Qarz allaqachon to'liq to'langan!")
        if months <= 0:
            raise ValueError("Oylar soni kamida 1 bo'lishi kerak!")
            
        # Oldingi to'lanmagan grafiklarni tozalash
        await db.execute("DELETE FROM debt_installments WHERE debt_id = ? AND status != 'paid'", (debt_id,))
        
        # Oylarga teng taqsimlash va qoldiq sentlarni oxirgi oyga yaxlitlash
        base_amount = round(remaining / months, 2)
        total_calc = round(base_amount * months, 2)
        remainder = round(remaining - total_calc, 2)
        
        if start_date:
            try:
                base_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            except Exception:
                base_dt = datetime.now().date()
        else:
            base_dt = datetime.now().date()
            
        def add_months_date(sourcedate, months_to_add):
            month = sourcedate.month - 1 + months_to_add
            year = sourcedate.year + month // 12
            month = month % 12 + 1
            day = min(sourcedate.day, calendar.monthrange(year, month)[1])
            return date(year, month, day)

        installments = []
        for i in range(1, months + 1):
            m_amount = base_amount
            if i == months:
                m_amount = round(base_amount + remainder, 2)
                
            due_dt = add_months_date(base_dt, i)
            due_date_str = due_dt.strftime("%Y-%m-%d")
            
            async with db.execute("""
                INSERT INTO debt_installments (debt_id, branch_id, month_number, due_date, amount, paid_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, 0.0, 'pending', ?)
            """, (debt_id, debt["branch_id"], i, due_date_str, m_amount, created_at)) as ins_cur:
                installments.append({
                    "id": ins_cur.lastrowid,
                    "debt_id": debt_id,
                    "branch_id": debt["branch_id"],
                    "month_number": i,
                    "due_date": due_date_str,
                    "amount": m_amount,
                    "paid_amount": 0.0,
                    "status": "pending"
                })
                
        first_due = installments[0]["due_date"] if installments else None
        await db.execute("""
            UPDATE debts 
            SET is_installment = 1, installment_months = ?, due_date = COALESCE(due_date, ?), updated_at = ?
            WHERE id = ?
        """, (months, first_due, created_at, debt_id))
        
        await db.commit()
        return installments

async def cancel_debt_installments(debt_id: int) -> bool:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM debt_installments WHERE debt_id = ? AND status != 'paid'", (debt_id,))
        await db.execute("UPDATE debts SET is_installment = 0, updated_at = ? WHERE id = ?", (created_at, debt_id))
        await db.commit()
        return True

async def get_debt_full_details(debt_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM debts WHERE id = ?", (debt_id,)) as cur:
            debt = await cur.fetchone()
            if not debt:
                raise ValueError("Nasiya topilmadi!")
        debt_dict = dict(debt)
        
        # Installments
        async with db.execute("SELECT * FROM debt_installments WHERE debt_id = ? ORDER BY month_number ASC", (debt_id,)) as cur:
            installments = [dict(r) for r in await cur.fetchall()]
        debt_dict["installments"] = installments
        
        # Payments
        async with db.execute("SELECT * FROM debt_payments WHERE debt_id = ? ORDER BY id DESC", (debt_id,)) as cur:
            payments = [dict(r) for r in await cur.fetchall()]
        debt_dict["payments"] = payments
        
        return debt_dict

async def get_due_debts_for_reminders() -> dict:
    from datetime import date, timedelta
    
    today_dt = datetime.now().date()
    today_str = today_dt.strftime("%Y-%m-%d")
    tomorrow_str = (today_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    
    result = {}
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # 1. Muddatli to'lovlar
        async with db.execute("""
            SELECT di.*, d.customer_name, d.customer_phone, d.item_details, d.category, d.customer_telegram_id
            FROM debt_installments di
            JOIN debts d ON di.debt_id = d.id
            WHERE di.status != 'paid' AND d.status != 'paid' AND di.due_date <= ?
            ORDER BY di.due_date ASC
        """, (tomorrow_str,)) as cur:
            inst_rows = await cur.fetchall()
            
        inst_debt_ids = set()
        for r in inst_rows:
            bid = r["branch_id"]
            if bid not in result:
                result[bid] = {"today": [], "tomorrow": [], "overdue": []}
            inst_debt_ids.add(r["debt_id"])
            item = dict(r)
            if r["due_date"] == today_str:
                result[bid]["today"].append(item)
            elif r["due_date"] == tomorrow_str:
                result[bid]["tomorrow"].append(item)
            elif r["due_date"] < today_str:
                result[bid]["overdue"].append(item)
                
        # 2. Oddiy qarzlar (bo'lib to'lanmagan)
        async with db.execute("""
            SELECT * FROM debts 
            WHERE status != 'paid' AND due_date IS NOT NULL AND due_date != '' AND due_date <= ?
        """, (tomorrow_str,)) as cur:
            debt_rows = await cur.fetchall()
            
        for r in debt_rows:
            if r["id"] in inst_debt_ids:
                continue
            bid = r["branch_id"]
            if bid not in result:
                result[bid] = {"today": [], "tomorrow": [], "overdue": []}
            item = dict(r)
            if r["due_date"] == today_str:
                result[bid]["today"].append(item)
            elif r["due_date"] == tomorrow_str:
                result[bid]["tomorrow"].append(item)
            elif r["due_date"] < today_str:
                result[bid]["overdue"].append(item)
                
    return result

async def get_active_debts(branch_id: int | None = None, category: str | None = None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        conditions = ["status != 'paid'", "remaining_amount > 0"]
        params = []
        if branch_id is not None:
            conditions.append("branch_id = ?")
            params.append(branch_id)
        if category is not None:
            conditions.append("category = ?")
            params.append(category)
        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM debts WHERE {where_clause} ORDER BY id DESC"
        async with db.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_debt_by_id(debt_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM debts WHERE id = ?", (debt_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_debt_payments(debt_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM debt_payments WHERE debt_id = ? ORDER BY id DESC", (debt_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_closed_debts(branch_id: int | None = None, limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if branch_id is not None:
            q = "SELECT * FROM debts WHERE branch_id = ? AND status = 'paid' ORDER BY updated_at DESC LIMIT ?"
            p = (branch_id, limit)
        else:
            q = "SELECT * FROM debts WHERE status = 'paid' ORDER BY updated_at DESC LIMIT ?"
            p = (limit,)
        async with db.execute(q, p) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_debts_summary(branch_id: int | None = None) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        if branch_id is not None:
            async with db.execute("""
                SELECT 
                    COUNT(*), 
                    COALESCE(SUM(remaining_amount), 0),
                    COALESCE(SUM(CASE WHEN category = 'carpet' THEN remaining_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN category = 'leather' THEN remaining_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN category = 'kavralan' THEN remaining_amount ELSE 0 END), 0)
                FROM debts 
                WHERE branch_id = ? AND status != 'paid' AND remaining_amount > 0
            """, (branch_id,)) as cursor:
                count, total_rem, carpet_rem, leather_rem, kavralan_rem = await cursor.fetchone()
        else:
            async with db.execute("""
                SELECT 
                    COUNT(*), 
                    COALESCE(SUM(remaining_amount), 0),
                    COALESCE(SUM(CASE WHEN category = 'carpet' THEN remaining_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN category = 'leather' THEN remaining_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN category = 'kavralan' THEN remaining_amount ELSE 0 END), 0)
                FROM debts 
                WHERE status != 'paid' AND remaining_amount > 0
            """) as cursor:
                count, total_rem, carpet_rem, leather_rem, kavralan_rem = await cursor.fetchone()
                
        return {
            "active_count": count,
            "total_rem": round(total_rem, 2),
            "carpet_rem": round(carpet_rem, 2),
            "leather_rem": round(leather_rem, 2),
            "kavralan_rem": round(kavralan_rem, 2)
        }

# --- DASHBOARD STATISTIKASI (BARCHA TOIFALAR VA NASIYALAR ALOHIDA) ---

async def get_dashboard_stats(branch_id: int | None = None) -> dict:
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Gilam statistikasi
        if branch_id is not None:
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM rolls WHERE branch_id = ? AND status = 'active' AND current_length > 0", (branch_id,)) as cursor:
                carpet_rolls_count, carpet_total_m2, carpet_total_val = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM sales WHERE branch_id = ? AND created_at LIKE ?", (branch_id, f"{today_str}%")) as cursor:
                today_carpet_count, today_carpet_m2, today_carpet_rev = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM sales WHERE branch_id = ?", (branch_id,)) as cursor:
                all_carpet_count, all_carpet_m2, all_carpet_rev = await cursor.fetchone()
                
            # 2. Teri statistikasi
            async with db.execute("SELECT COALESCE(SUM(quantity), 0), COALESCE(SUM(quantity * price_per_item), 0) FROM leather_inventory WHERE branch_id = ?", (branch_id,)) as cursor:
                leather_total_qty, leather_total_val = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(quantity), 0), COALESCE(SUM(total_price), 0) FROM leather_sales WHERE branch_id = ? AND created_at LIKE ?", (branch_id, f"{today_str}%")) as cursor:
                today_leather_count, today_leather_qty, today_leather_rev = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(quantity), 0), COALESCE(SUM(total_price), 0) FROM leather_sales WHERE branch_id = ?", (branch_id,)) as cursor:
                all_leather_count, all_leather_qty, all_leather_rev = await cursor.fetchone()

            # 3. Asl Kavralan statistikasi
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM kavralan_rolls WHERE branch_id = ? AND status = 'active' AND current_length > 0", (branch_id,)) as cursor:
                kavralan_rolls_count, kavralan_total_m2, kavralan_total_val = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM kavralan_sales WHERE branch_id = ? AND created_at LIKE ?", (branch_id, f"{today_str}%")) as cursor:
                today_kavralan_count, today_kavralan_m2, today_kavralan_rev = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM kavralan_sales WHERE branch_id = ?", (branch_id,)) as cursor:
                all_kavralan_count, all_kavralan_m2, all_kavralan_rev = await cursor.fetchone()
        else:
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM rolls WHERE status = 'active' AND current_length > 0") as cursor:
                carpet_rolls_count, carpet_total_m2, carpet_total_val = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM sales WHERE created_at LIKE ?", (f"{today_str}%",)) as cursor:
                today_carpet_count, today_carpet_m2, today_carpet_rev = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM sales") as cursor:
                all_carpet_count, all_carpet_m2, all_carpet_rev = await cursor.fetchone()
                
            async with db.execute("SELECT COALESCE(SUM(quantity), 0), COALESCE(SUM(quantity * price_per_item), 0) FROM leather_inventory") as cursor:
                leather_total_qty, leather_total_val = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(quantity), 0), COALESCE(SUM(total_price), 0) FROM leather_sales WHERE created_at LIKE ?", (f"{today_str}%",)) as cursor:
                today_leather_count, today_leather_qty, today_leather_rev = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(quantity), 0), COALESCE(SUM(total_price), 0) FROM leather_sales") as cursor:
                all_leather_count, all_leather_qty, all_leather_rev = await cursor.fetchone()

            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM kavralan_rolls WHERE status = 'active' AND current_length > 0") as cursor:
                kavralan_rolls_count, kavralan_total_m2, kavralan_total_val = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM kavralan_sales WHERE created_at LIKE ?", (f"{today_str}%",)) as cursor:
                today_kavralan_count, today_kavralan_m2, today_kavralan_rev = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM kavralan_sales") as cursor:
                all_kavralan_count, all_kavralan_m2, all_kavralan_rev = await cursor.fetchone()

            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM branch3_sales WHERE created_at LIKE ?", (f"{today_str}%",)) as cursor:
                today_b3_count, today_b3_m2, today_b3_rev = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0) FROM branch3_sales") as cursor:
                all_b3_count, all_b3_m2, all_b3_rev = await cursor.fetchone()

    carpet_cash = await get_cash_balance(branch_id=branch_id, category="carpet")
    leather_cash = await get_cash_balance(branch_id=branch_id, category="leather")
    kavralan_cash = await get_cash_balance(branch_id=branch_id, category="kavralan")
    branch3_cash = await get_cash_balance(branch_id=3, category="branch3")
    debts_sum = await get_debts_summary(branch_id=branch_id)

    return {
        "branch_id": branch_id,
        # Gilam
        "carpet_rolls_count": carpet_rolls_count,
        "carpet_total_m2": round(carpet_total_m2, 2),
        "carpet_total_val": round(carpet_total_val, 2),
        "carpet_cash": round(carpet_cash, 2),
        "today_carpet_count": today_carpet_count,
        "today_carpet_m2": round(today_carpet_m2, 2),
        "today_carpet_rev": round(today_carpet_rev, 2),
        "all_carpet_count": all_carpet_count,
        "all_carpet_m2": round(all_carpet_m2, 2),
        "all_carpet_rev": round(all_carpet_rev, 2),
        # Teri
        "leather_total_qty": leather_total_qty,
        "leather_total_val": round(leather_total_val, 2),
        "leather_cash": round(leather_cash, 2),
        "today_leather_count": today_leather_count,
        "today_leather_qty": today_leather_qty,
        "today_leather_rev": round(today_leather_rev, 2),
        "all_leather_count": all_leather_count,
        "all_leather_qty": all_leather_qty,
        "all_leather_rev": round(all_leather_rev, 2),
        # Kavralan
        "kavralan_rolls_count": kavralan_rolls_count,
        "kavralan_total_m2": round(kavralan_total_m2, 2),
        "kavralan_total_val": round(kavralan_total_val, 2),
        "kavralan_cash": round(kavralan_cash, 2),
        "today_kavralan_count": today_kavralan_count,
        "today_kavralan_m2": round(today_kavralan_m2, 2),
        "today_kavralan_rev": round(today_kavralan_rev, 2),
        "all_kavralan_count": all_kavralan_count,
        "all_kavralan_m2": round(all_kavralan_m2, 2),
        "all_kavralan_rev": round(all_kavralan_rev, 2),
        # 3-Filial
        "branch3_cash": round(branch3_cash, 2),
        "today_b3_count": today_b3_count if branch_id is None else 0,
        "today_b3_m2": round(today_b3_m2, 2) if branch_id is None else 0.0,
        "today_b3_rev": round(today_b3_rev, 2) if branch_id is None else 0.0,
        "all_b3_count": all_b3_count if branch_id is None else 0,
        "all_b3_m2": round(all_b3_m2, 2) if branch_id is None else 0.0,
        "all_b3_rev": round(all_b3_rev, 2) if branch_id is None else 0.0,
        # Nasiyalar
        "active_debts_count": debts_sum["active_count"],
        "total_debt_rem": debts_sum["total_rem"],
        "carpet_debt_rem": debts_sum["carpet_rem"],
        "leather_debt_rem": debts_sum["leather_rem"],
        "kavralan_debt_rem": debts_sum["kavralan_rem"]
    }

# --- 3-FILIAL FUNKSIYALARI (OMBORSIZ SOTUV) ---

async def make_branch3_sale(collection_name: str, length: float, branch_id: int = 3, custom_price_per_m2: float | None = None) -> dict:
    if collection_name not in BRANCH3_COLLECTIONS:
        raise ValueError(f"Noto'g'ri mahsulot tanlandi: {collection_name}")
    length = round(float(length), 2)
    if length <= 0:
        raise ValueError("Uzunlik 0 dan katta bo'lishi kerak!")

    # Sotuvchi formada narxni o'zgartirgan bo'lsa, o'shani olamiz; aks holda kolleksiya narxi
    if custom_price_per_m2 is not None and float(custom_price_per_m2) > 0:
        price_per_m2 = round(float(custom_price_per_m2), 2)
    else:
        price_per_m2 = BRANCH3_COLLECTIONS[collection_name]
    width = BRANCH3_WIDTH
    area_m2 = round(width * length, 2)
    total_price = round(area_m2 * price_per_m2, 2)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            INSERT INTO branch3_sales (branch_id, collection_name, width, length, area_m2, price_per_m2, total_price, payment_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'cash', ?)
        """, (branch_id, collection_name, width, length, area_m2, price_per_m2, total_price, created_at)) as cursor:
            sale_id = cursor.lastrowid

        current_balance = await get_cash_balance(branch_id=branch_id, category="branch3")
        new_balance = round(current_balance + total_price, 2)
        await db.execute("""
            INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
            VALUES (?, 'branch3', 'INCOME', ?, ?, ?, ?)
        """, (branch_id, total_price, f"Sotuv (3-Filial): {collection_name} 4x{length}m ({area_m2} m²)", new_balance, created_at))
        await db.commit()

    return {
        "sale_id": sale_id,
        "branch_id": branch_id,
        "collection_name": collection_name,
        "width": width,
        "length": length,
        "area_m2": area_m2,
        "price_per_m2": price_per_m2,
        "total_price": total_price,
        "created_at": created_at,
        "new_cash_balance": new_balance
    }

async def get_branch3_stats(branch_id: int = 3) -> dict:
    today_str = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT 
                COUNT(*) as total_count,
                COALESCE(SUM(area_m2), 0) as total_m2,
                COALESCE(SUM(total_price), 0) as total_rev
            FROM branch3_sales WHERE branch_id = ?
        """, (branch_id,)) as cursor:
            tot = await cursor.fetchone()

        async with db.execute("""
            SELECT 
                COUNT(*) as today_count,
                COALESCE(SUM(area_m2), 0) as today_m2,
                COALESCE(SUM(total_price), 0) as today_rev
            FROM branch3_sales WHERE branch_id = ? AND created_at LIKE ?
        """, (branch_id, f"{today_str}%")) as cursor:
            td = await cursor.fetchone()

        async with db.execute("""
            SELECT 
                collection_name,
                COUNT(*) as count,
                COALESCE(SUM(area_m2), 0) as m2,
                COALESCE(SUM(total_price), 0) as rev
            FROM branch3_sales WHERE branch_id = ?
            GROUP BY collection_name
        """, (branch_id,)) as cursor:
            coll_rows = await cursor.fetchall()
            by_coll = {
                row["collection_name"]: {
                    "count": row["count"], 
                    "m2": round(row["m2"], 2), 
                    "rev": round(row["rev"], 2)
                } for row in coll_rows
            }

    cash_bal = await get_cash_balance(branch_id=branch_id, category="branch3")
    return {
        "branch_id": branch_id,
        "cash_balance": cash_bal,
        "total_count": tot["total_count"],
        "total_m2": round(tot["total_m2"], 2),
        "total_rev": round(tot["total_rev"], 2),
        "today_count": td["today_count"],
        "today_m2": round(td["today_m2"], 2),
        "today_rev": round(td["today_rev"], 2),
        "by_collection": by_coll
    }

async def get_branch3_sales_history(branch_id: int = 3, limit: int = 15) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM branch3_sales 
            WHERE branch_id = ? 
            ORDER BY id DESC LIMIT ?
        """, (branch_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

# --- FOYDA VA ZARAR HISOBOTI (P&L) ---

async def get_profit_loss_report(
    branch_id: int | None = None,
    period: str = "current_month",
    date_from: str | None = None,
    date_to: str | None = None,
    category: str = "all"
) -> dict:
    """
    period: 'current_month' (default), 'today', 'week', 'month', 'all', 'custom'
    branch_id: None for all branches (SuperAdmin) or specific branch ID (1=Labzak, 2=Kartal, 3=3-Filial)
    category: 'all', 'kavralan', 'carpet', 'leather', 'branch3'
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Sana sharti (Defolt: joriy oy boshidan oxirigacha)
        date_cond = ""
        date_params = []
        if (period == "current_month") or (not date_from and period not in ["all", "custom", "today", "week", "month"]):
            date_cond = "date(created_at) >= date('now', 'localtime', 'start of month') AND date(created_at) <= date('now', 'localtime', 'start of month', '+1 month', '-1 day')"
        elif period == "today":
            date_cond = "date(created_at) = date('now', 'localtime')"
        elif period == "week":
            date_cond = "date(created_at) >= date('now', 'localtime', '-6 days')"
        elif period == "month":
            date_cond = "date(created_at) >= date('now', 'localtime', '-29 days')"
        elif (period == "custom" or date_from) and date_from:
            if not date_to:
                date_to = date_from
            date_cond = "created_at >= ? AND created_at <= ?"
            date_params = [f"{date_from} 00:00:00", f"{date_to} 23:59:59"]
        else:
            # 'all'
            date_cond = "1=1"

        # Filial sharti
        branch_cond = ""
        branch_params = []
        if branch_id is not None:
            branch_cond = "branch_id = ?"
            branch_params = [branch_id]
        else:
            branch_cond = "1=1"

        where_clause = f"WHERE ({date_cond}) AND ({branch_cond})"
        all_params = date_params + branch_params

        # 1. Barcha sotuvlar ro'yxati (Gilam, Teri, Kavralan, 3-Filial)
        sales_query = f"""
            SELECT * FROM (
                SELECT 
                    s.id, s.branch_id, 'carpet' as category, ('Rezinka Gilam ' || s.roll_code || ' (' || s.color || ')') as title,
                    s.sold_length, s.area_m2, s.price_per_m2, s.total_price, 
                    COALESCE(s.cost_price, 0.0) as cost_price, 
                    COALESCE(s.profit, (s.total_price - COALESCE(s.cost_price, 0.0))) as profit,
                    s.created_at, s.roll_code, s.color, '' as model,
                    CASE WHEN d.id IS NOT NULL THEN 1 ELSE 0 END as is_debt,
                    COALESCE(d.customer_name, '') as customer_name,
                    COALESCE(d.remaining_amount, 0.0) as debt_remaining,
                    COALESCE(d.status, '') as debt_status,
                    d.id as debt_id
                FROM sales s
                LEFT JOIN debts d ON (d.category = 'carpet' AND d.branch_id = s.branch_id AND d.created_at = s.created_at)
                UNION ALL
                SELECT
                    ls.id, ls.branch_id, 'leather' as category, ('Teri (' || ls.color || ')') as title,
                    ls.quantity as sold_length, ls.quantity as area_m2, ls.price_per_item as price_per_m2, ls.total_price,
                    COALESCE(ls.cost_price, 0.0) as cost_price,
                    COALESCE(ls.profit, (ls.total_price - COALESCE(ls.cost_price, 0.0))) as profit,
                    ls.created_at, '' as roll_code, ls.color, '' as model,
                    CASE WHEN d.id IS NOT NULL THEN 1 ELSE 0 END as is_debt,
                    COALESCE(d.customer_name, '') as customer_name,
                    COALESCE(d.remaining_amount, 0.0) as debt_remaining,
                    COALESCE(d.status, '') as debt_status,
                    d.id as debt_id
                FROM leather_sales ls
                LEFT JOIN debts d ON (d.category = 'leather' AND d.branch_id = ls.branch_id AND d.created_at = ls.created_at)
                UNION ALL
                SELECT
                    ks.id, ks.branch_id, 'kavralan' as category,
                    CASE 
                        WHEN (COALESCE(ks.model, kr.model, '') != '' AND COALESCE(ks.color, kr.color, '') != '')
                            THEN ('Asl 4x (' || COALESCE(ks.model, kr.model) || ': ' || COALESCE(ks.color, kr.color) || ')')
                        WHEN COALESCE(ks.model, kr.model, '') != ''
                            THEN ('Asl 4x (' || COALESCE(ks.model, kr.model) || ')')
                        WHEN COALESCE(ks.color, kr.color, '') != ''
                            THEN ('Asl 4x (' || COALESCE(ks.color, kr.color) || ')')
                        ELSE ('Asl 4x (' || ks.roll_code || ')')
                    END as title,
                    ks.sold_length, ks.area_m2, ks.price_per_m2, ks.total_price,
                    COALESCE(ks.cost_price, 0.0) as cost_price,
                    COALESCE(ks.profit, (ks.total_price - COALESCE(ks.cost_price, 0.0))) as profit,
                    ks.created_at, ks.roll_code, COALESCE(ks.color, kr.color, '') as color, COALESCE(ks.model, kr.model, '') as model,
                    CASE WHEN d.id IS NOT NULL THEN 1 ELSE 0 END as is_debt,
                    COALESCE(d.customer_name, '') as customer_name,
                    COALESCE(d.remaining_amount, 0.0) as debt_remaining,
                    COALESCE(d.status, '') as debt_status,
                    d.id as debt_id
                FROM kavralan_sales ks
                LEFT JOIN kavralan_rolls kr ON ks.roll_id = kr.id
                LEFT JOIN debts d ON (d.category = 'kavralan' AND d.branch_id = ks.branch_id AND d.created_at = ks.created_at)
                UNION ALL
                SELECT
                    b3.id, b3.branch_id, 'branch3' as category, ('3-Filial ' || b3.collection_name) as title,
                    b3.length as sold_length, b3.area_m2, b3.price_per_m2, b3.total_price,
                    COALESCE(b3.cost_price, 0.0) as cost_price,
                    COALESCE(b3.profit, (b3.total_price - COALESCE(b3.cost_price, 0.0))) as profit,
                    b3.created_at, '' as roll_code, '' as color, '' as model,
                    0 as is_debt,
                    '' as customer_name,
                    0.0 as debt_remaining,
                    '' as debt_status,
                    NULL as debt_id
                FROM branch3_sales b3
            ) AS combined_sales
            {where_clause}
            ORDER BY created_at DESC
        """

        async with db.execute(sales_query, all_params) as cur:
            all_sales_rows = [dict(r) for r in await cur.fetchall()]

        # 2. Xarajatlar (Rasxod)
        expenses_query = f"""
            SELECT id, branch_id, category, operation_type, amount, note, balance_after, created_at
            FROM cashbox
            WHERE operation_type = 'EXPENSE' AND ({date_cond}) AND ({branch_cond})
            ORDER BY created_at DESC
        """
        async with db.execute(expenses_query, all_params) as cur:
            all_expenses_rows = [dict(r) for r in await cur.fetchall()]

        # 3. 3 ta bo'lim bo'yicha alohida hisob-kitoblar (Asl kavralan, Drap gilam, Teri)
        by_category = {}
        cat_definitions = [
            ("kavralan", "Asl kavralan", "🧶"),
            ("carpet", "Drap gilam", "🛋️"),
            ("leather", "Teri", "👞")
        ]
        for c_key, c_name, c_icon in cat_definitions:
            c_sales = [s for s in all_sales_rows if s.get("category") == c_key]
            c_expenses = [e for e in all_expenses_rows if e.get("category") == c_key]
            c_rev = round(sum(s["total_price"] for s in c_sales), 2)
            c_cost = round(sum(s["cost_price"] for s in c_sales), 2)
            c_gross = round(sum(s["profit"] for s in c_sales), 2)
            c_exp = round(sum(e["amount"] for e in c_expenses), 2)
            c_net = round(c_gross - c_exp, 2)
            by_category[c_key] = {
                "name": c_name,
                "icon": c_icon,
                "revenue": c_rev,
                "cost": c_cost,
                "gross_profit": c_gross,
                "expenses": c_exp,
                "net_profit": c_net,
                "sales_count": len(c_sales),
                "expenses_count": len(c_expenses)
            }

        # 3-Filial ma'lumotlari mavjud bo'lsa
        b3_sales = [s for s in all_sales_rows if s.get("category") == "branch3"]
        b3_expenses = [e for e in all_expenses_rows if e.get("category") == "branch3"]
        if b3_sales or b3_expenses or branch_id == 3:
            b3_rev = round(sum(s["total_price"] for s in b3_sales), 2)
            b3_cost = round(sum(s["cost_price"] for s in b3_sales), 2)
            b3_gross = round(sum(s["profit"] for s in b3_sales), 2)
            b3_exp = round(sum(e["amount"] for e in b3_expenses), 2)
            b3_net = round(b3_gross - b3_exp, 2)
            by_category["branch3"] = {
                "name": "3-Filial",
                "icon": "🏢",
                "revenue": b3_rev,
                "cost": b3_cost,
                "gross_profit": b3_gross,
                "expenses": b3_exp,
                "net_profit": b3_net,
                "sales_count": len(b3_sales),
                "expenses_count": len(b3_expenses)
            }

        # Agar kategoriya bo'yicha filtr tanlangan bo'lsa
        if category and category != "all" and category in by_category:
            active_sales = [s for s in all_sales_rows if s.get("category") == category]
            active_expenses = [e for e in all_expenses_rows if e.get("category") == category]
            c_info = by_category[category]
            total_revenue = c_info["revenue"]
            total_cost = c_info["cost"]
            gross_profit = c_info["gross_profit"]
            total_expenses = c_info["expenses"]
            net_profit = c_info["net_profit"]
        else:
            active_sales = all_sales_rows
            active_expenses = all_expenses_rows
            total_revenue = round(sum(s["total_price"] for s in all_sales_rows), 2)
            total_cost = round(sum(s["cost_price"] for s in all_sales_rows), 2)
            gross_profit = round(sum(s["profit"] for s in all_sales_rows), 2)
            total_expenses = round(sum(e["amount"] for e in all_expenses_rows), 2)
            net_profit = round(gross_profit - total_expenses, 2)

        # Filiallar bo'yicha guruhlash (SuperAdmin uchun)
        by_branch = {}
        for bid, bname in BRANCH_NAMES.items():
            b_sales = [s for s in active_sales if s["branch_id"] == bid]
            b_expenses = [e for e in active_expenses if e["branch_id"] == bid]
            b_rev = round(sum(s["total_price"] for s in b_sales), 2)
            b_cost = round(sum(s["cost_price"] for s in b_sales), 2)
            b_gross = round(sum(s["profit"] for s in b_sales), 2)
            b_exp = round(sum(e["amount"] for e in b_expenses), 2)
            b_net = round(b_gross - b_exp, 2)
            by_branch[bid] = {
                "branch_name": bname,
                "revenue": b_rev,
                "cost": b_cost,
                "gross_profit": b_gross,
                "expenses": b_exp,
                "net_profit": b_net,
                "sales_count": len(b_sales)
            }

        # 4. Kassa qoldiqlari (Qo'ldagi naqd pul)
        cash_kavralan = await get_cash_balance(branch_id=branch_id, category="kavralan")
        cash_carpet = await get_cash_balance(branch_id=branch_id, category="carpet")
        cash_leather = await get_cash_balance(branch_id=branch_id, category="leather")
        cash_b3 = await get_cash_balance(branch_id=3, category="branch3") if (branch_id is None or branch_id == 3) else 0.0
        cash_total = round(cash_kavralan + cash_carpet + cash_leather + cash_b3, 2)

        # 5. Faol qarzlar (Nasiya qoldiqlari)
        d_branch_sql = f"AND branch_id = {branch_id}" if branch_id is not None else ""
        debts_by_cat = {}
        async with db.execute(f"SELECT category, SUM(remaining_amount) FROM debts WHERE status != 'paid' {d_branch_sql} GROUP BY category") as d_cur:
            for d_row in await d_cur.fetchall():
                debts_by_cat[d_row[0]] = round(d_row[1] or 0.0, 2)
        debts_total = round(sum(debts_by_cat.values()), 2)

        # by_category ga kassa va qarz ma'lumotlarini qo'shish
        for c_key in by_category:
            if c_key == 'kavralan':
                by_category[c_key]["cash_balance"] = cash_kavralan
            elif c_key == 'carpet':
                by_category[c_key]["cash_balance"] = cash_carpet
            elif c_key == 'leather':
                by_category[c_key]["cash_balance"] = cash_leather
            elif c_key == 'branch3':
                by_category[c_key]["cash_balance"] = cash_b3
            else:
                by_category[c_key]["cash_balance"] = 0.0
            by_category[c_key]["debt_remaining"] = debts_by_cat.get(c_key, 0.0)

        return {
            "period": period,
            "branch_id": branch_id,
            "category": category,
            "date_from": date_from,
            "date_to": date_to,
            "summary": {
                "total_revenue": total_revenue,
                "total_cost": total_cost,
                "gross_profit": gross_profit,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "sales_count": len(active_sales),
                "expenses_count": len(active_expenses)
            },
            "cash_balances": {
                "kavralan": cash_kavralan,
                "carpet": cash_carpet,
                "leather": cash_leather,
                "branch3": cash_b3,
                "total": cash_total
            },
            "debts_balances": {
                **debts_by_cat,
                "total": debts_total
            },
            "by_category": by_category,
            "by_branch": by_branch,
            "sales": active_sales,
            "all_sales": all_sales_rows,
            "expenses": active_expenses,
            "all_expenses": all_expenses_rows
        }



# --- SOTUVNI O'CHIRISH (BEKOR QILISH) VA QOLDIQLARNI QAYTARISH ---

async def _recalc_cashbox_balance(db, branch_id: int, category: str):
    async with db.execute(
        "SELECT id, operation_type, amount FROM cashbox WHERE branch_id = ? AND category = ? ORDER BY id ASC",
        (branch_id, category)
    ) as cur:
        rows = await cur.fetchall()
    
    bal = 0.0
    for r_id, op_type, amt in rows:
        if op_type == 'INCOME':
            bal = round(bal + amt, 2)
        else:
            bal = round(bal - amt, 2)
        await db.execute("UPDATE cashbox SET balance_after = ? WHERE id = ?", (bal, r_id))

async def delete_sale(sale_id: int, category: str, branch_id: int | None = None) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        if category == 'kavralan':
            async with db.execute("SELECT * FROM kavralan_sales WHERE id = ?", (sale_id,)) as cur:
                row = await cur.fetchone()
            if not row:
                raise ValueError("Kavralan sotuvi topilmadi!")
            sale = dict(row)
            if branch_id is not None and sale["branch_id"] != branch_id:
                raise ValueError("Faqat o'z filialingiz sotuvini o'chirishingiz mumkin!")
                
            s_branch = sale["branch_id"]
            sold_len = sale["sold_length"]
            roll_id = sale["roll_id"]
            roll_code = sale["roll_code"]
            total_price = sale["total_price"]
            
            # 1. Rulon qoldig'ini tiklash
            async with db.execute("SELECT * FROM kavralan_rolls WHERE id = ?", (roll_id,)) as cur:
                r_row = await cur.fetchone()
            if r_row:
                roll = dict(r_row)
                cur_len = round(roll["current_length"] + sold_len, 2)
                cur_area = round(roll["width"] * cur_len, 2)
                pr_m2 = roll.get("price_per_m2") or 30.0
                cur_tot = round(cur_area * pr_m2, 2)
                await db.execute("""
                    UPDATE kavralan_rolls 
                    SET current_length = ?, area_m2 = ?, total_price = ?, status = 'active'
                    WHERE id = ?
                """, (cur_len, cur_area, cur_tot, roll_id))
                
            # 2. Kassadan o'chirish va balansni qayta hisoblash
            async with db.execute("""
                SELECT id FROM cashbox 
                WHERE branch_id = ? AND category = 'kavralan' AND operation_type = 'INCOME' 
                  AND (note LIKE ? OR amount = ?)
                ORDER BY id DESC LIMIT 1
            """, (s_branch, f"%{roll_code}%", total_price)) as cur:
                cb_row = await cur.fetchone()
            if cb_row:
                await db.execute("DELETE FROM cashbox WHERE id = ?", (cb_row[0],))
                await _recalc_cashbox_balance(db, s_branch, 'kavralan')
                
            # 3. Nasiyani o'chirish (agar bo'lsa)
            async with db.execute("""
                SELECT id FROM debts 
                WHERE branch_id = ? AND category = 'kavralan' AND (item_details LIKE ? OR created_at = ?)
                ORDER BY id DESC LIMIT 1
            """, (s_branch, f"%{roll_code}%", sale["created_at"])) as cur:
                d_row = await cur.fetchone()
            if d_row:
                await db.execute("DELETE FROM debt_payments WHERE debt_id = ?", (d_row[0],))
                await db.execute("DELETE FROM debt_installments WHERE debt_id = ?", (d_row[0],))
                await db.execute("DELETE FROM debts WHERE id = ?", (d_row[0],))
                
            # 4. Sotuvni o'chirish
            await db.execute("DELETE FROM kavralan_sales WHERE id = ?", (sale_id,))
            await db.commit()
            return {"success": True, "sale_id": sale_id, "category": category, "message": f"Kavralan sotuvi ({roll_code}) muvaffaqiyatli o'chirildi va ombor qoldig'iga qaytarildi!"}
            
        elif category == 'carpet':
            async with db.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)) as cur:
                row = await cur.fetchone()
            if not row:
                raise ValueError("Gilam sotuvi topilmadi!")
            sale = dict(row)
            if branch_id is not None and sale["branch_id"] != branch_id:
                raise ValueError("Faqat o'z filialingiz sotuvini o'chirishingiz mumkin!")
                
            s_branch = sale["branch_id"]
            sold_len = sale["sold_length"]
            roll_id = sale["roll_id"]
            roll_code = sale["roll_code"]
            total_price = sale["total_price"]
            
            # 1. Rulon qoldig'ini tiklash
            async with db.execute("SELECT * FROM rolls WHERE id = ?", (roll_id,)) as cur:
                r_row = await cur.fetchone()
            if r_row:
                roll = dict(r_row)
                cur_len = round(roll["current_length"] + sold_len, 2)
                cur_area = round(roll["width"] * cur_len, 2)
                pr_m2 = roll.get("price_per_m2") or 8.0
                cur_tot = round(cur_area * pr_m2, 2)
                await db.execute("""
                    UPDATE rolls 
                    SET current_length = ?, area_m2 = ?, total_price = ?, status = 'active'
                    WHERE id = ?
                """, (cur_len, cur_area, cur_tot, roll_id))
                
            # 2. Kassadan o'chirish
            async with db.execute("""
                SELECT id FROM cashbox 
                WHERE branch_id = ? AND category = 'carpet' AND operation_type = 'INCOME' 
                  AND (note LIKE ? OR amount = ?)
                ORDER BY id DESC LIMIT 1
            """, (s_branch, f"%{roll_code}%", total_price)) as cur:
                cb_row = await cur.fetchone()
            if cb_row:
                await db.execute("DELETE FROM cashbox WHERE id = ?", (cb_row[0],))
                await _recalc_cashbox_balance(db, s_branch, 'carpet')
                
            # 3. Nasiyani o'chirish
            async with db.execute("""
                SELECT id FROM debts 
                WHERE branch_id = ? AND category = 'carpet' AND item_details LIKE ?
                ORDER BY id DESC LIMIT 1
            """, (s_branch, f"%{roll_code}%")) as cur:
                d_row = await cur.fetchone()
            if d_row:
                await db.execute("DELETE FROM debt_payments WHERE debt_id = ?", (d_row[0],))
                await db.execute("DELETE FROM debt_installments WHERE debt_id = ?", (d_row[0],))
                await db.execute("DELETE FROM debts WHERE id = ?", (d_row[0],))
                
            # 4. Sotuvni o'chirish
            await db.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
            await db.commit()
            return {"success": True, "sale_id": sale_id, "category": category, "message": f"Gilam sotuvi ({roll_code}) muvaffaqiyatli o'chirildi va ombor qoldig'iga qaytarildi!"}
            
        elif category == 'leather':
            async with db.execute("SELECT * FROM leather_sales WHERE id = ?", (sale_id,)) as cur:
                row = await cur.fetchone()
            if not row:
                raise ValueError("Teri sotuvi topilmadi!")
            sale = dict(row)
            if branch_id is not None and sale["branch_id"] != branch_id:
                raise ValueError("Faqat o'z filialingiz sotuvini o'chirishingiz mumkin!")
                
            s_branch = sale["branch_id"]
            color = sale["color"]
            qty = sale["quantity"]
            total_price = sale["total_price"]
            
            # 1. Ombor qoldig'ini tiklash
            await db.execute("""
                UPDATE leather_inventory 
                SET quantity = quantity + ? 
                WHERE color = ? AND branch_id = ?
            """, (qty, color, s_branch))
            
            # 2. Kassadan o'chirish
            async with db.execute("""
                SELECT id FROM cashbox 
                WHERE branch_id = ? AND category = 'leather' AND operation_type = 'INCOME' 
                  AND (note LIKE ? OR amount = ?)
                ORDER BY id DESC LIMIT 1
            """, (s_branch, f"%{color}%", total_price)) as cur:
                cb_row = await cur.fetchone()
            if cb_row:
                await db.execute("DELETE FROM cashbox WHERE id = ?", (cb_row[0],))
                await _recalc_cashbox_balance(db, s_branch, 'leather')
                
            # 3. Nasiyani o'chirish
            async with db.execute("""
                SELECT id FROM debts 
                WHERE branch_id = ? AND category = 'leather' AND item_details LIKE ?
                ORDER BY id DESC LIMIT 1
            """, (s_branch, f"%{color}%")) as cur:
                d_row = await cur.fetchone()
            if d_row:
                await db.execute("DELETE FROM debt_payments WHERE debt_id = ?", (d_row[0],))
                await db.execute("DELETE FROM debt_installments WHERE debt_id = ?", (d_row[0],))
                await db.execute("DELETE FROM debts WHERE id = ?", (d_row[0],))
                
            # 4. Sotuvni o'chirish
            await db.execute("DELETE FROM leather_sales WHERE id = ?", (sale_id,))
            await db.commit()
            return {"success": True, "sale_id": sale_id, "category": category, "message": f"Teri sotuvi ({color}) muvaffaqiyatli o'chirildi va ombor qoldig'iga qaytarildi!"}
            
        elif category == 'branch3':
            async with db.execute("SELECT * FROM branch3_sales WHERE id = ?", (sale_id,)) as cur:
                row = await cur.fetchone()
            if not row:
                raise ValueError("3-Filial sotuvi topilmadi!")
            sale = dict(row)
            if branch_id is not None and sale["branch_id"] != branch_id:
                raise ValueError("Faqat o'z filialingiz sotuvini o'chirishingiz mumkin!")
                
            s_branch = sale["branch_id"]
            coll = sale["collection_name"]
            total_price = sale["total_price"]
            
            # 1. Kassadan o'chirish
            async with db.execute("""
                SELECT id FROM cashbox 
                WHERE branch_id = ? AND category = 'branch3' AND operation_type = 'INCOME' 
                  AND (note LIKE ? OR amount = ?)
                ORDER BY id DESC LIMIT 1
            """, (s_branch, f"%{coll}%", total_price)) as cur:
                cb_row = await cur.fetchone()
            if cb_row:
                await db.execute("DELETE FROM cashbox WHERE id = ?", (cb_row[0],))
                await _recalc_cashbox_balance(db, s_branch, 'branch3')
                
            # 2. Sotuvni o'chirish
            await db.execute("DELETE FROM branch3_sales WHERE id = ?", (sale_id,))
            await db.commit()
            return {"success": True, "sale_id": sale_id, "category": category, "message": f"3-Filial sotuvi ({coll}) muvaffaqiyatli o'chirildi!"}
        else:
            raise ValueError(f"Noma'lum kategoriya: {category}")


async def edit_sale(
    sale_id: int, 
    category: str, 
    new_length: float, 
    new_total_price: float, 
    branch_id: int | None = None
) -> dict:
    new_length = round(float(new_length), 2)
    new_total_price = round(float(new_total_price), 2)
    if new_length <= 0:
        raise ValueError("Uzunlik yoki miqdor 0 dan katta bo'lishi kerak!")
    if new_total_price <= 0:
        raise ValueError("Sotuv summasi 0 dan katta bo'lishi kerak!")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if category == 'kavralan':
            async with db.execute("SELECT * FROM kavralan_sales WHERE id = ?", (sale_id,)) as cur:
                row = await cur.fetchone()
            if not row:
                raise ValueError("Kavralan sotuvi topilmadi!")
            sale = dict(row)
            if branch_id is not None and sale["branch_id"] != branch_id:
                raise ValueError("Faqat o'z filialingiz sotuvini tahrirlashingiz mumkin!")

            s_branch = sale["branch_id"]
            old_len = sale["sold_length"]
            old_tot = sale["total_price"]
            roll_id = sale["roll_id"]
            roll_code = sale["roll_code"]
            created_at = sale["created_at"]
            width = sale.get("width") or 4.0

            async with db.execute("SELECT * FROM kavralan_rolls WHERE id = ?", (roll_id,)) as cur:
                r_row = await cur.fetchone()
            if not r_row:
                raise ValueError("Kavralan ruloni topilmadi!")
            roll = dict(r_row)

            len_diff = round(new_length - old_len, 2)
            new_roll_len = round(roll["current_length"] - len_diff, 2)
            if new_roll_len < 0:
                raise ValueError(f"Rulonda yetarli qoldiq yo'q! Mavjud: {roll['current_length']}m, yana kerak: {len_diff}m")

            new_roll_area = round(roll["width"] * new_roll_len, 2)
            r_pr = roll.get("price_per_m2") or 30.0
            new_roll_tot = round(new_roll_area * r_pr, 2)
            new_roll_status = "finished" if new_roll_len <= 0 else "active"

            await db.execute("""
                UPDATE kavralan_rolls
                SET current_length = ?, area_m2 = ?, total_price = ?, status = ?
                WHERE id = ?
            """, (new_roll_len, new_roll_area, new_roll_tot, new_roll_status, roll_id))

            new_area = round(width * new_length, 2)
            actual_pr_m2 = round(new_total_price / new_area, 2) if new_area > 0 else 30.0
            cost_pr_m2 = roll.get("cost_price_per_m2") if roll.get("cost_price_per_m2") is not None and roll.get("cost_price_per_m2") > 0 else 30.0
            new_cost = round(new_area * cost_pr_m2, 2)
            new_profit = round(new_total_price - new_cost, 2)

            await db.execute("""
                UPDATE kavralan_sales
                SET sold_length = ?, area_m2 = ?, price_per_m2 = ?, total_price = ?, cost_price = ?, profit = ?
                WHERE id = ?
            """, (new_length, new_area, actual_pr_m2, new_total_price, new_cost, new_profit, sale_id))

            # Nasiya (qarz) tekshirish
            async with db.execute("""
                SELECT id, total_amount, initial_paid, paid_amount FROM debts
                WHERE branch_id = ? AND category = 'kavralan' AND (item_details LIKE ? OR created_at = ?)
                ORDER BY id DESC LIMIT 1
            """, (s_branch, f"%{roll_code}%", created_at)) as cur:
                d_row = await cur.fetchone()

            if d_row:
                d_id = d_row[0]
                d_paid = d_row[3]
                new_remaining = round(new_total_price - d_paid, 2)
                new_d_status = "paid" if new_remaining <= 0 else ("partial" if d_paid > 0 else "unpaid")
                item_desc = f"Kavralan: {roll['roll_code']} (4x{new_length}m = {new_area} m²)"
                await db.execute("""
                    UPDATE debts
                    SET total_amount = ?, remaining_amount = ?, status = ?, item_details = ?, updated_at = ?
                    WHERE id = ?
                """, (new_total_price, new_remaining, new_d_status, item_desc, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), d_id))
            else:
                async with db.execute("""
                    SELECT id FROM cashbox
                    WHERE branch_id = ? AND category = 'kavralan' AND operation_type = 'INCOME'
                      AND (note LIKE ? OR created_at = ? OR amount = ?)
                    ORDER BY id DESC LIMIT 1
                """, (s_branch, f"%{roll_code}%", created_at, old_tot)) as cur:
                    cb_row = await cur.fetchone()
                if cb_row:
                    await db.execute("UPDATE cashbox SET amount = ? WHERE id = ?", (new_total_price, cb_row[0]))
                    await _recalc_cashbox_balance(db, s_branch, 'kavralan')

            await db.commit()
            return {
                "success": True,
                "sale_id": sale_id,
                "category": category,
                "sold_length": new_length,
                "area_m2": new_area,
                "total_price": new_total_price,
                "cost_price": new_cost,
                "profit": new_profit,
                "message": f"Kavralan sotuvi muvaffaqiyatli tahrirlandi!"
            }

        elif category == 'carpet':
            async with db.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)) as cur:
                row = await cur.fetchone()
            if not row:
                raise ValueError("Gilam sotuvi topilmadi!")
            sale = dict(row)
            if branch_id is not None and sale["branch_id"] != branch_id:
                raise ValueError("Faqat o'z filialingiz sotuvini tahrirlashingiz mumkin!")

            s_branch = sale["branch_id"]
            old_len = sale["sold_length"]
            old_tot = sale["total_price"]
            roll_id = sale["roll_id"]
            roll_code = sale["roll_code"]
            created_at = sale["created_at"]
            width = sale.get("width") or 1.2

            async with db.execute("SELECT * FROM rolls WHERE id = ?", (roll_id,)) as cur:
                r_row = await cur.fetchone()
            if not r_row:
                raise ValueError("Gilam ruloni topilmadi!")
            roll = dict(r_row)

            len_diff = round(new_length - old_len, 2)
            new_roll_len = round(roll["current_length"] - len_diff, 2)
            if new_roll_len < 0:
                raise ValueError(f"Rulonda yetarli qoldiq yo'q! Mavjud: {roll['current_length']}m, yana kerak: {len_diff}m")

            new_roll_area = round(roll["width"] * new_roll_len, 2)
            r_pr = roll.get("price_per_m2") or 8.0
            new_roll_tot = round(new_roll_area * r_pr, 2)
            new_roll_status = "finished" if new_roll_len <= 0 else "active"

            await db.execute("""
                UPDATE rolls
                SET current_length = ?, area_m2 = ?, total_price = ?, status = ?
                WHERE id = ?
            """, (new_roll_len, new_roll_area, new_roll_tot, new_roll_status, roll_id))

            new_area = round(width * new_length, 2)
            actual_pr_m2 = round(new_total_price / new_area, 2) if new_area > 0 else 8.0
            cost_pr_m2 = roll.get("cost_price_per_m2") or roll.get("cost_price") or 8.0
            new_cost = round(new_area * cost_pr_m2, 2)
            new_profit = round(new_total_price - new_cost, 2)

            await db.execute("""
                UPDATE sales
                SET sold_length = ?, area_m2 = ?, price_per_m2 = ?, total_price = ?, cost_price = ?, profit = ?
                WHERE id = ?
            """, (new_length, new_area, actual_pr_m2, new_total_price, new_cost, new_profit, sale_id))

            async with db.execute("""
                SELECT id, total_amount, initial_paid, paid_amount FROM debts
                WHERE branch_id = ? AND category = 'carpet' AND (item_details LIKE ? OR created_at = ?)
                ORDER BY id DESC LIMIT 1
            """, (s_branch, f"%{roll_code}%", created_at)) as cur:
                d_row = await cur.fetchone()

            if d_row:
                d_id = d_row[0]
                d_paid = d_row[3]
                new_remaining = round(new_total_price - d_paid, 2)
                new_d_status = "paid" if new_remaining <= 0 else ("partial" if d_paid > 0 else "unpaid")
                item_desc = f"Rezinka Gilam {roll['roll_code']} ({roll['width']:g}x{new_length}m = {new_area} m², {roll['color']})"
                await db.execute("""
                    UPDATE debts
                    SET total_amount = ?, remaining_amount = ?, status = ?, item_details = ?, updated_at = ?
                    WHERE id = ?
                """, (new_total_price, new_remaining, new_d_status, item_desc, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), d_id))
            else:
                async with db.execute("""
                    SELECT id FROM cashbox
                    WHERE branch_id = ? AND category = 'carpet' AND operation_type = 'INCOME'
                      AND (note LIKE ? OR created_at = ? OR amount = ?)
                    ORDER BY id DESC LIMIT 1
                """, (s_branch, f"%{roll_code}%", created_at, old_tot)) as cur:
                    cb_row = await cur.fetchone()
                if cb_row:
                    await db.execute("UPDATE cashbox SET amount = ? WHERE id = ?", (new_total_price, cb_row[0]))
                    await _recalc_cashbox_balance(db, s_branch, 'carpet')

            await db.commit()
            return {
                "success": True,
                "sale_id": sale_id,
                "category": category,
                "sold_length": new_length,
                "area_m2": new_area,
                "total_price": new_total_price,
                "cost_price": new_cost,
                "profit": new_profit,
                "message": f"Gilam sotuvi muvaffaqiyatli tahrirlandi!"
            }

        elif category == 'leather':
            async with db.execute("SELECT * FROM leather_sales WHERE id = ?", (sale_id,)) as cur:
                row = await cur.fetchone()
            if not row:
                raise ValueError("Teri sotuvi topilmadi!")
            sale = dict(row)
            if branch_id is not None and sale["branch_id"] != branch_id:
                raise ValueError("Faqat o'z filialingiz sotuvini tahrirlashingiz mumkin!")

            s_branch = sale["branch_id"]
            old_qty = int(sale["quantity"])
            new_qty = int(new_length)
            color = sale["color"]
            created_at = sale["created_at"]
            old_tot = sale["total_price"]

            async with db.execute("SELECT quantity FROM leather_inventory WHERE branch_id = ? AND color = ?", (s_branch, color)) as cur:
                inv_row = await cur.fetchone()
            curr_stock = inv_row[0] if inv_row else 0
            qty_diff = new_qty - old_qty
            if curr_stock - qty_diff < 0:
                raise ValueError(f"Omborda yetarli teri yo'q! Mavjud: {curr_stock} dona")

            await db.execute("""
                UPDATE leather_inventory
                SET quantity = quantity - ?
                WHERE branch_id = ? AND color = ?
            """, (qty_diff, s_branch, color))

            actual_pr_item = round(new_total_price / new_qty, 2) if new_qty > 0 else 0.0
            cost_item = round((sale.get("cost_price") or 0.0) / old_qty, 2) if old_qty > 0 else 0.0
            new_cost = round(cost_item * new_qty, 2)
            new_profit = round(new_total_price - new_cost, 2)

            await db.execute("""
                UPDATE leather_sales
                SET quantity = ?, price_per_item = ?, total_price = ?, cost_price = ?, profit = ?
                WHERE id = ?
            """, (new_qty, actual_pr_item, new_total_price, new_cost, new_profit, sale_id))

            async with db.execute("""
                SELECT id, total_amount, initial_paid, paid_amount FROM debts
                WHERE branch_id = ? AND category = 'leather' AND (item_details LIKE ? OR created_at = ?)
                ORDER BY id DESC LIMIT 1
            """, (s_branch, f"%{color}%", created_at)) as cur:
                d_row = await cur.fetchone()

            if d_row:
                d_id = d_row[0]
                d_paid = d_row[3]
                new_remaining = round(new_total_price - d_paid, 2)
                new_d_status = "paid" if new_remaining <= 0 else ("partial" if d_paid > 0 else "unpaid")
                item_desc = f"Teri ({color}): {new_qty} dona"
                await db.execute("""
                    UPDATE debts
                    SET total_amount = ?, remaining_amount = ?, status = ?, item_details = ?, updated_at = ?
                    WHERE id = ?
                """, (new_total_price, new_remaining, new_d_status, item_desc, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), d_id))
            else:
                async with db.execute("""
                    SELECT id FROM cashbox
                    WHERE branch_id = ? AND category = 'leather' AND operation_type = 'INCOME'
                      AND (created_at = ? OR amount = ?)
                    ORDER BY id DESC LIMIT 1
                """, (s_branch, created_at, old_tot)) as cur:
                    cb_row = await cur.fetchone()
                if cb_row:
                    await db.execute("UPDATE cashbox SET amount = ? WHERE id = ?", (new_total_price, cb_row[0]))
                    await _recalc_cashbox_balance(db, s_branch, 'leather')

            await db.commit()
            return {
                "success": True,
                "sale_id": sale_id,
                "category": category,
                "sold_length": new_qty,
                "area_m2": new_qty,
                "total_price": new_total_price,
                "cost_price": new_cost,
                "profit": new_profit,
                "message": f"Teri sotuvi muvaffaqiyatli tahrirlandi!"
            }

        elif category == 'branch3':
            async with db.execute("SELECT * FROM branch3_sales WHERE id = ?", (sale_id,)) as cur:
                row = await cur.fetchone()
            if not row:
                raise ValueError("3-Filial sotuvi topilmadi!")
            sale = dict(row)
            old_tot = sale["total_price"]
            created_at = sale["created_at"]
            width = sale.get("width") or 4.0
            new_area = round(width * new_length, 2)
            actual_pr_m2 = round(new_total_price / new_area, 2) if new_area > 0 else 0.0
            cost_pr = round((sale.get("cost_price") or 0.0) / (sale.get("area_m2") or 1.0), 2)
            new_cost = round(new_area * cost_pr, 2)
            new_profit = round(new_total_price - new_cost, 2)

            await db.execute("""
                UPDATE branch3_sales
                SET length = ?, area_m2 = ?, price_per_m2 = ?, total_price = ?, cost_price = ?, profit = ?
                WHERE id = ?
            """, (new_length, new_area, actual_pr_m2, new_total_price, new_cost, new_profit, sale_id))

            async with db.execute("""
                SELECT id FROM cashbox
                WHERE branch_id = 3 AND operation_type = 'INCOME'
                  AND (created_at = ? OR amount = ?)
                ORDER BY id DESC LIMIT 1
            """, (created_at, old_tot)) as cur:
                cb_row = await cur.fetchone()
            if cb_row:
                await db.execute("UPDATE cashbox SET amount = ? WHERE id = ?", (new_total_price, cb_row[0]))
                await _recalc_cashbox_balance(db, 3, 'carpet')

            await db.commit()
            return {
                "success": True,
                "sale_id": sale_id,
                "category": category,
                "sold_length": new_length,
                "area_m2": new_area,
                "total_price": new_total_price,
                "cost_price": new_cost,
                "profit": new_profit,
                "message": f"3-Filial sotuvi muvaffaqiyatli tahrirlandi!"
            }


# ==================== ESLATMALAR / BLOKNOT (IPHONE NOTES USLUBIDA) ====================

async def get_notes(branch_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if branch_id is not None and branch_id != 0:
            query = """
                SELECT * FROM notes 
                WHERE branch_id = ? 
                ORDER BY is_pinned DESC, updated_at DESC, id DESC
            """
            cursor = await db.execute(query, (branch_id,))
        else:
            query = """
                SELECT * FROM notes 
                ORDER BY is_pinned DESC, updated_at DESC, id DESC
            """
            cursor = await db.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_note_by_id(note_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def save_note(note_id=None, branch_id=1, user_id=None, author_name='', title='', content='', is_pinned=0, color='yellow'):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if note_id:
            await db.execute("""
                UPDATE notes 
                SET title = ?, content = ?, is_pinned = ?, color = ?, updated_at = ?,
                    author_name = CASE WHEN ? != '' THEN ? ELSE author_name END
                WHERE id = ?
            """, (title, content, is_pinned, color, now_str, author_name, author_name, note_id))
            await db.commit()
            cursor = await db.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
        else:
            cursor = await db.execute("""
                INSERT INTO notes (branch_id, user_id, author_name, title, content, is_pinned, color, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (branch_id, user_id, author_name, title, content, is_pinned, color, now_str, now_str))
            new_id = cursor.lastrowid
            await db.commit()
            cursor = await db.execute("SELECT * FROM notes WHERE id = ?", (new_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

async def delete_note(note_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        await db.commit()
        return True

async def toggle_pin_note(note_id: int):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT is_pinned FROM notes WHERE id = ?", (note_id,))
        row = await cursor.fetchone()
        if not row:
            return 0
        new_val = 0 if row[0] else 1
        await db.execute("UPDATE notes SET is_pinned = ?, updated_at = ? WHERE id = ?", (new_val, now_str, note_id))
        await db.commit()
        return new_val
