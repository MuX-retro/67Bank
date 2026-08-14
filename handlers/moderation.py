import time
import re
from telegram import Update, ChatPermissions, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import database as db

async def get_target_user(update, context):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    if context.args:
        try:
            return await context.bot.get_chat_member(update.effective_chat.id, context.args[0]).user
        except:
            return None
    return None

async def is_admin(update, context, user_id=None):
    if user_id is None:
        user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except:
        return False

async def cmd_ban(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут банить.")
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Ответьте на сообщение пользователя или укажите ID.")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"✅ Пользователь {target.full_name} забанен.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_unban(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут разбанивать.")
        return
    if not context.args:
        await update.message.reply_text("Укажите ID пользователя: /unban 123456789")
        return
    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text(f"✅ Пользователь {user_id} разбанен.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_kick(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут кикать.")
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Ответьте на сообщение пользователя.")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"✅ {target.full_name} кикнут.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_mute(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут мутить.")
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Ответьте на сообщение пользователя.")
        return
    duration = "1h"
    if context.args:
        duration = context.args[0]
    time_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    unit = duration[-1]
    if unit in time_map and duration[:-1].isdigit():
        seconds = int(duration[:-1]) * time_map[unit]
    elif duration.isdigit():
        seconds = int(duration) * 60
    else:
        seconds = 3600
    until = time.time() + seconds
    try:
        perms = ChatPermissions(can_send_messages=False)
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, perms, until_date=until)
        await update.message.reply_text(f"🔇 {target.full_name} замучен на {duration}.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_unmute(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут размучивать.")
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Ответьте на сообщение пользователя.")
        return
    try:
        perms = ChatPermissions(can_send_messages=True)
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, perms)
        await update.message.reply_text(f"✅ {target.full_name} размучен.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_warn(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут выдавать варны.")
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Ответьте на сообщение пользователя.")
        return
    count = db.add_warning(target.id, update.effective_chat.id)
    await update.message.reply_text(f"⚠️ {target.full_name} получил предупреждение ({count}/3).")
    if count >= 3:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, target.id)
            await update.message.reply_text(f"🚫 {target.full_name} забанен за 3 предупреждения.")
        except Exception as e:
            await update.message.reply_text(f"Не удалось забанить: {e}")

async def cmd_unwarn(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут снимать варны.")
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Ответьте на сообщение пользователя.")
        return
    db.reset_warnings(target.id, update.effective_chat.id)
    await update.message.reply_text(f"✅ У {target.full_name} сброшены предупреждения.")

async def cmd_warnings(update, context):
    target = await get_target_user(update, context) or update.effective_user
    count = db.get_warnings(target.id, update.effective_chat.id)
    await update.message.reply_text(f"📊 У {target.full_name} {count} предупреждений.")

async def cmd_purge(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут очищать.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответьте на сообщение, до которого нужно удалить.")
        return
    try:
        msg_id = update.message.reply_to_message.message_id
        await context.bot.delete_message(update.effective_chat.id, update.message.message_id)
        for i in range(msg_id, update.message.message_id):
            try:
                await context.bot.delete_message(update.effective_chat.id, i)
            except:
                pass
        await update.message.reply_text("🗑️ Очищено.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_pin(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут закреплять.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответьте на сообщение для закрепления.")
        return
    try:
        silent = "silent" in context.args
        await context.bot.pin_chat_message(update.effective_chat.id, update.message.reply_to_message.message_id,
                                           disable_notification=silent)
        await update.message.reply_text("📌 Закреплено.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_unpin(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут откреплять.")
        return
    try:
        await context.bot.unpin_chat_message(update.effective_chat.id)
        await update.message.reply_text("📌 Откреплено.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_lock(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут закрывать чат.")
        return
    try:
        await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(can_send_messages=False))
        await update.message.reply_text("🔒 Чат закрыт для всех.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_unlock(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут открывать чат.")
        return
    try:
        await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(can_send_messages=True))
        await update.message.reply_text("🔓 Чат открыт.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_slowmode(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут включать медленный режим.")
        return
    if not context.args:
        await update.message.reply_text("Используйте: /slowmode 10s / 1m / 0 (отключить)")
        return
    duration = context.args[0]
    time_map = {'s': 1, 'm': 60, 'h': 3600}
    unit = duration[-1]
    if unit in time_map and duration[:-1].isdigit():
        seconds = int(duration[:-1]) * time_map[unit]
    elif duration.isdigit():
        seconds = int(duration)
    else:
        seconds = 0
    try:
        await context.bot.set_chat_slow_mode_delay(update.effective_chat.id, seconds)
        await update.message.reply_text(f"⏳ Медленный режим: {duration}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_promote(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут повышать.")
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Ответьте на сообщение пользователя.")
        return
    try:
        await context.bot.promote_chat_member(update.effective_chat.id, target.id,
                                              can_manage_chat=True, can_delete_messages=True,
                                              can_restrict_members=True, can_pin_messages=True,
                                              can_promote_members=False)
        await update.message.reply_text(f"✅ {target.full_name} повышен до администратора.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_demote(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут понижать.")
        return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Ответьте на сообщение пользователя.")
        return
    try:
        await context.bot.promote_chat_member(update.effective_chat.id, target.id,
                                              can_manage_chat=False, can_delete_messages=False,
                                              can_restrict_members=False, can_pin_messages=False,
                                              can_promote_members=False)
        await update.message.reply_text(f"✅ {target.full_name} понижен.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_title(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут устанавливать титул.")
        return
    if not context.args:
        await update.message.reply_text("Укажите титул: /title Новый титул")
        return
    title = " ".join(context.args)
    try:
        await context.bot.set_chat_administrator_custom_title(update.effective_chat.id, update.effective_user.id, title)
        await update.message.reply_text(f"✅ Титул установлен: {title}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def cmd_info(update, context):
    target = await get_target_user(update, context) or update.effective_user
    user_id = target.id
    chat_id = update.effective_chat.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    status = member.status
    await update.message.reply_text(
        f"🆔 ID: {user_id}\n"
        f"👤 Имя: {target.full_name}\n"
        f"📌 Статус: {status}\n"
        f"👥 Группа: {update.effective_chat.title}"
    )

async def cmd_id(update, context):
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(
        f"Ваш ID: {user.id}\n"
        f"ID чата: {chat.id}"
    )

async def cmd_admins(update, context):
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    text = "👑 Администраторы:\n"
    for admin in admins:
        text += f"- {admin.user.full_name} ({admin.user.id})\n"
    await update.message.reply_text(text)

async def cmd_rules(update, context):
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT rules FROM chat_modes WHERE chat_id=?", (update.effective_chat.id,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        await update.message.reply_text(f"📜 Правила:\n{row[0]}")
    else:
        await update.message.reply_text("Правила не установлены. /setrules текст")

async def cmd_setrules(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут устанавливать правила.")
        return
    if not context.args:
        await update.message.reply_text("Напишите правила после команды: /setrules Текст правил")
        return
    rules = " ".join(context.args)
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("UPDATE chat_modes SET rules=? WHERE chat_id=?", (rules, update.effective_chat.id))
    if c.rowcount == 0:
        c.execute("INSERT INTO chat_modes (chat_id, rules) VALUES (?, ?)", (update.effective_chat.id, rules))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ Правила сохранены.")

async def cmd_setwelcome(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут устанавливать приветствие.")
        return
    if not context.args:
        await update.message.reply_text("Напишите текст приветствия после команды: /setwelcome Текст")
        return
    text = " ".join(context.args)
    db.set_welcome(update.effective_chat.id, text, True)
    await update.message.reply_text("✅ Приветствие установлено.")

async def cmd_welcome_toggle(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только админы могут включать/выключать приветствие.")
        return
    chat_id = update.effective_chat.id
    _, enabled = db.get_welcome(chat_id)
    db.set_welcome(chat_id, "", not enabled)
    status = "включено" if not enabled else "выключено"
    await update.message.reply_text(f"Приветствие {status}.")

async def on_new_member(update, context):
    chat_id = update.effective_chat.id
    welcome_text, enabled = db.get_welcome(chat_id)
    if not enabled or not welcome_text:
        return
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        await update.message.reply_text(welcome_text.replace("{user}", member.full_name))
