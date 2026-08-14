import sqlite3
import os

DB_PATH = os.getenv("DATABASE_PATH", "/data/bot.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_modes (
        chat_id INTEGER PRIMARY KEY,
        antiflood INTEGER DEFAULT 0,
        antilink INTEGER DEFAULT 0,
        captcha INTEGER DEFAULT 0,
        nightmode INTEGER DEFAULT 0,
        welcome_enabled INTEGER DEFAULT 0,
        welcome_text TEXT DEFAULT '',
        rules TEXT DEFAULT ''
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ai_subscriptions (
        chat_id INTEGER PRIMARY KEY,
        active INTEGER DEFAULT 0,
        until INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS warnings (
        user_id INTEGER,
        chat_id INTEGER,
        count INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, chat_id)
    )''')
    conn.commit()
    conn.close()

def get_mode(chat_id, mode):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"SELECT {mode} FROM chat_modes WHERE chat_id=?", (chat_id,))
    row = c.fetchone()
    if row is None:
        c.execute("INSERT INTO chat_modes (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        row = (0,)
    conn.close()
    return row[0] == 1

def set_mode(chat_id, mode, value):
    conn = get_conn()
    c = conn.cursor()
    val = 1 if value else 0
    c.execute(f"UPDATE chat_modes SET {mode}=? WHERE chat_id=?", (val, chat_id))
    if c.rowcount == 0:
        c.execute(f"INSERT INTO chat_modes (chat_id, {mode}) VALUES (?, ?)", (chat_id, val))
    conn.commit()
    conn.close()

def get_ai_status(chat_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT active, until FROM ai_subscriptions WHERE chat_id=?", (chat_id,))
    row = c.fetchone()
    if row is None:
        return False, 0
    return row[0] == 1, row[1]

def set_ai_active(chat_id, until_ts):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO ai_subscriptions (chat_id, active, until) VALUES (?, 1, ?)", (chat_id, until_ts))
    conn.commit()
    conn.close()

def get_warnings(user_id, chat_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT count FROM warnings WHERE user_id=? AND chat_id=?", (user_id, chat_id))
    row = c.fetchone()
    if row is None:
        return 0
    return row[0]

def add_warning(user_id, chat_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO warnings (user_id, chat_id, count) VALUES (?, ?, 1) "
              "ON CONFLICT(user_id, chat_id) DO UPDATE SET count = count + 1", (user_id, chat_id))
    conn.commit()
    new_count = get_warnings(user_id, chat_id)
    conn.close()
    return new_count

def reset_warnings(user_id, chat_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM warnings WHERE user_id=? AND chat_id=?", (user_id, chat_id))
    conn.commit()
    conn.close()

def get_welcome(chat_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT welcome_text, welcome_enabled FROM chat_modes WHERE chat_id=?", (chat_id,))
    row = c.fetchone()
    if row is None:
        return "", False
    return row[0] or "", row[1] == 1

def set_welcome(chat_id, text, enabled=True):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE chat_modes SET welcome_text=?, welcome_enabled=? WHERE chat_id=?", (text, 1 if enabled else 0, chat_id))
    if c.rowcount == 0:
        c.execute("INSERT INTO chat_modes (chat_id, welcome_text, welcome_enabled) VALUES (?, ?, ?)",
                  (chat_id, text, 1 if enabled else 0))
    conn.commit()
    conn.close()
