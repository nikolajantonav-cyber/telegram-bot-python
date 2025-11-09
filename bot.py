# bot.py
import logging
from aiogram import Bot, Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand

import db
from config import API_TOKEN
from handlers import register_handlers
from helpers import load_recipes_from_json

# ======================================================
# 🧠 Логирование
# ======================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("cooking-bot")


# 🗃️ Инициализация базы

db.init_db()

added = load_recipes_from_json()
if added:
    logger.info(f"Добавлено рецептов из JSON: {added}")


# 🤖 Инициализация бота
bot = Bot(API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# Регистрируем все хендлеры
register_handlers(dp)


#  Команды

async def _set_bot_commands():
    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="help", description="Помощь и возможности"),
        BotCommand(command="recipes", description="Список рецептов"),
        BotCommand(command="random", description="Случайный рецепт"),
    ]
    try:
        await bot.set_my_commands(commands)
        logger.info("Команды бота установлены ✅")
    except Exception as e:
        logger.warning(f"Не удалось установить команды: {e}")



''' Старт и остановка'''

async def on_startup(dp):
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook удалён, старые апдейты сброшены ✅")
    except Exception as e:
        logger.warning(f"delete_webhook error: {e}")

    await _set_bot_commands()
    me = await bot.get_me()
    logger.info(f"Bot: {me.first_name} [@{me.username}] запущен и готов к работе 🔥")


async def on_shutdown(dp):
    # Закрываем соединение с БД, если нужно
    try:
        if hasattr(db, "close"):
            db.close()
            logger.info("Соединение с базой закрыто ✅")
    except Exception as e:
        logger.warning(f"DB close error: {e}")
    logger.info("Бот корректно остановлен 👋")



'''Запуск'''

if __name__ == "__main__":
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )