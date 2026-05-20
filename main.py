import asyncio
import logging
import os
import threading

from flask import Flask
from aiogram import Bot, Dispatcher

from database import init_db
from handlers.client import router as client_router
from handlers.admin import router as admin_router

app = Flask(__name__)

@app.route("/")
def home():
    return "SurveyBot is running!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(client_router)
dp.include_router(admin_router)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    asyncio.run(main())
