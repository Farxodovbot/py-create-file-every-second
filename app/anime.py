import json
import sqlite3
import requests
from flask import Flask, request

app = Flask(__name__)

# --- SOZLAMALAR ---
TOKEN = "8705927604:AAEjfrb7ZK2es-9tf2pu6csYuSUywMxrGxY"
ADMIN_ID = 7253593181
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"

# --- BAZANI SOZLASH ---
def init_db():
    conn = sqlite3.connect('anime_bot.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS channels (channel_id TEXT PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS animes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, season INTEGER, episodes_json TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS admin_state (admin_id INTEGER PRIMARY KEY, state TEXT, data TEXT)')
    conn.commit()
    conn.close()

# --- TELEGRAM API YORDAMCHILARI ---
def api_post(method, data):
    return requests.post(BASE_URL + method, json=data).json()

def check_sub(user_id):
    conn = sqlite3.connect('anime_bot.db')
    channels = [r[0] for r in conn.execute("SELECT channel_id FROM channels").fetchall()]
    conn.close()
    if not channels: return True
    for ch in channels:
        res = requests.get(f"{BASE_URL}getChatMember?chat_id={ch}&user_id={user_id}").json()
        if not res.get("ok") or res["result"]["status"] in ["left", "kicked"]: return False
    return True

# --- ADMIN PANEL TUGMALARI ---
def admin_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📢 Kanalga Post", "callback_data": "post_chan"}],
            [{"text": "➕ Kanal qo'shish", "callback_data": "add_ch"}, {"text": "❌ Kanalni o'chirish", "callback_data": "del_ch"}],
            [{"text": "➕ Anime qo'shish", "callback_data": "add_anime"}],
            [{"text": "👥 Statistika", "callback_data": "stats"}],
            [{"text": "🔙 Bosh menyu", "callback_data": "main_menu"}]
        ]
    }

# --- WEBHOOK MAIN ---
@app.route("/", methods=["POST"])
def webhook():
    upd = request.get_json()
    if "message" in upd:
        msg = upd["message"]
        uid = msg["from"]["id"]
        text = msg.get("text", "")

        # Foydalanuvchini ro'yxatga olish
        conn = sqlite3.connect('anime_bot.db')
        conn.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
        conn.commit()

        # Majburiy obuna tekshiruvi
        if uid != ADMIN_ID and not check_sub(uid):
            chs = conn.execute("SELECT channel_id FROM channels").fetchall()
            kb = [[{"text": f"Kanal {i+1}", "url": f"https://t.me/{c[0][1:]}"}] for i, c in enumerate(chs)]
            kb.append([{"text": "✅ Tekshirish", "callback_data": "check_sub"}])
            api_post("sendMessage", {"chat_id": uid, "text": "🛑 Botdan foydalanish uchun kanallarga a'zo bo'ling!", "reply_markup": {"inline_keyboard": kb}})
            return "OK"

        # Admin holatlari (State)
        res_state = conn.execute("SELECT state FROM admin_state WHERE admin_id=?", (uid,)).fetchone()
        state = res_state[0] if res_state else None

        if uid == ADMIN_ID:
            if state == "add_ch_name":
                conn.execute("INSERT OR IGNORE INTO channels VALUES (?)", (text,))
                conn.execute("DELETE FROM admin_state WHERE admin_id=?", (uid,))
                conn.commit()
                api_post("sendMessage", {"chat_id": uid, "text": "✅ Kanal qo'shildi!", "reply_markup": admin_keyboard()})
                return "OK"
            
            elif state == "broadcast":
                users = conn.execute("SELECT user_id FROM users").fetchall()
                for u in users: api_post("copyMessage", {"chat_id": u[0], "from_chat_id": uid, "message_id": msg["message_id"]})
                conn.execute("DELETE FROM admin_state WHERE admin_id=?", (uid,))
                conn.commit()
                api_post("sendMessage", {"chat_id": uid, "text": "✅ Reklama tarqatildi!"})
                return "OK"

        if text == "/start":
            kb = {
                "inline_keyboard": [
                    [{"text": "🔍 Qidiruv", "callback_data": "search"}, {"text": "⭐ Sevimlilar", "callback_data": "fav"}],
                    [{"text": "🟢 Davom etayotgan", "callback_data": "on"}, {"text": "✅ Tugallangan", "callback_data": "off"}],
                    [{"text": "🎲 Random", "callback_data": "rand"}, {"text": "👑 VIP", "callback_data": "vip"}]
                ]
            }
            if uid == ADMIN_ID: kb["inline_keyboard"].append([{"text": "🔐 Admin Panel", "callback_data": "admin"}])
            api_post("sendPhoto", {"chat_id": uid, "photo": "https://t.me/AniComplex_Rasmiy/10", "caption": "<b>AniComplex</b> botiga xush kelibsiz!", "reply_markup": kb})

        # Qidiruv mantiqi (Nom bo'yicha)
        elif state == "searching":
            # Bazadan qidirish (Sodda misol)
            api_post("sendMessage", {"chat_id": uid, "text": f"🔍 <b>{text}</b> bo'yicha fasllar:", 
                "reply_markup": {"inline_keyboard": [
                    [{"text": "1-fasl", "callback_data": f"se_1_{text}"}, {"text": "2-fasl", "callback_data": f"se_2_{text}"}]
                ]}})
            conn.execute("DELETE FROM admin_state WHERE admin_id=?", (uid,))
            conn.commit()

        conn.close()

    elif "callback_query" in upd:
        call = upd["callback_query"]
        uid = call["from"]["id"]
        data = call["data"]

        if data == "admin":
            api_post("sendMessage", {"chat_id": uid, "text": "🛠 Admin boshqaruv paneli:", "reply_markup": admin_keyboard()})
        
        elif data == "add_ch":
            conn = sqlite3.connect('anime_bot.db')
            conn.execute("INSERT OR REPLACE INTO admin_state (admin_id, state) VALUES (?, ?)", (uid, "add_ch_name"))
            conn.commit()
            api_post("sendMessage", {"chat_id": uid, "text": "Kanal yuzerini yuboring (@ yordamida):"})
        
        elif data == "search":
            conn = sqlite3.connect('anime_bot.db')
            conn.execute("INSERT OR REPLACE INTO admin_state (admin_id, state) VALUES (?, ?)", (uid, "searching"))
            conn.commit()
            api_post("sendMessage", {"chat_id": uid, "text": "🔍 Anime nomini kiriting:"})

        elif data.startswith("se_"):
            # 25 ta qismni chiqarish
            buttons = []
            row = []
            for i in range(1, 26):
                row.append({"text": str(i), "callback_data": f"ep_{i}"})
                if len(row) == 5:
                    buttons.append(row); row = []
            api_post("editMessageText", {"chat_id": uid, "message_id": call["message"]["message_id"], "text": "📺 Qismni tanlang:", "reply_markup": {"inline_keyboard": buttons}})

    return "OK"

if __name__ == "__main__":
    init_db()
    app.run(port=5000)
