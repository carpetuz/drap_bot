import os
import aiosqlite
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime
from database.local_db import DB_PATH

async def generate_excel_report(file_path: str = "CRM_Hisobot.xlsx") -> str:
    wb = openpyxl.Workbook()
    
    # Stillar
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # 1. Ombor qoldig'i
        ws_ombor = wb.active
        ws_ombor.title = "Ombor Qoldig'i"
        
        headers_ombor = [
            "Rulon kodi", "Eni (m)", "Rangi", "Boshlang'ich metr", 
            "Qoldiq metr", "Maydon (m²)", "Tovar qiymati ($)", "Holati", "Kirim sanasi"
        ]
        ws_ombor.append(headers_ombor)
        
        async with db.execute("SELECT * FROM rolls ORDER BY id DESC") as cursor:
            rolls = await cursor.fetchall()
            for r in rolls:
                ws_ombor.append([
                    r["roll_code"], r["width"], r["color"], r["initial_length"],
                    r["current_length"], r["area_m2"], r["total_price"],
                    "Mavjud" if r["status"] == "active" and r["current_length"] > 0 else "Tugagan",
                    r["created_at"]
                ])
                
        # 2. Sotuvlar tarixi
        ws_sales = wb.create_sheet(title="Sotuvlar Tarixi")
        headers_sales = [
            "Sana va Vaqt", "Rulon kodi", "Mahsulot", "Sotilgan metr (m)", 
            "Maydoni (m²)", "Narx ($/m²)", "Jami summa ($)"
        ]
        ws_sales.append(headers_sales)
        
        async with db.execute("SELECT * FROM sales ORDER BY id DESC") as cursor:
            sales = await cursor.fetchall()
            for s in sales:
                ws_sales.append([
                    s["created_at"], s["roll_code"], f"{s['width']}x{s['sold_length']}m - {s['color']}",
                    s["sold_length"], s["area_m2"], s["price_per_m2"], s["total_price"]
                ])
                
        # 3. Kassa tarixi
        ws_cash = wb.create_sheet(title="Kassa Amallari")
        headers_cash = [
            "Sana va Vaqt", "Operatsiya turi", "Summa ($)", "Izoh", "Kassa qoldig'i ($)"
        ]
        ws_cash.append(headers_cash)
        
        async with db.execute("SELECT * FROM cashbox ORDER BY id DESC") as cursor:
            cash = await cursor.fetchall()
            for c in cash:
                ws_cash.append([
                    c["created_at"],
                    "Kirim (Sotuv)" if c["operation_type"] == "INCOME" else "Chiqim (Topshirildi)",
                    c["amount"], c["note"], c["balance_after"]
                ])

    # Varaqlarni formatlash
    for ws in [ws_ombor, ws_sales, ws_cash]:
        # Sarlavha qatori stili
        for col_num in range(1, ws.max_column + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            
        # Ma'lumot qatorlari
        for row in range(2, ws.max_row + 1):
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                if isinstance(cell.value, (int, float)):
                    cell.alignment = right_align
                else:
                    cell.alignment = left_align
                    
        # Ustun kengliklarini avtomatik to'g'irlash
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    wb.save(file_path)
    return file_path
