import os
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 🔑 Configurar keys desde variables de entorno
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"] # Debe ser la URL base de tu servicio en Render

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)

# --- Lógica de Gemini ---

# Función para generar respuesta con Gemini (solo fútbol)
def generar_respuesta_gemini(pregunta):
    try:
        # Nota: El generador de contenido funciona en un hilo de Python,
        # pero es bueno asegurarse de que no bloquea si es posible.
        modelo = genai.GenerativeModel("models/gemini-2.5-flash")
        respuesta = modelo.generate_content(
            f"Responde de forma experta y solo sobre fútbol: {pregunta}"
        )
        return respuesta.text
    except Exception as e:
        return f"❌ Error al generar respuesta: {e}"

# --- Comandos y Handlers de Telegram ---

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
    # Esta función se llama desde un proceso asíncrono (el handler),
    # pero el método generar_respuesta_gemini es síncrono.
    # Usamos run_in_executor para no bloquear el bucle de eventos,
    # aunque para esta tarea, a veces no es estrictamente necesario,
    # pero es una buena práctica para llamadas de red/I/O síncronas.
    loop = asyncio.get_event_loop()
    respuesta = await loop.run_in_executor(None, generar_respuesta_gemini, pregunta)
    
    await update.message.reply_text(respuesta)


# --- Configuración del Bot ---

# ⚙️ Función para configurar el bot (NO lo ejecuta)
def setup_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    
    return app

# Inicializar el bot globalmente. Esto se hace una sola vez.
BOT_APP = setup_bot()


# --- Flask App (El Único Servidor Web) ---

flask_app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))

@flask_app.route("/")
def home():
    # Render comprobará este endpoint.
    return "✅ Bot de fútbol activo y corriendo correctamente en el puerto {}".format(PORT), 200

# Endpoint que recibe las peticiones de Telegram
@flask_app.route("/webhook", methods=["POST"])
async def telegram_webhook():
    # Obtener el cuerpo JSON de la petición (la actualización de Telegram)
    if request.method == "POST":
        update_json = request.get_json(force=True)
        
        # Crear un objeto Update de Telegram y procesarlo
        update = Update.de_json(update_json, BOT_APP.bot)
        
        # Procesar la actualización con el Application (Bot)
        # Esto dispara los handlers (start, help, responder)
        await BOT_APP.process_update(update)
        
    return jsonify({"status": "ok"}), 200 # Telegram espera un 200 OK

# --- Función de Inicio para Render ---

# Esta función se ejecutará al inicio para establecer la URL del webhook en Telegram
async def set_telegram_webhook():
    webhook_path = "/webhook"
    full_webhook_url = f"{WEBHOOK_URL}{webhook_path}"
    
    print(f"🤖 Configurando Webhook en Telegram: {full_webhook_url}")
    
    # Esto es importante: asegurar que el webhook está apuntando a la ruta correcta en Flask
    await BOT_APP.bot.set_webhook(url=full_webhook_url)
    print("✅ Webhook establecido con éxito.")

def run_setup_and_flask():
    # 1. Ejecutar la configuración asíncrona (set_webhook)
    # Creamos un nuevo bucle de eventos para esta tarea de inicio síncrono.
    try:
        asyncio.run(set_telegram_webhook())
    except Exception as e:
        print(f"⚠️ Error al intentar establecer el webhook: {e}")
        # La aplicación debe continuar ejecutándose para que Render pueda escanear el puerto.

    # 2. Iniciar el servidor Flask (el único servidor)
    # '0.0.0.0' hace que escuche en todas las interfaces, como requiere Render.
    print(f"🖥️ Flask iniciando en 0.0.0.0:{PORT}")
    
    # Nota: Usar el servidor de desarrollo de Flask (flask_app.run) está bien para Render/Heroku.
    # Si quieres un servidor más robusto (producción), usarías gunicorn/waitress.
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)


# 🚀 Lanzar la Aplicación Principal
if __name__ == "__main__":
    # SOLO ejecutamos la función que inicia Flask, el único que enlaza al puerto.
    run_setup_and_flask()

