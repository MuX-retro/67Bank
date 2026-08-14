import time
from telegram import Update, PreCheckoutQuery
from telegram.ext import ContextTypes
import database as db
import config

async def cmd_buyai(update, context):
    chat_id = update.effective_chat.id
    await update.message.reply_invoice(
        title="AI-режим для чата",
        description="Доступ к ИИ на 30 дней",
        payload=f"ai_{chat_id}",
        currency="XTR",
        prices=[{"label": "Премиум AI", "amount": config.AI_PRICE}],
        start_parameter="buy_ai"
    )

async def on_precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("ai_"):
        await query.answer(ok=True)

async def on_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = int(update.message.successful_payment.invoice_payload.split("_")[1])
    until = int(time.time()) + config.AI_DURATION
    db.set_ai_active(chat_id, until)
    await update.message.reply_text("✅ AI-режим активирован на 30 дней! Теперь используйте /ai вопрос")

async def cmd_ai(update, context):
    chat_id = update.effective_chat.id
    active, until = db.get_ai_status(chat_id)
    if not active or time.time() > until:
        await update.message.reply_text("❌ AI не активен. Админ может купить через /buyai")
        return
    if not context.args:
        await update.message.reply_text("Напишите вопрос: /ai Как дела?")
        return
    question = " ".join(context.args)
    await update.message.reply_text(f"🤖 Ваш вопрос: {question}\n\n(Ответ AI пока заглушка, подключите OpenAI API)")

async def cmd_aistatus(update, context):
    chat_id = update.effective_chat.id
    active, until = db.get_ai_status(chat_id)
    if active and time.time() < until:
        days = int((until - time.time()) / 86400)
        await update.message.reply_text(f"✅ AI активен, осталось {days} дней.")
    else:
        await update.message.reply_text("❌ AI не активен.")
