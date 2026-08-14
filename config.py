import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных окружения!")

AI_PRICE = 300  # цена AI-подписки в звёздах
AI_DURATION = 30 * 24 * 3600  # 30 дней
