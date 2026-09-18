import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
ADMIN_IDS_RAW = os.getenv('ADMIN_IDS', '8350493371').split(',')
ADMIN_IDS = [int(i.strip()) for i in ADMIN_IDS_RAW if i.strip().isdigit()]

PRICE_PER_M2 = float(os.getenv('PRICE_PER_M2', '8.0'))
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '').strip()
GOOGLE_CREDS_FILE = os.getenv('GOOGLE_CREDS_FILE', 'service_account.json').strip()

# Mahsulot parametrlari
AVAILABLE_WIDTHS = [0.8, 1.0, 1.2, 1.6, 2.0]
AVAILABLE_COLORS = [
    'Seriy',
    'Kofe',
    'Qizil',
    'Bordo',
    'Qora',
    'Yashil',
    'Kok'
]
