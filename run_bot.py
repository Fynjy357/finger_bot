import subprocess
import threading
import time
import sys
import os

def get_project_root():
    """Получение корневой директории проекта"""
    return os.path.dirname(os.path.abspath(__file__))

def run_api():
    """Запуск FingerBot API"""
    print("🚀 Запуск FingerBot API...")
    project_root = get_project_root()
    api_dir = os.path.join(project_root, "fingerbot_api")
    
    if not os.path.exists(api_dir):
        print(f"❌ Папка fingerbot_api не найдена: {api_dir}")
        return
    
    os.chdir(api_dir)
    print(f"📁 Рабочая директория API: {os.getcwd()}")
    subprocess.run([sys.executable, "app.py"])

def run_telegram_bot():
    """Запуск Telegram бота"""
    time.sleep(3)  # Даем API время запуститься
    print("🤖 Запуск Telegram бота на aiogram...")
    project_root = get_project_root()
    bot_dir = os.path.join(project_root, "telegram_bot")
    
    if not os.path.exists(bot_dir):
        print(f"❌ Папка telegram_bot не найдена: {bot_dir}")
        return
    
    os.chdir(bot_dir)
    print(f"📁 Рабочая директория бота: {os.getcwd()}")
    subprocess.run([sys.executable, "bot.py"])

if __name__ == "__main__":
    # Сохраняем текущую директорию
    original_dir = os.getcwd()
    project_root = get_project_root()
    
    print(f"📂 Корневая директория проекта: {project_root}")
    
    # Проверяем структуру папок
    print("🔍 Проверка структуры проекта...")
    api_exists = os.path.exists(os.path.join(project_root, "fingerbot_api"))
    bot_exists = os.path.exists(os.path.join(project_root, "telegram_bot"))
    
    print(f"   fingerbot_api: {'✅' if api_exists else '❌'}")
    print(f"   telegram_bot: {'✅' if bot_exists else '❌'}")
    
    if not api_exists or not bot_exists:
        print("❌ Не найдены необходимые папки. Проверьте структуру проекта.")
        sys.exit(1)
    
    try:
        # Запускаем в отдельных потоках
        api_thread = threading.Thread(target=run_api)
        bot_thread = threading.Thread(target=run_telegram_bot)
        
        api_thread.start()
        bot_thread.start()
        
        api_thread.join()
        bot_thread.join()
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервисов...")
    finally:
        os.chdir(original_dir)
