import os
import aiosqlite
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime
from database.local_db import DB_PATH
from config import BRANCH_NAMES

async def generate_excel_report(file_path: str = "CRM_Hisobot.xlsx", branch_id: int | None = None) -> str:
    wb = openpyxl.Workbook()
    
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    carpet_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid") # Moviy
    leather_fill = PatternFill(start_color="804000", end_color="804000", fill_type="solid") # Jigarrang
    kavralan_fill = PatternFill(start_color="0E6655", end_color="0E6655", fill_type="solid") # To'q yashil/Teal
    b3_fill = PatternFill(start_color="5B2C6F", end_color="5B2C6F", fill_type="solid")       # Binafsha
    cash_fill = PatternFill(start_color="274E13", end_color="274E13", fill_type="solid")    # Yashil
    debt_fill = PatternFill(start_color="78281F", end_color="78281F", fill_type="solid")    # To'q qizil
    
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"), right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"), bottom=Side(style="thin", color="D9D9D9")
    )
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    sheet_configs = []

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # --- AGAR FAQAT 3-FILIAL SO'RALSE ---
        if branch_id == 3:
            # 1. 3-Filial Sotuvlari
            ws_b3_sales = wb.active
            ws_b3_sales.title = "3-Filial Sotuvlari"
            headers_b3 = ["Filial", "Sana va Vaqt", "Mahsulot", "Eni (m)", "Uzunligi (m)", "Maydoni (m²)", "Narx ($/m²)", "Jami summa ($)", "To'lov turi"]
            ws_b3_sales.append(headers_b3)
            async with db.execute("SELECT * FROM branch3_sales WHERE branch_id = 3 ORDER BY id DESC") as cursor:
                for s in await cursor.fetchall():
                    ws_b3_sales.append([
                        "3-Filial", s["created_at"], s["collection_name"], s["width"], s["length"],
                        s["area_m2"], s["price_per_m2"], s["total_price"], "Naqd"
                    ])
            sheet_configs.append((ws_b3_sales, b3_fill))

            # 2. 3-Filial Kassasi
            ws_b3_cash = wb.create_sheet(title="3-Filial Kassasi")
            headers_b3_cash = ["Filial", "Sana va Vaqt", "Operatsiya", "Summa ($)", "Izoh", "Kassa qoldig'i ($)"]
            ws_b3_cash.append(headers_b3_cash)
            async with db.execute("SELECT * FROM cashbox WHERE branch_id = 3 AND category = 'branch3' ORDER BY id DESC") as cursor:
                for c in await cursor.fetchall():
                    ws_b3_cash.append([
                        "3-Filial", c["created_at"],
                        "Kirim (Sotuv)" if c["operation_type"] == "INCOME" else "Chiqim",
                        c["amount"], c["note"], c["balance_after"]
                    ])
            sheet_configs.append((ws_b3_cash, cash_fill))

        else:
            # --- 1-FILIAL, 2-FILIAL YOKI BARCHA FILIALLAR ---
            p = (branch_id,) if branch_id else ()

            # 1. Gilam Ombor Qoldig'i
            ws_c_ombor = wb.active
            ws_c_ombor.title = "Gilam Ombori"
            headers_c_ombor = ["Filial", "Rulon kodi", "Eni (m)", "Rangi", "Boshlang'ich metr", "Qoldiq metr", "Maydon (m²)", "Qiymati ($)", "Holati", "Kirim sanasi"]
            ws_c_ombor.append(headers_c_ombor)
            q = "SELECT * FROM rolls WHERE branch_id = ? ORDER BY id DESC" if branch_id else "SELECT * FROM rolls ORDER BY branch_id ASC, id DESC"
            async with db.execute(q, p) as cursor:
                for r in await cursor.fetchall():
                    b_name = BRANCH_NAMES.get(r["branch_id"], f"Filial-{r['branch_id']}")
                    ws_c_ombor.append([b_name, r["roll_code"], r["width"], r["color"], r["initial_length"], r["current_length"], r["area_m2"], r["total_price"], "Mavjud" if r["status"] == "active" and r["current_length"] > 0 else "Tugagan", r["created_at"]])
            sheet_configs.append((ws_c_ombor, carpet_fill))

            # 2. Teri Ombor Qoldig'i
            ws_l_ombor = wb.create_sheet(title="Teri Ombori")
            headers_l_ombor = ["Filial", "Mahsulot", "Rangi", "Qoldiq (dona)", "Narxi ($/dona)", "Jami qiymati ($)", "Oxirgi yangilanish"]
            ws_l_ombor.append(headers_l_ombor)
            q = "SELECT * FROM leather_inventory WHERE branch_id = ? ORDER BY color ASC" if branch_id else "SELECT * FROM leather_inventory ORDER BY branch_id ASC, color ASC"
            async with db.execute(q, p) as cursor:
                for l in await cursor.fetchall():
                    b_name = BRANCH_NAMES.get(l["branch_id"], f"Filial-{l['branch_id']}")
                    val = round(l["quantity"] * l["price_per_item"], 2)
                    ws_l_ombor.append([b_name, "Teri", l["color"], l["quantity"], l["price_per_item"], val, l["updated_at"]])
            sheet_configs.append((ws_l_ombor, leather_fill))

            # 3. Asl Kavralan Ombor Qoldig'i
            ws_k_ombor = wb.create_sheet(title="Kavralan Ombori")
            headers_k_ombor = ["Filial", "Rulon kodi", "Eni (m)", "Boshlang'ich metr", "Qoldiq metr", "Maydon (m²)", "Qiymati ($)", "Holati", "Kirim sanasi"]
            ws_k_ombor.append(headers_k_ombor)
            q = "SELECT * FROM kavralan_rolls WHERE branch_id = ? ORDER BY id DESC" if branch_id else "SELECT * FROM kavralan_rolls ORDER BY branch_id ASC, id DESC"
            async with db.execute(q, p) as cursor:
                for kr in await cursor.fetchall():
                    b_name = BRANCH_NAMES.get(kr["branch_id"], f"Filial-{kr['branch_id']}")
                    ws_k_ombor.append([b_name, kr["roll_code"], kr["width"], kr["initial_length"], kr["current_length"], kr["area_m2"], kr["total_price"], "Mavjud" if kr["status"] == "active" and kr["current_length"] > 0 else "Tugagan", kr["created_at"]])
            sheet_configs.append((ws_k_ombor, kavralan_fill))

            # 4. Gilam Sotuvlar Tarixi
            ws_c_sales = wb.create_sheet(title="Gilam Sotuvlari")
            headers_c_sales = ["Filial", "Sana va Vaqt", "Rulon kodi", "O'lchami va rangi", "Sotilgan metr", "Maydoni (m²)", "Narx ($/m²)", "Jami summa ($)"]
            ws_c_sales.append(headers_c_sales)
            q = "SELECT * FROM sales WHERE branch_id = ? ORDER BY id DESC" if branch_id else "SELECT * FROM sales ORDER BY branch_id ASC, id DESC"
            async with db.execute(q, p) as cursor:
                for s in await cursor.fetchall():
                    b_name = BRANCH_NAMES.get(s["branch_id"], f"Filial-{s['branch_id']}")
                    ws_c_sales.append([b_name, s["created_at"], s["roll_code"], f"{s['width']}x{s['sold_length']}m - {s['color']}", s["sold_length"], s["area_m2"], s["price_per_m2"], s["total_price"]])
            sheet_configs.append((ws_c_sales, carpet_fill))

            # 5. Teri Sotuvlar Tarixi
            ws_l_sales = wb.create_sheet(title="Teri Sotuvlari")
            headers_l_sales = ["Filial", "Sana va Vaqt", "Mahsulot", "Rangi", "Sotilgan dona", "Narx ($/dona)", "Jami summa ($)"]
            ws_l_sales.append(headers_l_sales)
            q = "SELECT * FROM leather_sales WHERE branch_id = ? ORDER BY id DESC" if branch_id else "SELECT * FROM leather_sales ORDER BY branch_id ASC, id DESC"
            async with db.execute(q, p) as cursor:
                for ls in await cursor.fetchall():
                    b_name = BRANCH_NAMES.get(ls["branch_id"], f"Filial-{ls['branch_id']}")
                    ws_l_sales.append([b_name, ls["created_at"], "Teri", ls["color"], ls["quantity"], ls["price_per_item"], ls["total_price"]])
            sheet_configs.append((ws_l_sales, leather_fill))

            # 6. Asl Kavralan Sotuvlar Tarixi
            ws_k_sales = wb.create_sheet(title="Kavralan Sotuvlari")
            headers_k_sales = ["Filial", "Sana va Vaqt", "Rulon kodi", "O'lchami", "Sotilgan metr", "Maydoni (m²)", "Narx ($/m²)", "Jami summa ($)"]
            ws_k_sales.append(headers_k_sales)
            q = "SELECT * FROM kavralan_sales WHERE branch_id = ? ORDER BY id DESC" if branch_id else "SELECT * FROM kavralan_sales ORDER BY branch_id ASC, id DESC"
            async with db.execute(q, p) as cursor:
                for ks in await cursor.fetchall():
                    b_name = BRANCH_NAMES.get(ks["branch_id"], f"Filial-{ks['branch_id']}")
                    ws_k_sales.append([b_name, ks["created_at"], ks["roll_code"], f"{ks['width']}x{ks['sold_length']}m", ks["sold_length"], ks["area_m2"], ks["price_per_m2"], ks["total_price"]])
            sheet_configs.append((ws_k_sales, kavralan_fill))

            # 7. 3-Filial Sotuvlari (Umumiy hisobotda)
            if branch_id is None:
                ws_b3_all = wb.create_sheet(title="3-Filial Sotuvlari")
                headers_b3_all = ["Filial", "Sana va Vaqt", "Mahsulot", "Eni (m)", "Uzunligi (m)", "Maydoni (m²)", "Narx ($/m²)", "Jami summa ($)", "To'lov turi"]
                ws_b3_all.append(headers_b3_all)
                async with db.execute("SELECT * FROM branch3_sales ORDER BY id DESC") as cursor:
                    for s in await cursor.fetchall():
                        ws_b3_all.append([
                            "3-Filial", s["created_at"], s["collection_name"], s["width"], s["length"],
                            s["area_m2"], s["price_per_m2"], s["total_price"], "Naqd"
                        ])
                sheet_configs.append((ws_b3_all, b3_fill))

            # 8. Gilam Kassasi Harakatlari
            ws_c_cash = wb.create_sheet(title="Gilam Kassasi")
            headers_c_cash = ["Filial", "Sana va Vaqt", "Operatsiya", "Summa ($)", "Izoh", "Kassa qoldig'i ($)"]
            ws_c_cash.append(headers_c_cash)
            q = "SELECT * FROM cashbox WHERE branch_id = ? AND category = 'carpet' ORDER BY id DESC" if branch_id else "SELECT * FROM cashbox WHERE category = 'carpet' ORDER BY branch_id ASC, id DESC"
            async with db.execute(q, p) as cursor:
                for c in await cursor.fetchall():
                    b_name = BRANCH_NAMES.get(c["branch_id"], f"Filial-{c['branch_id']}")
                    ws_c_cash.append([b_name, c["created_at"], "Kirim (Sotuv)" if c["operation_type"] == "INCOME" else "Chiqim (Topshirildi)", c["amount"], c["note"], c["balance_after"]])
            sheet_configs.append((ws_c_cash, cash_fill))

            # 9. Teri Kassasi Harakatlari
            ws_l_cash = wb.create_sheet(title="Teri Kassasi")
            headers_l_cash = ["Filial", "Sana va Vaqt", "Operatsiya", "Summa ($)", "Izoh", "Kassa qoldig'i ($)"]
            ws_l_cash.append(headers_l_cash)
            q = "SELECT * FROM cashbox WHERE branch_id = ? AND category = 'leather' ORDER BY id DESC" if branch_id else "SELECT * FROM cashbox WHERE category = 'leather' ORDER BY branch_id ASC, id DESC"
            async with db.execute(q, p) as cursor:
                for c in await cursor.fetchall():
                    b_name = BRANCH_NAMES.get(c["branch_id"], f"Filial-{c['branch_id']}")
                    ws_l_cash.append([b_name, c["created_at"], "Kirim (Sotuv)" if c["operation_type"] == "INCOME" else "Chiqim (Topshirildi)", c["amount"], c["note"], c["balance_after"]])
            sheet_configs.append((ws_l_cash, cash_fill))

            # 10. Kavralan Kassasi Harakatlari
            ws_k_cash = wb.create_sheet(title="Kavralan Kassasi")
            headers_k_cash = ["Filial", "Sana va Vaqt", "Operatsiya", "Summa ($)", "Izoh", "Kassa qoldig'i ($)"]
            ws_k_cash.append(headers_k_cash)
            q = "SELECT * FROM cashbox WHERE branch_id = ? AND category = 'kavralan' ORDER BY id DESC" if branch_id else "SELECT * FROM cashbox WHERE category = 'kavralan' ORDER BY branch_id ASC, id DESC"
            async with db.execute(q, p) as cursor:
                for c in await cursor.fetchall():
                    b_name = BRANCH_NAMES.get(c["branch_id"], f"Filial-{c['branch_id']}")
                    ws_k_cash.append([b_name, c["created_at"], "Kirim (Sotuv)" if c["operation_type"] == "INCOME" else "Chiqim (Topshirildi)", c["amount"], c["note"], c["balance_after"]])
            sheet_configs.append((ws_k_cash, cash_fill))

            # 11. 3-Filial Kassasi (Umumiy hisobotda)
            if branch_id is None:
                ws_b3_cash_all = wb.create_sheet(title="3-Filial Kassasi")
                headers_b3_cash_all = ["Filial", "Sana va Vaqt", "Operatsiya", "Summa ($)", "Izoh", "Kassa qoldig'i ($)"]
                ws_b3_cash_all.append(headers_b3_cash_all)
                async with db.execute("SELECT * FROM cashbox WHERE branch_id = 3 AND category = 'branch3' ORDER BY id DESC") as cursor:
                    for c in await cursor.fetchall():
                        ws_b3_cash_all.append([
                            "3-Filial", c["created_at"],
                            "Kirim (Sotuv)" if c["operation_type"] == "INCOME" else "Chiqim",
                            c["amount"], c["note"], c["balance_after"]
                        ])
                sheet_configs.append((ws_b3_cash_all, cash_fill))

            # 12. Nasiyalar (Qarzlar) Daftari
            ws_debts = wb.create_sheet(title="Nasiyalar (Qarzlar)")
            headers_debts = ["Filial", "Nasiya ID", "Mijoz Ismi", "Telefon", "Tovar turi", "Mahsulot tavsifi", "Jami summa ($)", "Boshlang'ich ($)", "To'langan ($)", "Qarz qoldig'i ($)", "Holati", "Berilgan sana", "Oxirgi yangilanish"]
            ws_debts.append(headers_debts)
            q = "SELECT * FROM debts WHERE branch_id = ? ORDER BY id DESC" if branch_id else "SELECT * FROM debts ORDER BY branch_id ASC, id DESC"
            async with db.execute(q, p) as cursor:
                for d in await cursor.fetchall():
                    b_name = BRANCH_NAMES.get(d["branch_id"], f"Filial-{d['branch_id']}")
                    cat_name = "Gilam" if d["category"] == "carpet" else ("Teri" if d["category"] == "leather" else "Kavralan")
                    status_text = "To'liq yopilgan" if d["status"] == "paid" else ("Qisman to'langan" if d["status"] == "partial" else "To'lanmagan")
                    ws_debts.append([
                        b_name,
                        f"#D-{d['id']}",
                        d["customer_name"],
                        d["customer_phone"] or "-",
                        cat_name,
                        d["item_details"],
                        d["total_amount"],
                        d["initial_paid"],
                        d["paid_amount"],
                        d["remaining_amount"],
                        status_text,
                        d["created_at"],
                        d["updated_at"]
                    ])
            sheet_configs.append((ws_debts, debt_fill))

    # Stillar va formatlash
    for ws, fill in sheet_configs:
        for col_num in range(1, ws.max_column + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = fill
            cell.alignment = center_align
            
        for row in range(2, ws.max_row + 1):
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                if isinstance(cell.value, (int, float)):
                    cell.alignment = right_align
                else:
                    cell.alignment = left_align
                    
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    wb.save(file_path)
    return file_path
