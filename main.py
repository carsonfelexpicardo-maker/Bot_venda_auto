# =========================
# IMPORTS
# =========================
import telebot
from telebot import types
from flask import Flask, jsonify
from threading import Thread
import sqlite3
import time
import os

# =========================
# CONFIGURATION
# =========================
TOKEN = os.getenv("BOT_TOKEN")  # Use Environment Variable on Render
ADMIN_ID = 6953777986

EMAIL_PAYPAL = "rivaldomaurinholuis3@gmail.com"
CARTEIRA_USDT = "0x7bbf369df5a2c12dbcac4d9768703d318d74b491"

BOT = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# =========================
# DATABASE
# =========================
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    package TEXT,
    price TEXT,
    status TEXT,
    time INTEGER
)
""")
db.commit()

# =========================
# PRODUCTS
# =========================
PRODUCTS = {
    "bronze": {
        "name": "🥉 BRONZE",
        "stars": 1500,
        "usd": "$32.99",
        "link": "https://mega.nz/folder/PBdQwCTZ#1TAr86RRtZQD59pTH91TXQ",
        "description": "401 photos + 20 videos"
    },
    "silver": {
        "name": "🥈 SILVER",
        "stars": 2500,
        "usd": "$51.99",
        "link": "https://mega.nz/folder/nQ0USC4J#-aeGDupNTy_vgQCgX4jZFg",
        "description": "842 photos + 223 videos"
    },
    "diamond": {
        "name": "💎 DIAMOND",
        "stars": 5000,
        "usd": "$99.99",
        "link": "https://mega.nz/folder/DF8CTJpa#8sHiABdYvYAX5xWzsAyRnw",
        "description": "2706 photos + 981 videos"
    }
}

# =========================
# ANTI-FLOOD
# =========================
last_msg = {}
def anti_flood(user_id):
    now = time.time()
    if user_id in last_msg and now - last_msg[user_id] < 2:
        return False
    last_msg[user_id] = now
    return True

# =========================
# DASHBOARD
# =========================
@app.route("/")
def dashboard():
    cursor.execute("SELECT COUNT(*), status FROM sales GROUP BY status")
    data = cursor.fetchall()
    return jsonify(data)

def run_web():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_web).start()

# =========================
# START
# =========================
@BOT.message_handler(commands=["start"])
def start(msg):
    if not anti_flood(msg.from_user.id): return
    kb = types.InlineKeyboardMarkup()
    for k, p in PRODUCTS.items():
        kb.add(types.InlineKeyboardButton(
            f"{p['name']} - {p['usd']} ({p['description']})",
            callback_data=f"buy_{k}"
        ))
    welcome_text = (
        "✨ Welcome to the Premium Video Store! ✨\n\n"
        "What package would you like to buy today?"
    )
    BOT.send_message(msg.chat.id, welcome_text, reply_markup=kb)

# =========================
# CHOOSE PAYMENT METHOD
# =========================
@BOT.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def choose_method(call):
    pkg = call.data.split("_")[1]
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("⭐ Telegram Stars", callback_data=f"stars_{pkg}"),
        types.InlineKeyboardButton("💳 PayPal", callback_data=f"paypal_{pkg}"),
        types.InlineKeyboardButton("🔗 USDT", callback_data=f"crypto_{pkg}")
    )
    BOT.edit_message_text(
        f"📦 {PRODUCTS[pkg]['name']}\nPrice: {PRODUCTS[pkg]['usd']}\nDescription: {PRODUCTS[pkg]['description']}\n\nChoose your payment method:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )

# =========================
# TELEGRAM STARS (AUTOMATIC)
# =========================
@BOT.callback_query_handler(func=lambda c: c.data.startswith("stars_"))
def stars_pay(call):
    pkg = call.data.split("_")[1]
    BOT.send_invoice(
        call.message.chat.id,
        title=PRODUCTS[pkg]["name"],
        description="Instant Access",
        invoice_payload=pkg,
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice("Stars", PRODUCTS[pkg]["stars"])]
    )

@BOT.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    BOT.answer_pre_checkout_query(q.id, ok=True)

@BOT.message_handler(content_types=["successful_payment"])
def success(msg):
    pkg = msg.successful_payment.invoice_payload
    BOT.send_message(
        msg.chat.id,
        f"✅ Payment confirmed!\nYour link: {PRODUCTS[pkg]['link']}"
    )
    cursor.execute(
        "INSERT INTO sales (user_id, package, price, status, time) VALUES (?,?,?,?,?)",
        (msg.from_user.id, pkg, PRODUCTS[pkg]["usd"], "AUTO", int(time.time()))
    )
    db.commit()

# =========================
# PAYPAL / USDT MANUAL
# =========================
@BOT.callback_query_handler(func=lambda c: c.data.startswith(("paypal_", "crypto_")))
def manual(call):
    method, pkg = call.data.split("_")
    text = (
        f"💳 PayPal Payment\nAmount: {PRODUCTS[pkg]['usd']}\nEmail: `{EMAIL_PAYPAL}`"
        if method == "paypal"
        else f"🔗 USDT Payment (BEP20)\nAmount: {PRODUCTS[pkg]['usd']}\nWallet: `{CARTEIRA_USDT}`"
    )
    BOT.send_message(call.message.chat.id, text + "\n\nPlease send a screenshot of your payment.", parse_mode="Markdown")
    cursor.execute(
        "INSERT INTO sales (user_id, package, price, status, time) VALUES (?,?,?,?,?)",
        (call.from_user.id, pkg, PRODUCTS[pkg]["usd"], "PENDING", int(time.time()))
    )
    db.commit()

# =========================
# RECEIVE PAYMENT RECEIPT
# =========================
@BOT.message_handler(content_types=["photo"])
def receipt(msg):
    BOT.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{msg.from_user.id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{msg.from_user.id}")
    )
    BOT.send_message(ADMIN_ID, "New payment receipt:", reply_markup=kb)

# =========================
# APPROVE / REJECT
# =========================
@BOT.callback_query_handler(func=lambda c: c.data.startswith(("approve_", "reject_")))
def admin_action(call):
    if call.from_user.id != ADMIN_ID: return
    action, user_id = call.data.split("_")
    user_id = int(user_id)

    if action == "approve":
        cursor.execute("SELECT package FROM sales WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
        pkg = cursor.fetchone()[0]
        BOT.send_message(user_id, f"✅ Payment approved!\nYour link: {PRODUCTS[pkg]['link']}")
        cursor.execute("UPDATE sales SET status='APPROVED' WHERE user_id=?", (user_id,))
    else:
        BOT.send_message(user_id, "❌ Payment rejected.")
        cursor.execute("UPDATE sales SET status='REJECTED' WHERE user_id=?", (user_id,))

    db.commit()
    BOT.answer_callback_query(call.id)

# =========================
# START BOT
# =========================
print("BOT ONLINE")
BOT.infinity_polling()