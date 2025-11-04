import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Tuya API credentials
CLIENT_ID = os.getenv("TUYA_CLIENT_ID")
CLIENT_SECRET = os.getenv("TUYA_CLIENT_SECRET")
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")
TUYA_REGION = os.getenv("TUYA_REGION", "eu")

# Проверка обязательных переменных
required_vars = {
    "TUYA_CLIENT_ID": CLIENT_ID,
    "TUYA_CLIENT_SECRET": CLIENT_SECRET,
    "TUYA_DEVICE_ID": DEVICE_ID
}

missing_vars = []
for var_name, var_value in required_vars.items():
    if not var_value:
        missing_vars.append(var_name)

if missing_vars:
    raise ValueError(f"Следующие переменные не установлены в .env файле: {', '.join(missing_vars)}")

print(f"✅ Конфигурация загружена: DEVICE_ID={DEVICE_ID}, REGION={TUYA_REGION}")
