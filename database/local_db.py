import aiosqlite
from datetime import datetime
from config import PRICE_PER_M2, LEATHER_PRICE, BRANCH_NAMES, LEATHER_COLORS

DB_PATH = "data.db"

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
        
        # Xavfsiz avtomatik migratsiyalar
        for tbl in ["rolls", "sales", "cashbox"]:
            try:
                async with db.execute(f"PRAGMA table_info({tbl})") as cur:
                    cols = [row[1] for row in await cur.fetchall()]
                    if "branch_id" not in cols:
                        await db.execute(f"ALTER TABLE {tbl} ADD COLUMN branch_id INTEGER NOT NULL DEFAULT 1")
            except Exception:
                pass

        try:
            async with db.execute("PRAGMA table_info(cashbox)") as cur:
                cols = [row[1] for row in await cur.fetchall()]
                if "category" not in cols:
                    await db.execute("ALTER TABLE cashbox ADD COLUMN category TEXT NOT NULL DEFAULT 'carpet'")
        except Exception:
            pass
            
        await db.commit()

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
        cat_name = "Gilam" if category == "carpet" else "Teri"
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

# --- GILAM FUNKSIYALARI ---

async def add_roll(width: float, color: str, length: float, branch_id: int = 1, price_per_m2: float = PRICE_PER_M2) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    area_m2 = round(width * length, 2)
    total_price = round(area_m2 * price_per_m2, 2)
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT MAX(id) FROM rolls") as cursor:
            row = await cursor.fetchone()
            next_id = (row[0] or 0) + 1
            roll_code = f"#F{branch_id}-{1000 + next_id}"
        
        await db.execute("""
            INSERT INTO rolls (branch_id, roll_code, width, color, initial_length, current_length, area_m2, total_price, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
        """, (branch_id, roll_code, width, color, length, length, area_m2, total_price, created_at))
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
            query = "SELECT * FROM rolls WHERE branch_id = ? AND current_length > 0 AND status = 'active' ORDER BY width ASC, current_length DESC"
            params = (branch_id,)
        else:
            query = "SELECT * FROM rolls WHERE current_length > 0 AND status = 'active' ORDER BY branch_id ASC, width ASC, current_length DESC"
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

async def make_sale(roll_id: int, sold_length: float, branch_id: int = 1, price_per_m2: float = PRICE_PER_M2) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM rolls WHERE id = ? AND branch_id = ?", (roll_id, branch_id)) as cursor:
            roll = await cursor.fetchone()
            if not roll:
                raise ValueError("Rulon topilmadi yoki boshqa filialga tegishli!")
            
            if sold_length > roll["current_length"]:
                raise ValueError(f"Rulonda yetarli uzunlik yo'q! Mavjud qoldiq: {roll['current_length']} m")
        
        new_length = round(roll["current_length"] - sold_length, 2)
        new_area = round(roll["width"] * new_length, 2)
        new_total_price = round(new_area * price_per_m2, 2)
        new_status = "finished" if new_length <= 0 else "active"
        
        await db.execute("""
            UPDATE rolls 
            SET current_length = ?, area_m2 = ?, total_price = ?, status = ?
            WHERE id = ?
        """, (new_length, new_area, new_total_price, new_status, roll_id))
        
        sold_area = round(roll["width"] * sold_length, 2)
        sale_total_price = round(sold_area * price_per_m2, 2)
        
        async with db.execute("""
            INSERT INTO sales (branch_id, roll_id, roll_code, width, color, sold_length, area_m2, price_per_m2, total_price, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (branch_id, roll_id, roll["roll_code"], roll["width"], roll["color"], sold_length, sold_area, price_per_m2, sale_total_price, created_at)) as cursor:
            sale_id = cursor.lastrowid
        
        # Gilam kassasiga tushum
        current_balance = await get_cash_balance(branch_id=branch_id, category="carpet")
        new_balance = round(current_balance + sale_total_price, 2)
        await db.execute("""
            INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
            VALUES (?, 'carpet', 'INCOME', ?, ?, ?, ?)
        """, (branch_id, sale_total_price, f"Sotuv (Gilam): {roll['roll_code']} ({roll['width']}x{sold_length}m - {roll['color']})", new_balance, created_at))
        
        await db.commit()
        
        return {
            "sale_id": sale_id,
            "branch_id": branch_id,
            "roll_code": roll["roll_code"],
            "width": roll["width"],
            "color": roll["color"],
            "sold_length": sold_length,
            "sold_area": sold_area,
            "price_per_m2": price_per_m2,
            "sale_total_price": sale_total_price,
            "remaining_length": new_length,
            "created_at": created_at,
            "new_cash_balance": new_balance
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

async def make_leather_sale(color: str, quantity: int, branch_id: int = 1, price_per_item: float = LEATHER_PRICE) -> dict:
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
        
        sale_total_price = round(quantity * price_per_item, 2)
        async with db.execute("""
            INSERT INTO leather_sales (branch_id, color, quantity, price_per_item, total_price, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (branch_id, color, quantity, price_per_item, sale_total_price, created_at)) as cursor:
            sale_id = cursor.lastrowid
            
        # Teri kassasiga tushum
        current_balance = await get_cash_balance(branch_id=branch_id, category="leather")
        new_balance = round(current_balance + sale_total_price, 2)
        await db.execute("""
            INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
            VALUES (?, 'leather', 'INCOME', ?, ?, ?, ?)
        """, (branch_id, sale_total_price, f"Sotuv (Teri): {quantity} dona - {color}", new_balance, created_at))
        
        await db.commit()
        
    return {
        "sale_id": sale_id,
        "branch_id": branch_id,
        "color": color,
        "sold_quantity": quantity,
        "price_per_item": price_per_item,
        "sale_total_price": sale_total_price,
        "remaining_quantity": new_qty,
        "created_at": created_at,
        "new_leather_cash_balance": new_balance
    }

# --- DASHBOARD STATISTIKASI (IKKALA TOIFA ALOHIDA) ---

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

    carpet_cash = await get_cash_balance(branch_id=branch_id, category="carpet")
    leather_cash = await get_cash_balance(branch_id=branch_id, category="leather")

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
        "all_leather_rev": round(all_leather_rev, 2)
    }
