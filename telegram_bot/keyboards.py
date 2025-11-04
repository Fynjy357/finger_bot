# telegram_bot/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_quick_click_keyboard():
    """Клавиатура с кнопками управления"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚡ Быстрый клик")],
            [KeyboardButton(text="🔋 Проверить заряд")]  # НОВАЯ КНОПКА
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
