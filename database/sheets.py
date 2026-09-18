import os
import logging
import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_SHEET_ID, GOOGLE_CREDS_FILE, PRICE_PER_M2

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

class GoogleSheetsManager:
    def __init__(self):
        self.client = None
        self.sheet = None
        self.is_connected = False
        self._init_client()

    def _init_client(self):
        if not GOOGLE_SHEET_ID:
            logger.info("GOOGLE_SHEET_ID sozlanmagan. Google Sheets vaqtinchalik o'chiq.")
            return

        if not os.path.exists(GOOGLE_CREDS_FILE):
            logger.info(f"{GOOGLE_CREDS_FILE} topilmadi. Google Sheets vaqtinchalik o'chiq.")
            return

        try:
            creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=SCOPES)
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(GOOGLE_SHEET_ID)
            self._ensure_worksheets()
            self.is_connected = True
            logger.info("Google Sheets muvaffaqiyatli ulandi!")
        except Exception as e:
            logger.error(f"Google Sheets ulanishida xatolik: {e}")
            self.is_connected = False

    def _ensure_worksheets(self):
        # 1. Ombor varag'i
        try:
            ws_ombor = self.sheet.worksheet("Ombor")
        except gspread.WorksheetNotFound:
            ws_ombor = self.sheet.add_worksheet(title="Ombor", rows="500", cols="10")
            ws_ombor.append_row([
                "Rulon ID", "Eni (m)", "Rangi", "Boshlang'ich uzunlik (m)", 
                "Qoldiq (m)", "Maydon (m²)", "Qiymati ($)", "Holati", "Kirim sanasi"
            ])

        # 2. Sotuvlar varag'i
        try:
            ws_sales = self.sheet.worksheet("Sotuvlar")
        except gspread.WorksheetNotFound:
            ws_sales = self.sheet.add_worksheet(title="Sotuvlar", rows="1000", cols="10")
            ws_sales.append_row([
                "Sana va Vaqt", "Rulon ID", "Mahsulot", "Sotilgan metr (m)", 
                "Sotilgan maydon (m²)", "Narx ($/m²)", "Jami summa ($)"
            ])

        # 3. Kassa varag'i
        try:
            ws_kassa = self.sheet.worksheet("Kassa")
        except gspread.WorksheetNotFound:
            ws_kassa = self.sheet.add_worksheet(title="Kassa", rows="1000", cols="10")
            ws_kassa.append_row([
                "Sana va Vaqt", "Operatsiya turi", "Summa ($)", "Izoh", "Kassa balansi ($)"
            ])

    def add_roll(self, roll: dict):
        if not self.is_connected:
            return
        try:
            ws = self.sheet.worksheet("Ombor")
            ws.append_row([
                roll["roll_code"],
                roll["width"],
                roll["color"],
                roll["initial_length"],
                roll["current_length"],
                roll["area_m2"],
                roll["total_price"],
                roll.get("status", "active"),
                roll["created_at"]
            ])
        except Exception as e:
            logger.error(f"Google Sheetsga rulon qo'shishda xatolik: {e}")

    def update_roll_balance(self, roll_code: str, new_length: float, new_area: float, new_price: float, status: str):
        if not self.is_connected:
            return
        try:
            ws = self.sheet.worksheet("Ombor")
            cell = ws.find(roll_code)
            if cell:
                row = cell.row
                ws.update_cell(row, 5, new_length)   # Qoldiq (m)
                ws.update_cell(row, 6, new_area)     # Maydon (m²)
                ws.update_cell(row, 7, new_price)    # Qiymati ($)
                ws.update_cell(row, 8, status)       # Holati
        except Exception as e:
            logger.error(f"Google Sheetsda rulon yangilashda xatolik: {e}")

    def add_sale(self, sale: dict):
        if not self.is_connected:
            return
        try:
            ws = self.sheet.worksheet("Sotuvlar")
            ws.append_row([
                sale["created_at"],
                sale["roll_code"],
                f"{sale['width']}x{sale['sold_length']}m - {sale['color']}",
                sale["sold_length"],
                sale["sold_area"],
                sale["price_per_m2"],
                sale["sale_total_price"]
            ])
        except Exception as e:
            logger.error(f"Google Sheetsga sotuv yozishda xatolik: {e}")

    def add_cash_operation(self, op_type: str, amount: float, note: str, balance: float, created_at: str):
        if not self.is_connected:
            return
        try:
            ws = self.sheet.worksheet("Kassa")
            ws.append_row([
                created_at,
                "Kirim" if op_type == "INCOME" else "Chiqim (Topshirildi)",
                amount,
                note,
                balance
            ])
        except Exception as e:
            logger.error(f"Google Sheetsga kassa yozishda xatolik: {e}")

sheets_manager = GoogleSheetsManager()
