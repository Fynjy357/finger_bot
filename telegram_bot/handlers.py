# telegram_bot/handlers.py
import asyncio
import aiohttp
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

from keyboards import get_quick_click_keyboard
from config import FINGERBOT_API_URL

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "👋 <b>Дорогие гости, добро пожаловать!</b>\n\n"
        "Для открытия домофона выполните следующие действия:\n"
        "1) наберите на домофоне 14 квартиру\n"
        "2) пока идет вызов, нажмите на кнопку\n⚡ Быстрый клик"
        "Используйте кнопки ниже:",
        reply_markup=get_quick_click_keyboard()
    )

@router.message(Command("quick_click"))
async def cmd_quick_click(message: Message, bot: Bot):
    """Обработчик команды /quick_click"""
    await send_quick_click_command(message, bot)

@router.message(Command("battery"))
async def cmd_battery(message: Message, bot: Bot):
    """Обработчик команды /battery"""
    await send_battery_check_command(message, bot)

@router.message(F.text == "⚡ Быстрый клик")
async def quick_click_button(message: Message, bot: Bot):
    """Обработчик кнопки быстрого клика"""
    await send_quick_click_command(message, bot)

@router.message(F.text == "🔋 Проверить заряд")
async def battery_check_button(message: Message, bot: Bot):
    """Обработчик кнопки проверки заряда"""
    await send_battery_check_command(message, bot)

async def send_quick_click_command(message: Message, bot: Bot):
    """Отправка команды быстрого клика"""
    # Показываем "печатает..."
    try:
        await bot.send_chat_action(
            chat_id=message.chat.id, 
            action="typing"
        )
    except Exception:
        pass  # Игнорируем ошибки отправки action
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{FINGERBOT_API_URL}/check_battery", timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        await message.answer(
                            "✅ <b>Команда 'Быстрый клик' отправлена!</b>\n"
                            "FingerBot выполнил нажатие.",
                            reply_markup=get_quick_click_keyboard()
                        )
                    else:
                        await message.answer(
                            "❌ <b>Ошибка выполнения команды.</b>",
                            reply_markup=get_quick_click_keyboard()
                        )
                else:
                    await message.answer(
                        f"❌ <b>Ошибка API:</b> {response.status}",
                        reply_markup=get_quick_click_keyboard()
                    )
                    
    except aiohttp.ClientConnectionError:
        await message.answer(
            "❌ <b>Не удалось подключиться к FingerBot API.</b>\n"
            "Проверьте, запущен ли API сервер.",
            reply_markup=get_quick_click_keyboard()
        )
    except asyncio.TimeoutError:
        await message.answer(
            "❌ <b>Таймаут подключения.</b>",
            reply_markup=get_quick_click_keyboard()
        )
    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка:</b> {str(e)}",
            reply_markup=get_quick_click_keyboard()
        )

async def send_battery_check_command(message: Message, bot: Bot):
    """Отправка команды проверки заряда"""
    # Показываем "печатает..."
    try:
        await bot.send_chat_action(
            chat_id=message.chat.id, 
            action="typing"
        )
    except Exception:
        pass
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{FINGERBOT_API_URL}/check_battery", timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        # Отправляем сообщение с Markdown разметкой
                        await message.answer(
                            result["message"],
                            parse_mode="Markdown",
                            reply_markup=get_quick_click_keyboard()
                        )
                    else:
                        await message.answer(
                            "❌ <b>Не удалось получить информацию о батарее.</b>",
                            reply_markup=get_quick_click_keyboard()
                        )
                else:
                    await message.answer(
                        f"❌ <b>Ошибка API:</b> {response.status}",
                        reply_markup=get_quick_click_keyboard()
                    )
                    
    except aiohttp.ClientConnectionError:
        await message.answer(
            "❌ <b>Не удалось подключиться к FingerBot API.</b>\n"
            "Проверьте, запущен ли API сервер.",
            reply_markup=get_quick_click_keyboard()
        )
    except asyncio.TimeoutError:
        await message.answer(
            "❌ <b>Таймаут подключения.</b>",
            reply_markup=get_quick_click_keyboard()
        )
    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка:</b> {str(e)}",
            reply_markup=get_quick_click_keyboard()
        )

@router.message()
async def any_message(message: Message):
    """Обработчик любых других сообщений"""
    await message.answer(
        "🤖 <b>Используйте кнопки для управления домофоном</b>",
        reply_markup=get_quick_click_keyboard()
    )
