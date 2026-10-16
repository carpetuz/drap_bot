import aiosqlite
from datetime import datetime
from config import PRICE_PER_M2, LEATHER_PRICE, BRANCH_NAMES, LEATHER_COLORS, KAVRALAN_PRICE, KAVRALAN_WIDTH, BRANCH3_WIDTH, BRANCH3_COLLECTIONS

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

async def update_kavralan_roll(roll_id: int, current_length: float, price_per_m2: float) -> dict:
    area_m2 = round(4.0 * current_length, 2)
    total_price = round(area_m2 * price_per_m2, 2)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE kavralan_rolls
            SET current_length = ?, area_m2 = ?, total_price = ?
            WHERE id = ?
        """, (current_length, area_m2, total_price, roll_id))
        await db.commit()
    return {"success": True, "roll_id": roll_id, "current_length": current_length, "area_m2": area_m2, "total_price": total_price}

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
    initial_paid: float = 0.0
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
            
            item_desc = f"{roll['roll_code']} ({roll['width']:g}x{sold_length}m - {roll['color']})"
            async with db.execute("""
                INSERT INTO debts (branch_id, category, customer_name, customer_phone, item_details, total_amount, initial_paid, paid_amount, remaining_amount, status, created_at, updated_at)
                VALUES (?, 'carpet', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (branch_id, customer_name, customer_phone, item_desc, sale_total_price, initial_paid, initial_paid, remaining_amount, debt_status, created_at, created_at)) as cursor:
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
    initial_paid: float = 0.0
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
                INSERT INTO debts (branch_id, category, customer_name, customer_phone, item_details, total_amount, initial_paid, paid_amount, remaining_amount, status, created_at, updated_at)
                VALUES (?, 'leather', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (branch_id, customer_name, customer_phone, item_desc, sale_total_price, initial_paid, initial_paid, remaining_amount, debt_status, created_at, created_at)) as cursor:
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

async def add_kavralan_roll(length: float, branch_id: int = 1, price_per_m2: float = KAVRALAN_PRICE) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    width = KAVRALAN_WIDTH
    area_m2 = round(width * length, 2)
    total_price = round(area_m2 * price_per_m2, 2)
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT MAX(id) FROM kavralan_rolls") as cursor:
            row = await cursor.fetchone()
            next_id = (row[0] or 0) + 1001
            
        roll_code = f"#K{branch_id}-{next_id}"
        
        await db.execute("""
            INSERT INTO kavralan_rolls (branch_id, roll_code, width, initial_length, current_length, area_m2, total_price, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
        """, (branch_id, roll_code, width, length, length, area_m2, total_price, created_at))
        await db.commit()
        
        return {
            "id": next_id,
            "branch_id": branch_id,
            "roll_code": roll_code,
            "width": width,
            "initial_length": length,
            "current_length": length,
            "area_m2": area_m2,
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
    initial_paid: float = 0.0
) -> dict:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    width = KAVRALAN_WIDTH
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM kavralan_rolls WHERE id = ? AND branch_id = ?", (roll_id, branch_id)) as cursor:
            roll = await cursor.fetchone()
            if not roll:
                raise ValueError("Kavralan ruloni topilmadi yoki boshqa filialga tegishli!")
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
            
        cost_price = round(sold_area * KAVRALAN_PRICE, 2)
        profit = round(sale_total_price - cost_price, 2)
        
        async with db.execute("""
            INSERT INTO kavralan_sales (branch_id, roll_id, roll_code, width, sold_length, area_m2, price_per_m2, total_price, cost_price, profit, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (branch_id, roll_id, roll["roll_code"], width, sold_length, sold_area, actual_price_per_m2, sale_total_price, cost_price, profit, created_at)) as cursor:
            sale_id = cursor.lastrowid
            
        debt_id = None
        if is_debt:
            initial_paid = round(float(initial_paid), 2)
            remaining_amount = round(sale_total_price - initial_paid, 2)
            debt_status = "partial" if initial_paid > 0 else "unpaid"
            
            item_desc = f"Kavralan: {roll['roll_code']} (4x{sold_length}m = {sold_area} m²)"
            async with db.execute("""
                INSERT INTO debts (branch_id, category, customer_name, customer_phone, item_details, total_amount, initial_paid, paid_amount, remaining_amount, status, created_at, updated_at)
                VALUES (?, 'kavralan', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (branch_id, customer_name, customer_phone, item_desc, sale_total_price, initial_paid, initial_paid, remaining_amount, debt_status, created_at, created_at)) as cursor:
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

async def pay_debt(debt_id: int, payment_amount: float, branch_id: int, note: str = "") -> dict:
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
        
        # Qarz to'lovlari tarixiga kiritish
        await db.execute("""
            INSERT INTO debt_payments (debt_id, branch_id, category, amount, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (debt_id, debt["branch_id"], debt["category"], payment_amount, note or "Qarz to'lovi", created_at))
        
        # Tegishli tovar kassasiga kirim qilish
        current_balance = await get_cash_balance(branch_id=debt["branch_id"], category=debt["category"])
        new_balance = round(current_balance + payment_amount, 2)
        cat_title = "Gilam" if debt["category"] == "carpet" else ("Teri" if debt["category"] == "leather" else "Kavralan")
        await db.execute("""
            INSERT INTO cashbox (branch_id, category, operation_type, amount, note, balance_after, created_at)
            VALUES (?, ?, 'INCOME', ?, ?, ?, ?)
        """, (debt["branch_id"], debt["category"], payment_amount, f"Qarz to'lovi ({cat_title}): {debt['customer_name']} (#{debt_id})", new_balance, created_at))
        
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
            "new_cash_balance": new_balance,
            "created_at": created_at
        }

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

async def make_branch3_sale(collection_name: str, length: float, branch_id: int = 3) -> dict:
    if collection_name not in BRANCH3_COLLECTIONS:
        raise ValueError(f"Noto'g'ri mahsulot tanlandi: {collection_name}")
    length = round(float(length), 2)
    if length <= 0:
        raise ValueError("Uzunlik 0 dan katta bo'lishi kerak!")

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
    period: str = "today",
    date_from: str | None = None,
    date_to: str | None = None
) -> dict:
    """
    period: 'today', 'week', 'month', 'all', 'custom'
    branch_id: None for all branches (SuperAdmin) or specific branch ID (1=Labzak, 2=Kartal, 3=3-Filial)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Sana sharti
        date_cond = ""
        date_params = []
        if period == "today":
            date_cond = "date(created_at) = date('now', 'localtime')"
        elif period == "week":
            date_cond = "date(created_at) >= date('now', 'localtime', '-6 days')"
        elif period == "month":
            date_cond = "date(created_at) >= date('now', 'localtime', '-29 days')"
        elif period == "custom" and date_from:
            if date_to:
                date_cond = "created_at >= ? AND created_at <= ?"
                date_params = [f"{date_from} 00:00:00", f"{date_to} 23:59:59"]
            else:
                date_cond = "created_at >= ?"
                date_params = [f"{date_from} 00:00:00"]
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
                    id, branch_id, 'carpet' as category, ('Rezinka Gilam ' || roll_code || ' (' || color || ')') as title,
                    sold_length, area_m2, price_per_m2, total_price, 
                    COALESCE(cost_price, 0.0) as cost_price, 
                    COALESCE(profit, (total_price - COALESCE(cost_price, 0.0))) as profit,
                    created_at
                FROM sales
                UNION ALL
                SELECT
                    id, branch_id, 'leather' as category, ('Teri (' || color || ')') as title,
                    quantity as sold_length, quantity as area_m2, price_per_item as price_per_m2, total_price,
                    COALESCE(cost_price, 0.0) as cost_price,
                    COALESCE(profit, (total_price - COALESCE(cost_price, 0.0))) as profit,
                    created_at
                FROM leather_sales
                UNION ALL
                SELECT
                    id, branch_id, 'kavralan' as category, ('Asl Kavralan ' || roll_code) as title,
                    sold_length, area_m2, price_per_m2, total_price,
                    COALESCE(cost_price, 0.0) as cost_price,
                    COALESCE(profit, (total_price - COALESCE(cost_price, 0.0))) as profit,
                    created_at
                FROM kavralan_sales
                UNION ALL
                SELECT
                    id, branch_id, 'branch3' as category, ('3-Filial ' || collection_name) as title,
                    length as sold_length, area_m2, price_per_m2, total_price,
                    COALESCE(cost_price, 0.0) as cost_price,
                    COALESCE(profit, (total_price - COALESCE(cost_price, 0.0))) as profit,
                    created_at
                FROM branch3_sales
            ) AS combined_sales
            {where_clause}
            ORDER BY created_at DESC
        """

        async with db.execute(sales_query, all_params) as cur:
            sales_rows = [dict(r) for r in await cur.fetchall()]

        # 2. Xarajatlar (Rasxod)
        expenses_query = f"""
            SELECT id, branch_id, category, operation_type, amount, note, balance_after, created_at
            FROM cashbox
            WHERE operation_type = 'EXPENSE' AND ({date_cond}) AND ({branch_cond})
            ORDER BY created_at DESC
        """
        async with db.execute(expenses_query, all_params) as cur:
            expenses_rows = [dict(r) for r in await cur.fetchall()]

        # KPI Hisoblash
        total_revenue = round(sum(s["total_price"] for s in sales_rows), 2)
        total_cost = round(sum(s["cost_price"] for s in sales_rows), 2)
        gross_profit = round(sum(s["profit"] for s in sales_rows), 2)
        total_expenses = round(sum(e["amount"] for e in expenses_rows), 2)
        net_profit = round(gross_profit - total_expenses, 2)
        
        # Filiallar bo'yicha guruhlash (SuperAdmin uchun)
        by_branch = {}
        for bid, bname in BRANCH_NAMES.items():
            b_sales = [s for s in sales_rows if s["branch_id"] == bid]
            b_expenses = [e for e in expenses_rows if e["branch_id"] == bid]
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

        return {
            "period": period,
            "branch_id": branch_id,
            "summary": {
                "total_revenue": total_revenue,
                "total_cost": total_cost,
                "gross_profit": gross_profit,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "sales_count": len(sales_rows),
                "expenses_count": len(expenses_rows)
            },
            "by_branch": by_branch,
            "sales": sales_rows,
            "expenses": expenses_rows
        }

