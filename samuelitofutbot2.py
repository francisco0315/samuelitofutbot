import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 🔑 Configurar keys desde variables de entorno
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Función para generar respuesta con Gemini (solo fútbol)
def generar_respuesta_gemini(pregunta):
    try:
        modelo = genai.GenerativeModel("models/gemini-2.5-flash")
        respuesta = modelo.generate_content(
            f"Responde de forma experta y solo sobre fútbol: {pregunta}"
        )
        return respuesta.text
    except Exception as e:
        return f"❌ Error al generar respuesta: {e}"

# Comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ ¡Hola! Soy tu bot de fútbol. Pregúntame lo que quieras sobre el fútbol y te respondo."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Puedes preguntarme cosas como:\n"
        "- Resultados recientes de equipos o ligas.\n"
        "- Información de jugadores y clubes.\n"
        "- Estadísticas y curiosidades futbolísticas."
    )

# Mensajes generales (todo fútbol)
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text
    respuesta = generar_respuesta_gemini(pregunta)
    await update.message.reply_text(respuesta)

# Función principal
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    # Puerto de Render
    PORT = int(os.environ.get("PORT", 10000))

    # Iniciar webhook
    print("🤖 Bot de fútbol iniciado con Webhook...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
