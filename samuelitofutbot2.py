import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import requests
from dotenv import load_dotenv

# 🧾 Cargar variables de entorno desde .env
load_dotenv()

# 🔑 Leer claves desde variables de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

# ⚙️ Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
modelo_gemini = genai.GenerativeModel("models/gemini-2.5-flash")

# 🧠 Generar respuesta con Gemini
def generar_respuesta_gemini(pregunta):
    try:
        respuesta = modelo_gemini.generate_content(
            f"Responde de forma breve y experta sobre fútbol: {pregunta}"
        )
        return respuesta.text if hasattr(respuesta, "text") and respuesta.text else "No tengo información precisa sobre eso ⚽."
    except Exception as e:
        return f"❌ Error al generar respuesta con Gemini: {e}"

# ⚽ Información del Club América
def obtener_info_america():
    try:
        url = "https://api-football-v1.p.rapidapi.com/v3/teams?search=america"
        headers = {
            "X-RapidAPI-Key": API_FOOTBALL_KEY,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        r = requests.get(url, headers=headers)
        data = r.json()

        if data.get("response"):
            equipo = data["response"][0]["team"]
            nombre = equipo["name"]
            pais = equipo["country"]
            return f"🇲🇽 *{nombre}* juega en {pais} y actualmente tiene *16 títulos de liga*. ¡El más grande! 💛💙"
        else:
            return "No encontré información del América ahora mismo."
    except Exception as e:
        return f"⚠️ Error al consultar API-FOOTBALL: {e}"

# 🏁 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ ¡Hola! Soy *Samuelito FutBot*, tu asistente experto en fútbol.\n"
        "Pregúntame sobre equipos, jugadores o resultados. 👟",
        parse_mode="Markdown"
    )

# 📝 /help
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Ejemplos de lo que puedes preguntar:\n"
        "- ¿Quién ganó el mundial 2010?\n"
        "- ¿Cuántos títulos tiene el América?\n"
        "- Últimos resultados del Real Madrid.\n\n"
        "⚠️ Solo hablo de fútbol 😉"
    )

# 💬 Mensajes del usuario
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text.lower()

    # 🧩 Palabras clave futboleras
    temas_futbol = [
        "futbol", "fútbol", "liga", "mundial", "gol", "jugador", "américa",
        "real madrid", "barcelona", "chivas", "pumas", "cruz azul", "club",
        "equipo", "partido", "marcador", "selección", "balón", "campeonato"
    ]

    # 🚫 Si no es de fútbol, ignorar
    if not any(palabra in pregunta for palabra in temas_futbol):
        await update.message.reply_text("⚠️ Solo respondo preguntas sobre fútbol, bro ⚽😉")
        return

    # ⚽ Preguntas específicas del América
    if "américa" in pregunta:
        respuesta = obtener_info_america()
        await update.message.reply_text(respuesta, parse_mode="Markdown")
        return

    # 🧠 Respuesta general con Gemini
    respuesta = generar_respuesta_gemini(pregunta)
    await update.message.reply_text(respuesta)

# 🚀 Inicio del bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    print("🤖 Samuelito FutBot está en línea...")
    app.run_polling()

# 🧩 Ejecutar
if __name__ == "__main__":
    main()
