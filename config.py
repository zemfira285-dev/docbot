import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ====================== ДАННЫЕ ВАШЕГО ИП (заполните один раз) ======================
IP_DATA = {
    "name": "ИП Иванов Иван Иванович",                     # Полное название ИП
    "iin": "123456789012",                                # ИИН ИП
    "address": "г. Алматы, ул. Примерная, д. 1, кв. 1",  # Адрес
    "phone": "+7 700 123 45 67",                         # Телефон
    "bank": "АО «Kaspi Bank»",                           # Банк
    "iik": "KZ123456789012345678",                       # ИИК
    "bik": "CASPKZKA",                                   # БИК
    "city": "Алматы",                                    # Город по умолчанию
}

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Исправлено: сохраняем базу данных в корень проекта, куда у приложения есть права на запись
DB_PATH = os.path.join(BASE_DIR, "clients.db")

# Печать и подпись (положите файлы stamp.png и signature.png в папку assets)
STAMP_PATH = os.path.join(ASSETS_DIR, "stamp.png")
SIGNATURE_PATH = os.path.join(ASSETS_DIR, "signature.png")