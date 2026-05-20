import asyncio
import logging
import os
import threading

from aiogram import Bot, Dispatcher
from flask import Flask

from handlers.client import router as client_router
from handlers.admin import router as admin_router
from database import init_db

# Логирование
logging.basicConfig(level=logging.INFO)

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не найдена!")

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Flask keep-alive для Render
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running!"


def run_web():
    app.run(host="0.0.0.0", port=10000)


async def main():
    # Инициализация базы данных
    await init_db()

    # Подключение роутеров
    dp.include_router(client_router)
    dp.include_router(admin_router)

    # Запуск бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Flask запускается в отдельном потоке
    threading.Thread(target=run_web).start()

    asyncio.run(main())