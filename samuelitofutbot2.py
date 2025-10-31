from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
import google.generativeai as genai
import requests
import os

# 🔑 Variables de entorno (configuradas en Render)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)

# ⚽ Funciones de fútbol
def generar_respuesta_gemini(pregunta):
    try:
        modelo = genai.GenerativeModel("models/gemini-2.5-flash")
        respuesta = modelo.generate_content(
            f"Responde de forma breve y experta sobre fútbol: {pregunta}"
        )
        return respuesta.text
    except Exception as e:
        return f"❌ Error al generar respuesta: {e}"

def obtener_info_america():
    try:
        url = "https://v3.football.api-sports.io/teams?search=america"
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        r = requests.get(url, headers=headers)
        data = r.json()
        if data.get("response"):
            equipo = data["response"][0]["team"]
            nombre = equipo["name"]
            pais = equipo["country"]
            return f"🇲🇽 {nombre} juega en {pais} y actualmente tiene *16 títulos de liga*. ¡El más grande! 💛💙"
        else:
            return "No encontré información del América ahora mismo."
    except Exception as e:
        return f"⚠️ Error al consultar API-FOOTBALL: {e}"

# 🚀 Flask
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)

# /start
def start(update: Update, context):
    update.message.reply_text("⚽ ¡Hola! Soy tu bot de fútbol. Pregúntame lo que quieras sobre el mundo del fútbol.")

# /help
def help_command(update: Update, context):
    update.message.reply_text(
        "📋 Puedes preguntarme cosas como:\n"
        "- ¿Quién ganó el mundial 2010?\n"
        "- ¿Cuántos títulos tiene el América?\n"
        "- Resultados recientes de equipos o ligas."
    )

# Mensajes generales
def responder(update: Update, context):
    pregunta = update.message.text.lower()
    temas_futbol = ["futbol", "fútbol", "liga", "mundial", "gol", "jugador", "américa", "real madrid", "barcelona", "chivas", "equipo", "partido"]
    if not any(palabra in pregunta for palabra in temas_futbol):
        update.message.reply_text("⚠️ Solo respondo preguntas sobre fútbol ⚽😉")
        return

    if "américa" in pregunta:
        respuesta = obtener_info_america()
        update.message.reply_text(respuesta, parse_mode="Markdown")
        return

    respuesta = generar_respuesta_gemini(pregunta)
    update.message.reply_text(respuesta)

# Handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

# Ruta para recibir los webhooks de Telegram
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Ruta principal para pruebas
@app.route("/")
def index():
    return "Bot de fútbol corriendo 🔥"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
