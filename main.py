import telebot
from telebot import types

# --- CONFIGURAÇÕES ---
TOKEN = '8316409069:AAHpUmJCQJvKxwOV7QA_uiaFPuP5wxEjVsQ'  # <--- COLOQUE O TOKEN AQUI
BOT = telebot.TeleBot(TOKEN)

# Informações de Pagamento
EMAIL_PAYPAL = "rivaldomaurinholuis3@gmail.com"
CARTEIRA_USDT = "0x7bbf369df5a2c12dbcac4d9768703d318d74b491"
ADMIN_ID = 6953777986

# Definição dos pacotes
PRODUCTS = {
    'p_bronze': {
        'name': '🥉 BRONZE PACKAGE', 
        'label': '💵 $30.00 (1500 ⭐)', 
        'price': 1500, 
        'usd': '$30.00',
        'delivery': 'LINK_DO_VIDEO_BRONZE_AQUI'
    },
    'p_silver': {
        'name': '🥈 SILVER PACKAGE', 
        'label': '💵 $50.00 (2500 ⭐)', 
        'price': 2500, 
        'usd': '$50.00',
        'delivery': 'LINK_DO_VIDEO_SILVER_AQUI'
    },
    'p_diamond': {
        'name': '💎 DIAMOND PACKAGE', 
        'label': '💵 $100.00 (5000 ⭐)', 
        'price': 5000, 
        'usd': '$100.00',
        'delivery': 'LINK_DO_VIDEO_DIAMOND_AQUI'
    }
}

# --- MENU INICIAL (REINICIA O BOT) ---
@BOT.message_handler(commands=['start'])
def menu(message):
    # Esta função é chamada sempre que alguém digita /start
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, p in PRODUCTS.items():
        btn = types.InlineKeyboardButton(f"{p['name']} - {p['label']}", callback_data=f"select_{key}")
        markup.add(btn)
    
    welcome = "✨ **PREMIUM VIDEO STORE** ✨\n\nSelect your package below:"
    
    # Envia uma nova mensagem, agindo como um "reinício" visual
    BOT.send_message(message.chat.id, welcome, reply_markup=markup, parse_mode="Markdown")

# --- ESCOLHA DO MÉTODO ---
@BOT.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def choose_method(call):
    try:
        product_key = call.data.replace('select_', '')
        
        # Verifica se o produto existe para evitar erros
        if product_key not in PRODUCTS:
            return

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

# --- BOTÃO VOLTAR (REINICIA O MENU) ---
@BOT.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_main(call):
    # Apaga a mensagem atual e chama o menu novamente
    try:
        BOT.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass # Ignora se não der para apagar
    menu(call.message)

# --- MÉTODOS MANUAIS (PAYPAL E CRYPTO) ---
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
        print(f"Erro pagamento manual: {e}")

# --- RECEBIMENTO DO COMPROVANTE ---
@BOT.message_handler(content_types=['photo'])
def handle_receipt(message):
    BOT.reply_to(message, "🎯 **Receipt Received!** We are reviewing it. Please wait for admin approval.")
    
    user = message.from_user
    username = f"@{user.username}" if user.username else "Sem User"
    
    admin_msg = (f"🆕 **NOVO COMPROVANTE!**\n"
                 f"👤 De: {user.first_name} ({username})\n"
                 f"🆔 ID: `{user.id}`\n\n"
                 f"⚠️ *Verifique a imagem acima.*\n\n"
                 f"Para liberar, RESPONDA à foto com:\n"
                 f"`/liberar_bronze`\n`/liberar_silver`\n`/liberar_diamond`")
    
    try:
        BOT.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        BOT.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Erro ao enviar para admin: {e}")

# --- COMANDOS DE LIBERAÇÃO MANUAL (APENAS ADMIN) ---
@BOT.message_handler(commands=['liberar_bronze', 'liberar_silver', 'liberar_diamond'])
def manual_approve(message):
    if message.from_user.id != ADMIN_ID: 
        return 
        
    if not message.reply_to_message:
        return BOT.reply_to(message, "❌ Erro: Responda à foto do comprovante (encaminhada) com este comando.")

    try:
        # Pega o ID do usuário da mensagem original encaminhada
        if message.reply_to_message.forward_from:
            original_user_id = message.reply_to_message.forward_from.id
        else:
            # Tenta pegar do texto se o forward for oculto (opcional, requer lógica extra), 
            # mas aqui vamos avisar o erro.
            BOT.reply_to(message, "❌ Não consegui ler o ID (Usuário tem privacidade no encaminhamento). Envie o link manualmente.")
            return

        cmd = message.text.split('_')[1] # pega 'bronze', 'silver' ou 'diamond'
        p_key = f"p_{cmd}" 
        
        if p_key in PRODUCTS:
            link = PRODUCTS[p_key]['delivery']
            product_name = PRODUCTS[p_key]['name']
            
            # Envia para o cliente
            msg_client = f"✅ **Payment Approved!**\n\nPackage: {product_name}\n\nHere is your link:\n{link}"
            BOT.send_message(original_user_id, msg_client, parse_mode="Markdown")
            
            # Confirma para o admin
            BOT.reply_to(message, f"✅ Sucesso! Link do **{cmd}** enviado para o ID `{original_user_id}`.")
        else:
            BOT.reply_to(message, "❌ Erro: Pacote não encontrado no sistema.")
            
    except Exception as e:
        BOT.reply_to(message, f"❌ Erro: {e}")

# --- TELEGRAM STARS (AUTOMÁTICO) ---
@BOT.callback_query_handler(func=lambda call: call.data.startswith('stars_'))
def pay_stars(call):
    try:
        product_key = call.data.replace('stars_', '')
        p = PRODUCTS[product_key]
        
        BOT.send_invoice(
            call.message.chat.id, 
            title=f"{p['name']}", 
            description="Instant Access via Telegram Stars", 
            invoice_payload=product_key, 
            provider_token="", 
            currency="XTR", 
            prices=[types.LabeledPrice(label=p['name'], amount=p['price'])],
            start_parameter="premium-video"
        )
    except Exception as e:
        print(f"Erro Stars: {e}")

@BOT.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    BOT.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@BOT.message_handler(content_types=['successful_payment'])
def got_payment(message):
    try:
        payload = message.successful_payment.invoice_payload
        if payload in PRODUCTS:
            product = PRODUCTS[payload]
            BOT.send_message(message.chat.id, f"🎉 **PAYMENT CONFIRMED!**\n\nThank you!\n🚀 Link: {product['delivery']}", parse_mode="Markdown")
    except Exception as e:
        print(f"Erro processar pagamento: {e}")

print("Bot rodando...")
if __name__ == "__main__":
    BOT.infinity_polling()
