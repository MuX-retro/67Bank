import re
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

async def cmd_modes(update, context):
    await update.message.reply_text(
        "Режимы:\n"
        "/antiflood – защита от флуда\n"
        "/antilink – блокировка ссылок\n"
        "/captcha – капча для новичков\n"
        "/nightmode – отключение сообщений ночью"
    )

async def cmd_antiflood(update, context):
    chat_id = update.effective_chat.id
    cur = db.get_mode(chat_id, "antiflood")
    db.set_mode(chat_id, "antiflood", not cur)
    await update.message.reply_text(f"Антифлуд {'включён' if not cur else 'выключен'}")

async def cmd_antilink(update, context):
    chat_id = update.effective_chat.id
    cur = db.get_mode(chat_id, "antilink")
    db.set_mode(chat_id, "antilink", not cur)
    await update.message.reply_text(f"Антиссылка {'включена' if not cur else 'выключена'}")

async def cmd_captcha(update, context):
    chat_id = update.effective_chat.id
    cur = db.get_mode(chat_id, "captcha")
    db.set_mode(chat_id, "captcha", not cur)
    await update.message.reply_text(f"Капча {'включена' if not cur else 'выключена'}")

async def cmd_nightmode(update, context):
    chat_id = update.effective_chat.id
    cur = db.get_mode(chat_id, "nightmode")
    db.set_mode(chat_id, "nightmode", not cur)
    await update.message.reply_text(f"Ночной режим {'включён' if not cur else 'выключен'}")

async def on_new_member_captcha(update, context):
    if not db.get_mode(update.effective_chat.id, "captcha"):
        return
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        await update.message.reply_text(
            f"Добро пожаловать, {member.full_name}! Нажмите кнопку, чтобы подтвердить, что вы не бот.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Я человек", callback_data="captcha_ok")]])
        )

async def on_captcha_button(update, context):
    query = update.callback_query
    await query.answer("✅ Вы подтверждены!")
    await query.edit_message_text("Добро пожаловать в чат!")

async def enforce_modes(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text or update.message.caption or ""
    if db.get_mode(chat_id, "antilink"):
        if re.search(r'(https?://|www\.)', text, re.I):
            try:
                await context.bot.delete_message(chat_id, update.message.message_id)
                await context.bot.send_message(chat_id, "❌ Ссылки запрещены!")
                return
            except:
                pass
    if db.get_mode(chat_id, "antiflood"):
        pass
    if db.get_mode(chat_id, "nightmode"):
        hour = time.localtime().tm_hour
        if 0 <= hour < 6:
            try:
                await context.bot.delete_message(chat_id, update.message.message_id)
                await context.bot.send_message(chat_id, "🌙 Ночной режим: сообщения запрещены.")
                return
            except:
                pass
