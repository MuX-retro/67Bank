import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler, filters
import config
import database as db
from handlers import moderation as mod
from handlers import modes
from handlers import ai

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("jamalai")

async def cmd_start(update, context):
    await update.message.reply_text(
        "👋 Привет! Я <b>JamalAI</b> – бот-модератор с ИИ.\n"
        "Добавь меня в группу с правами администратора.\n\n"
        "Команды: /help\n"
        "AI-режим: /buyai (300 ⭐)",
        parse_mode="HTML"
    )

async def cmd_help(update, context):
    text = (
        "📖 <b>Все команды JamalAI</b>\n\n"
        "🔹 <b>Модерация</b>\n"
        "/ban, /unban, /kick – бан/разбан/кик\n"
        "/mute [время], /unmute – мут/размут\n"
        "/warn, /unwarn, /warnings – система предупреждений\n"
        "/purge – очистка сообщений\n"
        "/pin [silent], /unpin – закреп/откреп\n"
        "/lock, /unlock – закрыть/открыть чат\n"
        "/slowmode 10s|1m|0 – медленный режим\n"
        "/promote, /demote, /title – администрирование\n"
        "/info, /id, /admins – информация\n"
        "/rules, /setrules – правила\n"
        "/setwelcome, /welcome – приветствие\n\n"
        "🔹 <b>Режимы</b>\n"
        "/antiflood, /antilink, /captcha, /nightmode\n\n"
        "🔹 <b>Искусственный интеллект</b>\n"
        "/buyai – активировать AI (300 ⭐)\n"
        "/ai вопрос – спросить ИИ\n"
        "/aistatus – статус подписки"
    )
    await update.message.reply_text(text, parse_mode="HTML")

def main():
    db.init_db()
    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("modes", modes.cmd_modes))

    app.add_handler(CommandHandler("ban", mod.cmd_ban))
    app.add_handler(CommandHandler("unban", mod.cmd_unban))
    app.add_handler(CommandHandler("kick", mod.cmd_kick))
    app.add_handler(CommandHandler("mute", mod.cmd_mute))
    app.add_handler(CommandHandler("unmute", mod.cmd_unmute))
    app.add_handler(CommandHandler("warn", mod.cmd_warn))
    app.add_handler(CommandHandler("unwarn", mod.cmd_unwarn))
    app.add_handler(CommandHandler("warnings", mod.cmd_warnings))
    app.add_handler(CommandHandler("purge", mod.cmd_purge))
    app.add_handler(CommandHandler("pin", mod.cmd_pin))
    app.add_handler(CommandHandler("unpin", mod.cmd_unpin))
    app.add_handler(CommandHandler("lock", mod.cmd_lock))
    app.add_handler(CommandHandler("unlock", mod.cmd_unlock))
    app.add_handler(CommandHandler("slowmode", mod.cmd_slowmode))
    app.add_handler(CommandHandler("promote", mod.cmd_promote))
    app.add_handler(CommandHandler("demote", mod.cmd_demote))
    app.add_handler(CommandHandler("title", mod.cmd_title))
    app.add_handler(CommandHandler("info", mod.cmd_info))
    app.add_handler(CommandHandler("id", mod.cmd_id))
    app.add_handler(CommandHandler("admins", mod.cmd_admins))
    app.add_handler(CommandHandler("rules", mod.cmd_rules))
    app.add_handler(CommandHandler("setrules", mod.cmd_setrules))
    app.add_handler(CommandHandler("setwelcome", mod.cmd_setwelcome))
    app.add_handler(CommandHandler("welcome", mod.cmd_welcome_toggle))

    app.add_handler(CommandHandler("antiflood", modes.cmd_antiflood))
    app.add_handler(CommandHandler("antilink", modes.cmd_antilink))
    app.add_handler(CommandHandler("captcha", modes.cmd_captcha))
    app.add_handler(CommandHandler("nightmode", modes.cmd_nightmode))

    app.add_handler(CommandHandler("buyai", ai.cmd_buyai))
    app.add_handler(CommandHandler("ai", ai.cmd_ai))
    app.add_handler(CommandHandler("aistatus", ai.cmd_aistatus))
    app.add_handler(PreCheckoutQueryHandler(ai.on_precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, ai.on_successful_payment))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, mod.on_new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, modes.on_new_member_captcha))
    app.add_handler(CallbackQueryHandler(modes.on_captcha_button, pattern="^captcha_ok:"))

    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND, modes.enforce_modes))

    logger.info("🚀 JamalAI запущен, начинаю polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
