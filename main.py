import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os
import re
import time

# --- CONFIGURAÇÃO DO SERVIDOR (PARA O RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Online e Conectado!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.setDaemon(True)
    t.start()

# --- CONFIGURAÇÕES DO BOT ---
TOKEN = '8316409069:AAFwMVesRk6ja_ME540Jlg5-ROawuzpZujg'
BOT = telebot.TeleBot(TOKEN)

EMAIL_PAYPAL = "rivaldomaurinholuis3@gmail.com"
CARTEIRA_USDT = "0x7bbf369df5a2c12dbcac4d9768703d318d74b491"
ADMIN_ID = 6953777986

PRODUCTS = {
    'p_bronze': {
        'name': '🥉 BRONZE PACKAGE', 
        'price': 1500, 
        'usd': '$32.99',
        'delivery': 'https://mega.nz/folder/PBdQwCTZ#1TAr86RRtZQD59pTH91TXQ'
    },
    'p_silver': {
        'name': '🥈 SILVER PACKAGE', 
        'price': 2500, 
        'usd': '$51.99',
        'delivery': 'https://mega.nz/folder/nQ0USC4J#-aeGDupNTy_vgQCgX4jZFg'
    },
    'p_diamond': {
        'name': '💎 DIAMOND PACKAGE', 
        'price': 5000, 
        'usd': '$99.99',
        'delivery': 'https://mega.nz/folder/DF8CTJpa#8sHiABdYvYAX5xWzsAyRnw'
    }
}

# --- MENU INICIAL ---
@BOT.message_handler(commands=['start'])
def menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, p in PRODUCTS.items():
        btn = types.InlineKeyboardButton(f"{p['name']} - {p['usd']}", callback_data=f"select_{key}")
        markup.add(btn)
    
    welcome = "✨ <b>PREMIUM VIDEO STORE</b> ✨\n\nSelect your package below:"
    BOT.send_message(message.chat.id, welcome, reply_markup=markup, parse_mode="HTML")

# --- ESCOLHA DO MÉTODO ---
@BOT.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def choose_method(call):
    try:
        product_key = call.data.replace('select_', '')
        p = PRODUCTS[product_key]
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("⭐ Telegram Stars (Instant)", callback_data=f"stars_{product_key}"),
            types.InlineKeyboardButton("💳 PayPal (Manual Review)", callback_data=f"paypal_{product_key}"),
            types.InlineKeyboardButton("🔗 USDT - BEP20 (Manual Review)", callback_data=f"crypto_{product_key}"),
            types.InlineKeyboardButton("« Back", callback_data="back_to_main")
        )
        
        text = f"📦 <b>{p['name']}</b>\n💰 <b>Value:</b> {p['usd']}\n\nChoose payment method:"
        BOT.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except: pass

@BOT.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_main(call):
    menu(call.message)

# --- MÉTODOS MANUAIS ---
@BOT.callback_query_handler(func=lambda call: call.data.startswith(('paypal_', 'crypto_')))
def manual_pay(call):
    try:
        if "paypal_" in call.data:
            p = PRODUCTS[call.data.replace('paypal_', '')]
            msg = f"💳 <b>PAYPAL PAYMENT</b>\n\nAmount: <b>{p['usd']}</b>\nEmail: <code>{EMAIL_PAYPAL}</code>"
        else:
            p = PRODUCTS[call.data.replace('crypto_', '')]
            msg = f"🔗 <b>USDT PAYMENT (BEP20)</b>\n\nAmount: <b>{p['usd']} USDT</b>\nAddress: <code>{CARTEIRA_USDT}</code>"
        
        BOT.edit_message_text(f"{msg}\n\n⚠️ Send the screenshot of payment here.", call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except: pass

# --- RECEBIMENTO DO COMPROVANTE ---
@BOT.message_handler(content_types=['photo'])
def handle_receipt(message):
    BOT.reply_to(message, "🎯 <b>Receipt Received!</b> We are reviewing it.", parse_mode="HTML")
    
    user = message.from_user
    username = f"@{user.username}" if user.username else "N/A"
    
    admin_msg = (f"🆕 <b>NOVO COMPROVANTE!</b>\n"
                 f"👤 De: {user.first_name} ({username})\n"
                 f"🆔 ID: <code>{user.id}</code>\n\n"
                 f"⚠️ Responda A ESTA MENSAGEM com:\n"
                 f"/liberar_bronze\n"
                 f"/liberar_silver\n"
                 f"/liberar_diamond\n"
                 f"/rejeitar")
    
    BOT.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    BOT.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")

# --- DECISÃO DO ADMIN (CORREÇÃO DE ERRO 400 E REJEIÇÃO) ---
@BOT.message_handler(commands=['liberar_bronze', 'liberar_silver', 'liberar_diamond', 'rejeitar'])
def admin_decision(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return

    try:
        text_orig = message.reply_to_message.text or ""
        match = re.search(r"ID:\s*(\d+)", text_orig)
        if not match: return
        
        target_id = int(match.group(1))
        cmd = message.text.split()[0]

        if "/rejeitar" in cmd:
            BOT.send_message(target_id, "❌ <b>Payment Rejected.</b> Invalid receipt.", parse_mode="HTML")
            return BOT.reply_to(message, "🚫 Rejeitado.")

        p_key = f"p_{cmd.split('_')[1]}"
        if p_key in PRODUCTS:
            pkg = PRODUCTS[p_key]
            BOT.send_message(target_id, f"✅ <b>Approved!</b>\n{pkg['name']}\n\nLink: {pkg['delivery']}", parse_mode="HTML")
            BOT.reply_to(message, f"✅ Liberado para {target_id}")
    except Exception as e:
        BOT.reply_to(message, f"Erro: {e}")

# --- PAGAMENTO VIA STARS ---
@BOT.callback_query_handler(func=lambda call: call.data.startswith('stars_'))
def pay_stars(call):
    p = PRODUCTS[call.data.replace('stars_', '')]
    BOT.send_invoice(call.message.chat.id, p['name'], "Instant Access", call.data.replace('stars_', ''), "", "XTR", [types.LabeledPrice(p['name'], p['price'])])

@BOT.pre_checkout_query_handler(func=lambda q: True)
def checkout(q): BOT.answer_pre_checkout_query(q.id, ok=True)

@BOT.message_handler(content_types=['successful_payment'])
def got_payment(message):
    payload = message.successful_payment.invoice_payload
    BOT.send_message(message.chat.id, f"🎉 <b>CONFIRMED!</b>\nLink: {PRODUCTS[payload]['delivery']}", parse_mode="HTML")

# --- INICIALIZAÇÃO SEGURA (EVITA ERRO 409) ---
if __name__ == "__main__":
    keep_alive()
    try:
        BOT.remove_webhook()
        time.sleep(2)
    except: pass
    print("Bot Conectado com Sucesso!")
    BOT.infinity_polling(skip_pending=True)
