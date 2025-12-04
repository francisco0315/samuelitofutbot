import os
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"] 

genai.configure(api_key=GEMINI_API_KEY)

def generar_respuesta_gemini(pregunta):
    try:
        modelo = genai.GenerativeModel("models/gemini-2.5-flash")

        prompt_final = (
            "Eres un experto en fútbol mundial (ligas, jugadores, resultados, historia, etc.). "
            "Responde a la siguiente pregunta de forma experta, enfocándote en el contexto futbolístico. "
            "Si el tema está fuera de tu experiencia o es muy ambiguo, responde de forma concisa.\n\n"
            f"Pregunta: {pregunta}"
        )
        
        respuesta = modelo.generate_content(prompt_final)
        return respuesta.text
    except Exception as e:
        return "❌ Error al generar respuesta de Gemini."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ ¡Hola! Soy tu bot de fútbol mundial experto en ligas como la Liga MX, Premier League, Champions, etc. Pregúntame lo que quieras sobre el fútbol y te respondo."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Puedes preguntarme cosas sobre fútbol mundial, como:\n"
        "- Resultados y tablas de posiciones de ligas (e.g., Liga MX, Premier League).\n"
        "- Información y estadísticas de jugadores (e.g., ¿Quién es el máximo goleador de la Champions?).\n"
        "- Historia de clubes y competiciones (e.g., ¿Quién ganó la Champions en 2005?)."
    )

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text
    loop = asyncio.get_event_loop()
    
    # Ejecutamos la función síncrona en un hilo separado para no bloquear el bucle de eventos
    respuesta = await loop.run_in_executor(None, generar_respuesta_gemini, pregunta)
    
    await update.message.reply_text(respuesta)

def setup_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    return app

BOT_APP = setup_bot()

flask_app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))

@flask_app.route("/")
def home():
    return "✅ Bot de fútbol activo y corriendo correctamente en el puerto {}".format(PORT), 200

@flask_app.route("/webhook", methods=["POST"])
async def telegram_webhook():
    if request.method == "POST":
        update_json = request.get_json(force=True)

        update = Update.de_json(update_json, BOT_APP.bot)
        await BOT_APP.process_update(update)
        
    return jsonify({"status": "ok"}), 200 

async def set_telegram_webhook():
    webhook_path = "/webhook"
    full_webhook_url = f"{WEBHOOK_URL}{webhook_path}"
    
    print("🧹 Eliminando configuraciones previas de Webhook/Polling...")
    await BOT_APP.bot.delete_webhook(drop_pending_updates=True) 
    print("✅ Limpieza completada.")

    print(f"🤖 Configurando Webhook en Telegram: {full_webhook_url}")
    await BOT_APP.bot.set_webhook(url=full_webhook_url)
    print("✅ Webhook establecido con éxito.")

def run_setup_and_flask():
    try:
        asyncio.run(set_telegram_webhook())
    except Exception as e:
        print(f"⚠️ Error FATAL al intentar establecer el webhook: {e}") 

    print(f"🖥️ Flask iniciando en 0.0.0.0:{PORT}")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == "__main__":
    run_setup_and_flask()

