from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import requests
import os

# 🔑 Cargar claves desde las variables de entorno en Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

# 🚨 Verificación básica
if not TELEGRAM_TOKEN or not GEMINI_API_KEY or not API_FOOTBALL_KEY:
    raise ValueError("❌ Faltan una o más API keys. Verifica tus variables de entorno en Render.")

# ⚙️ Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)

# 🧠 Función para generar respuesta con Gemini
def generar_respuesta_gemini(pregunta):
    try:
        modelo = genai.GenerativeModel("models/gemini-2.5-flash")
        respuesta = modelo.generate_content(
            f"Responde de forma breve, actualizada y experta sobre fútbol: {pregunta}"
        )
        return respuesta.text
    except Exception as e:
        return f"❌ Error al generar respuesta: {e}"

# ⚽ Función para obtener información del Club América
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

# 🏁 Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚽ ¡Hola! Soy tu bot de fútbol. Pregúntame lo que quieras sobre el mundo del fútbol.")

# 📝 Comando /help
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Puedes preguntarme cosas como:\n"
        "- ¿Quién ganó el mundial 2010?\n"
        "- ¿Cuántos títulos tiene el América?\n"
        "- Resultados recientes de equipos o ligas."
    )

# 💬 Responder preguntas
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text.lower()

    # 🚫 Solo responde sobre fútbol
    temas_futbol = ["futbol", "fútbol", "liga", "mundial", "gol", "jugador", "américa", "real madrid", "barcelona", "chivas", "equipo", "partido"]
    if not any(palabra in pregunta for palabra in temas_futbol):
        await update.message.reply_text("⚠️ Solo respondo preguntas sobre fútbol ⚽😉")
        return

    # ⚽ Si preguntan por América
    if "américa" in pregunta:
        respuesta = obtener_info_america()
        await update.message.reply_text(respuesta, parse_mode="Markdown")
        return

    # 💡 Si no, usa Gemini
    respuesta = generar_respuesta_gemini(pregunta)
    await update.message.reply_text(respuesta)

# 🚀 Iniciar el bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    print("🤖 Bot de fútbol iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
