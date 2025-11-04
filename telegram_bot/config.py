# telegram_bot/config.py
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройки Telegram бота
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Настройки API
FINGERBOT_API_URL = os.getenv("FINGERBOT_API_URL", "http://localhost:5001")

# Проверка обязательных переменных
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env файле")
