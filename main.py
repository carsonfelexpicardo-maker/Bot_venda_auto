import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os
import re 

# --- CONFIGURAÇÃO DO SERVIDOR FALSO (PARA O RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "Estou vivo! O Bot está rodando."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURAÇÕES DO BOT ---
TOKEN = '8316409069:AAHpUmJCQJvKxwOV7QA_uiaFPuP5wxEjVsQ'  # <--- SEU TOKEN
BOT = telebot.TeleBot(TOKEN)

# Informações de Pagamento
EMAIL_PAYPAL = "rivaldomaurinholuis3@gmail.com"
CARTEIRA_USDT = "0x7bbf369df5a2c12dbcac4d9768703d318d74b491"
ADMIN_ID = 6953777986

# Definição dos pacotes
PRODUCTS = {
    'p_bronze': {
        'name': '🥉 BRONZE PACKAGE', 
        'label': '💵 $32.99 (1500 ⭐)', 
        'price': 1500, 
        'usd': '$32.99',
        'delivery': 'https://mega.nz/folder/PBdQwCTZ#1TAr86RRtZQD59pTH91TXQ'
    },
    'p_silver': {
        'name': '🥈 SILVER PACKAGE', 
        'label': '💵 $51.99 (2500 ⭐)', 
        'price': 2500, 
        'usd': '$51.99',
        'delivery': 'https://mega.nz/folder/nQ0USC4J#-aeGDupNTy_vgQCgX4jZFg'
    },
    'p_diamond': {
        'name': '💎 DIAMOND PACKAGE', 
        'label': '💵 $99.99 (5000 ⭐)', 
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
    
    welcome = "✨ **PREMIUM VIDEO STORE** ✨\n\nSelect your package below:"
    BOT.send_message(message.chat.id, welcome, reply_markup=markup, parse_mode="Markdown")

# --- ESCOLHA DO MÉTODO ---
@BOT.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def choose_method(call):
    try:
        product_key = call.data.replace('select_', '')
        if product_key not in PRODUCTS: return

        p = PRODUCTS[product_key]
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_stars = types.InlineKeyboardButton("⭐ Telegram Stars (Instant)", callback_data=f"stars_{product_key}")
        btn_paypal = types.InlineKeyboardButton("💳 PayPal (Manual Review)", callback_data=f"paypal_{product_key}")
        btn_crypto = types.InlineKeyboardButton("🔗 USDT - BEP20 (Manual Review)", callback_data=f"crypto_{product_key}")
        btn_back = types.InlineKeyboardButton("« Back", callback_data="back_to_main")
        markup.add(btn_stars, btn_paypal, btn_crypto, btn_back)
        
        text = f"📦 **{p['name']}**\n💰 **Value:** {p['usd']}\n\nChoose payment method:"
        BOT.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(f"Erro no menu: {e}")

@BOT.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_main(call):
    try: BOT.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    menu(call.message)

# --- MÉTODOS MANUAIS ---
@BOT.callback_query_handler(func=lambda call: call.data.startswith('paypal_') or call.data.startswith('crypto_'))
def manual_pay(call):
    try:
        if "paypal_" in call.data:
            product_key = call.data.replace('paypal_', '')
            p = PRODUCTS[product_key]
            msg = f"💳 **PAYPAL PAYMENT**\n\nAmount: **{p['usd']}**\nEmail: `{EMAIL_PAYPAL}`"
        else:
            product_key = call.data.replace('crypto_', '')
            p = PRODUCTS[product_key]
            msg = f"🔗 **USDT PAYMENT (BEP20)**\n\nAmount: **{p['usd']} USDT**\nNetwork: **BEP20**\nAddress: `{CARTEIRA_USDT}`"
        
        instructions = f"{msg}\n\n⚠️ Send the payment and then **send the screenshot (photo)** here in this chat."
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("« Back", callback_data=f"select_{product_key}"))
        
        BOT.edit_message_text(instructions, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(f"Erro manual: {e}")

# --- RECEBIMENTO DO COMPROVANTE ---
@BOT.message_handler(content_types=['photo'])
def handle_receipt(message):
    BOT.reply_to(message, "🎯 **Receipt Received!** We are reviewing it.")
    
    user = message.from_user
    username = f"@{user.username}" if user.username else "Sem User"
    
    # Mensagem para o Admin com os comandos de APROVAR ou REJEITAR
    admin_msg = (f"🆕 <b>NOVO COMPROVANTE!</b>\n"
                 f"👤 De: {user.first_name} ({username})\n"
                 f"🆔 ID: <code>{user.id}</code>\n\n"
                 f"⚠️ <b>Responda A ESTA MENSAGEM com:</b>\n"
                 f"✅ <code>/liberar_bronze</code>\n"
                 f"✅ <code>/liberar_silver</code>\n"
                 f"✅ <code>/liberar_diamond</code>\n"
                 f"❌ <code>/rejeitar</code>")
    try:
        BOT.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        BOT.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")
    except Exception as e:
        print(f"Erro admin: {e}")

# --- DECISÃO DO ADMIN (APROVAR OU REJEITAR) ---
@BOT.message_handler(commands=['liberar_bronze', 'liberar_silver', 'liberar_diamond', 'rejeitar'])
def admin_decision(message):
    if message.from_user.id != ADMIN_ID: return
    
    if not message.reply_to_message:
        return BOT.reply_to(message, "❌ Responda à MENSAGEM DE TEXTO do bot que contém o ID.")

    try:
        # Pega o ID do usuário original de dentro do texto da mensagem do bot
        text_original = message.reply_to_message.text or message.reply_to_message.caption or ""
        match = re.search(r"ID:\s*(\d+)", text_original)
        
        if match:
            original_user_id = int(match.group(1))
        else:
            return BOT.reply_to(message, "❌ Não achei o ID na mensagem. Responda à mensagem de texto com os dados do usuário.")

        command = message.text.split()[0] # Pega o comando (ex: /rejeitar)

        # --- LÓGICA DE REJEIÇÃO ---
        if "/rejeitar" in command:
            BOT.send_message(original_user_id, "❌ **Payment Rejected.**\n\nWe could not verify your payment or the amount is incorrect.\nPlease contact support if you think this is an error.", parse_mode="Markdown")
            BOT.reply_to(message, "🚫 **Comprovante Rejeitado.** O usuário foi notificado.")
            return

        # --- LÓGICA DE APROVAÇÃO ---
        cmd_type = command.split('_')[1] # pega 'bronze', 'silver' etc
        p_key = f"p_{cmd_type}"
        
        if p_key in PRODUCTS:
            pkg = PRODUCTS[p_key]
            BOT.send_message(original_user_id, f"✅ **Payment Approved!**\nPackage: {pkg['name']}\n\nLink:\n{pkg['delivery']}", parse_mode="Markdown")
            BOT.reply_to(message, f"✅ Liberado **{pkg['name']}** para ID `{original_user_id}`.", parse_mode="Markdown")
        else:
            BOT.reply_to(message, "❌ Pacote não encontrado no sistema.")
            
    except Exception as e:
        BOT.reply_to(message, f"❌ Erro ao processar: {e}")

# --- STARS (PAGAMENTO AUTOMÁTICO) ---
@BOT.callback_query_handler(func=lambda call: call.data.startswith('stars_'))
def pay_stars(call):
    try:
        product_key = call.data.replace('stars_', '')
        p = PRODUCTS[product_key]
        BOT.send_invoice(
            chat_id=call.message.chat.id, 
            title=p['name'], 
            description="Instant Access", 
            invoice_payload=product_key, 
            provider_token="", 
            currency="XTR", 
            prices=[types.LabeledPrice(label=p['name'], amount=p['price'])]
        )
    except: pass

@BOT.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    BOT.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@BOT.message_handler(content_types=['successful_payment'])
def got_payment(message):
    try:
        payload = message.successful_payment.invoice_payload
        if payload in PRODUCTS:
            BOT.send_message(message.chat.id, f"🎉 **PAYMENT CONFIRMED!**\n🚀 Link: {PRODUCTS[payload]['delivery']}", parse_mode="Markdown")
            BOT.send_message(ADMIN_ID, f"💰 **Venda Automática (Stars)!**\nPacote: {PRODUCTS[payload]['name']}\nUser: {message.from_user.first_name}")
    except: pass

# --- INICIALIZAÇÃO ---
print("Bot iniciando...")
keep_alive()
BOT.infinity_polling()
