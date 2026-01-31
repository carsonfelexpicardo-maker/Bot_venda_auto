import telebot
from telebot import types
from flask import Flask
from threading import Thread
import re
import time

# --- SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Premium Store is Live!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- BOT CONFIGURATION ---
TOKEN = '8316409069:AAFwMVesRk6ja_ME540Jlg5-ROawuzpZujg'
BOT = telebot.TeleBot(TOKEN)

EMAIL_PAYPAL = "rivaldomaurinholuis3@gmail.com"
CARTEIRA_USDT = "0x7bbf369df5a2c12dbcac4d9768703d318d74b491"
ADMIN_ID = 6953777986

# --- PROFESSIONAL PACKAGES ---
PRODUCTS = {
    'p_bronze': {
        'name': '🥉 BRONZE PACKAGE',
        'desc': '• Access to Standard Premium Collection\n• 720p Video Quality\n• Regular Updates',
        'label': '💵 $32.99 (1500 ⭐)',
        'price': 1500,
        'usd': '$32.99',
        'link': 'https://mega.nz/folder/PBdQwCTZ#1TAr86RRtZQD59pTH91TXQ'
    },
    'p_silver': {
        'name': '🥈 SILVER PACKAGE',
        'desc': '• Access to Extended Premium Collection\n• 1080p Full HD Quality\n• Priority Support & Daily Updates',
        'label': '💵 $51.99 (2500 ⭐)',
        'price': 2500,
        'usd': '$51.99',
        'link': 'https://mega.nz/folder/nQ0USC4J#-aeGDupNTy_vgQCgX4jZFg'
    },
    'p_diamond': {
        'name': '💎 DIAMOND PACKAGE',
        'desc': '• Full Lifetime VIP Access\n• 4K Ultra HD Quality\n• Exclusive Content & 24/7 VIP Support',
        'label': '💵 $99.99 (5000 ⭐)',
        'price': 5000,
        'usd': '$99.99',
        'link': 'https://mega.nz/folder/DF8CTJpa#8sHiABdYvYAX5xWzsAyRnw'
    }
}

# --- CLIENT INTERFACE (ENGLISH) ---
@BOT.message_handler(commands=['start'])
def menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, p in PRODUCTS.items():
        btn = types.InlineKeyboardButton(f"{p['name']} - {p['usd']}", callback_data=f"select_{key}")
        markup.add(btn)
    
    welcome_text = (
        "✨ <b>WELCOME TO PREMIUM CONTENT STORE</b> ✨\n\n"
        "Choose the best plan for you:\n\n"
        f"🥉 <b>BRONZE:</b> {PRODUCTS['p_bronze']['desc']}\n\n"
        f"🥈 <b>SILVER:</b> {PRODUCTS['p_silver']['desc']}\n\n"
        f"💎 <b>DIAMOND:</b> {PRODUCTS['p_diamond']['desc']}\n\n"
        "<i>Select a package below to proceed with payment:</i>"
    )
    BOT.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="HTML")

@BOT.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def choose_method(call):
    p_key = call.data.replace('select_', '')
    p = PRODUCTS[p_key]
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"⭐ Telegram Stars ({p['price']} ⭐)", callback_data=f"stars_{p_key}"),
        types.InlineKeyboardButton(f"💳 PayPal ({p['usd']})", callback_data=f"paypal_{p_key}"),
        types.InlineKeyboardButton(f"🔗 USDT BEP20 ({p['usd']})", callback_data=f"crypto_{p_key}"),
        types.InlineKeyboardButton("« Back", callback_data="back_to_main")
    )
    
    text = f"📦 <b>{p['name']}</b>\nSelected Price: <b>{p['usd']}</b>\n\nSelect your payment method:"
    BOT.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@BOT.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_main(call):
    menu(call.message)

@BOT.callback_query_handler(func=lambda call: call.data.startswith(('paypal_', 'crypto_')))
def manual_pay(call):
    p_key = call.data.split('_')[1]
    p = PRODUCTS[f"p_{p_key}"]
    
    if "paypal" in call.data:
        msg = f"💳 <b>PAYPAL PAYMENT</b>\n\nAmount: <b>{p['usd']}</b>\nEmail: <code>{EMAIL_PAYPAL}</code>"
    else:
        msg = f"🔗 <b>USDT PAYMENT (BEP20)</b>\n\nAmount: <b>{p['usd']} USDT</b>\nNetwork: <b>BEP20</b>\nAddress: <code>{CARTEIRA_USDT}</code>"
    
    instr = f"{msg}\n\n⚠️ <b>IMPORTANT:</b> After payment, send the <b>SCREENSHOT (Photo)</b> of the receipt here."
    BOT.edit_message_text(instr, call.message.chat.id, call.message.message_id, parse_mode="HTML")

# --- ADMIN NOTIFICATION ---
@BOT.message_handler(content_types=['photo'])
def handle_receipt(message):
    BOT.reply_to(message, "🎯 <b>Receipt Received!</b>\nOur team is validating your payment. Please wait.", parse_mode="HTML")
    
    user = message.from_user
    info = (f"📩 <b>NEW RECEIPT!</b>\n"
            f"👤 User: {user.first_name}\n"
            f"🆔 ID: <code>{user.id}</code>\n\n"
            f"⚠️ <b>REPLY TO THE PHOTO WITH:</b>\n"
            f"/approve_bronze\n"
            f"/approve_silver\n"
            f"/approve_diamond\n"
            f"/reject")
    
    # Forward the photo so admin can reply to it
    fwd = BOT.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    BOT.send_message(ADMIN_ID, info, reply_to_message_id=fwd.message_id, parse_mode="HTML")

# --- ADMIN DECISION (REPLY TO PHOTO) ---
@BOT.message_handler(commands=['approve_bronze', 'approve_silver', 'approve_diamond', 'reject'])
def admin_action(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message:
        return BOT.reply_to(message, "❌ Please, reply directly to the <b>forwarded photo</b>.")

    try:
        # Get target ID from forward data
        if message.reply_to_message.forward_from:
            target_id = message.reply_to_message.forward_from.id
        else:
            return BOT.reply_to(message, "❌ Cannot detect User ID (Privacy settings). Use manual release.")

        cmd = message.text.split()[0]

        if "/reject" in cmd:
            BOT.send_message(target_id, "❌ <b>Payment Rejected</b>\nWe couldn't verify your transaction. Support: @Admin", parse_mode="HTML")
            return BOT.reply_to(message, "🚫 Rejected.")

        p_type = f"p_{cmd.split('_')[1]}"
        if p_type in PRODUCTS:
            p = PRODUCTS[p_type]
            BOT.send_message(target_id, f"✅ <b>PAYMENT APPROVED!</b>\n\nPackage: {p['name']}\n🚀 <b>Access Link:</b> {p['link']}", parse_mode="HTML")
            BOT.reply_to(message, f"✅ Released {p['name']} to {target_id}")

    except Exception as e:
        BOT.reply_to(message, f"Error: {e}")

# --- AUTOMATIC STARS PAYMENT ---
@BOT.callback_query_handler(func=lambda call: call.data.startswith('stars_'))
def pay_stars(call):
    p = PRODUCTS[call.data.replace('stars_', 'p_') if 'p_' not in call.data else call.data.replace('stars_', '')]
    BOT.send_invoice(
        call.message.chat.id, p['name'], "Instant Access to Premium Content", 
        call.data, "", "XTR", [types.LabeledPrice(p['name'], p['price'])]
    )

@BOT.pre_checkout_query_handler(func=lambda q: True)
def checkout(q): BOT.answer_pre_checkout_query(q.id, ok=True)

@BOT.message_handler(content_types=['successful_payment'])
def success(message):
    p_key = message.successful_payment.invoice_payload.replace('stars_', '')
    BOT.send_message(message.chat.id, f"🎉 <b>CONFIRMED!</b>\n🚀 <b>Link:</b> {PRODUCTS[p_key]['link']}", parse_mode="HTML")

# --- SECURITY BOOT ---
if __name__ == "__main__":
    keep_alive()
    try:
        BOT.remove_webhook()
        time.sleep(2)
    except: pass
    print("Bot is Professional and Running!")
    BOT.infinity_polling(skip_pending=True)
