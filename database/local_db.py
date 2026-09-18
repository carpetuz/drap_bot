import aiosqlite
from datetime import datetime
from config import PRICE_PER_M2, BRANCH_NAMES

DB_PATH = "data.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cashbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL DEFAULT 1,
                operation_type TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                balance_after REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()

async def get_cash_balance(branch_id: int | None = None) -> float:
    async with aiosqlite.connect(DB_PATH) as db:
        if branch_id is not None:
            async with db.execute(
                "SELECT balance_after FROM cashbox WHERE branch_id = ? ORDER BY id DESC LIMIT 1", 
                (branch_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return round(row[0], 2) if row else 0.0
        else:
            # Barcha filiallar umumiy kassa yig'indisi
            total = 0.0
            for b_id in BRANCH_NAMES.keys():
                async with db.execute(
                    "SELECT balance_after FROM cashbox WHERE branch_id = ? ORDER BY id DESC LIMIT 1", 
                    (b_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        total += row[0]
            return round(total, 2)

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
        
        current_balance = await get_cash_balance(branch_id=branch_id)
        new_balance = round(current_balance + sale_total_price, 2)
        await db.execute("""
            INSERT INTO cashbox (branch_id, operation_type, amount, note, balance_after, created_at)
            VALUES (?, 'INCOME', ?, ?, ?, ?)
        """, (branch_id, sale_total_price, f"Sotuv: {roll['roll_code']} ({roll['width']}x{sold_length}m - {roll['color']})", new_balance, created_at))
        
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

async def withdraw_cash(amount: float, branch_id: int = 1, note: str = "Kassa topshirildi") -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_balance = await get_cash_balance(branch_id=branch_id)
    
    if amount <= 0:
        raise ValueError("Chiqim summasi 0 dan katta bo'lishi kerak!")
    if amount > current_balance:
        raise ValueError(f"Kassada yetarli mablag' yo'q! Mavjud: ${current_balance:.2f}")
        
    new_balance = round(current_balance - amount, 2)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO cashbox (branch_id, operation_type, amount, note, balance_after, created_at)
            VALUES (?, 'WITHDRAWAL', ?, ?, ?, ?)
        """, (branch_id, amount, note, new_balance, created_at))
        await db.commit()
        
    return {
        "amount": amount,
        "branch_id": branch_id,
        "old_balance": current_balance,
        "new_balance": new_balance,
        "note": note,
        "created_at": created_at
    }

async def get_dashboard_stats(branch_id: int | None = None) -> dict:
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    async with aiosqlite.connect(DB_PATH) as db:
        if branch_id is not None:
            # Bitta filial
            async with db.execute("""
                SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0)
                FROM rolls
                WHERE branch_id = ? AND status = 'active' AND current_length > 0
            """, (branch_id,)) as cursor:
                stock_count, total_stock_area, total_stock_value = await cursor.fetchone()
                
            async with db.execute("""
                SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0)
                FROM sales
                WHERE branch_id = ? AND created_at LIKE ?
            """, (branch_id, f"{today_str}%")) as cursor:
                today_sales_count, today_sold_area, today_revenue = await cursor.fetchone()
                
            async with db.execute("""
                SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0)
                FROM sales
                WHERE branch_id = ?
            """, (branch_id,)) as cursor:
                all_sales_count, all_sold_area, all_revenue = await cursor.fetchone()

            cash_balance = await get_cash_balance(branch_id=branch_id)
        else:
            # Barcha filiallar
            async with db.execute("""
                SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0)
                FROM rolls
                WHERE status = 'active' AND current_length > 0
            """) as cursor:
                stock_count, total_stock_area, total_stock_value = await cursor.fetchone()
                
            async with db.execute("""
                SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0)
                FROM sales
                WHERE created_at LIKE ?
            """, (f"{today_str}%",)) as cursor:
                today_sales_count, today_sold_area, today_revenue = await cursor.fetchone()
                
            async with db.execute("""
                SELECT COUNT(*), COALESCE(SUM(area_m2), 0), COALESCE(SUM(total_price), 0)
                FROM sales
            """) as cursor:
                all_sales_count, all_sold_area, all_revenue = await cursor.fetchone()

            cash_balance = await get_cash_balance(branch_id=None)

    return {
        "branch_id": branch_id,
        "stock_rolls_count": stock_count,
        "stock_total_m2": round(total_stock_area, 2),
        "stock_total_value": round(total_stock_value, 2),
        "cash_balance": round(cash_balance, 2),
        "today_sales_count": today_sales_count,
        "today_sold_m2": round(today_sold_area, 2),
        "today_revenue": round(today_revenue, 2),
        "all_sales_count": all_sales_count,
        "all_sold_m2": round(all_sold_area, 2),
        "all_revenue": round(all_revenue, 2),
    }
