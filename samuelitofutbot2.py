import os
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 🔑 Configurar keys desde variables de entorno
# Se asume que estas variables de entorno están configuradas en Render.
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"] # URL base de tu servicio en Render

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)

# --- Lógica de Gemini ---

# Función síncrona para generar respuesta con Gemini (enfocada en fútbol, sin auto-filtro estricto)
def generar_respuesta_gemini(pregunta):
    try:
        modelo = genai.GenerativeModel("models/gemini-2.5-flash")
        
        # ⚽️ PROMPT MEJORADO: Establece el rol de experto en fútbol y elimina la instrucción 
        # de responder con el mensaje de error "⚠️ Solo respondo preguntas sobre fútbol ⚽️🌕".
        # Ahora el bot responderá a todas las preguntas de fútbol sin el rechazo anterior.
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

# --- Comandos y Handlers de Telegram ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mensaje de bienvenida específico de fútbol
    await update.message.reply_text(
        "⚽ ¡Hola! Soy tu bot de fútbol mundial experto en ligas como la Liga MX, Premier League, Champions, etc. Pregúntame lo que quieras sobre el fútbol y te respondo."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mensaje de ayuda específico de fútbol
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

# --- Configuración del Bot ---

# ⚙️ Función para configurar el objeto Application del bot
def setup_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    return app

# Inicializar el bot globalmente
BOT_APP = setup_bot()

# --- Flask App (El Único Servidor Web) ---

flask_app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))

@flask_app.route("/")
def home():
    # Render comprobará este endpoint para saber si la aplicación está viva.
    return "✅ Bot de fútbol activo y corriendo correctamente en el puerto {}".format(PORT), 200

# Endpoint que recibe las peticiones de Telegram
@flask_app.route("/webhook", methods=["POST"])
async def telegram_webhook():
    if request.method == "POST":
        update_json = request.get_json(force=True)
        
        # Procesar la actualización con el Application (Bot)
        update = Update.de_json(update_json, BOT_APP.bot)
        await BOT_APP.process_update(update)
        
    return jsonify({"status": "ok"}), 200 # Telegram espera un 200 OK

# --- Función de Configuración de Webhook (La que soluciona el conflicto) ---

async def set_telegram_webhook():
    webhook_path = "/webhook"
    full_webhook_url = f"{WEBHOOK_URL}{webhook_path}"
    
    # 1. LIMPIEZA: Eliminar cualquier webhook o polling anterior
    print("🧹 Eliminando configuraciones previas de Webhook/Polling...")
    # Esto resuelve el error "Conflict: terminated by other getUpdates request"
    await BOT_APP.bot.delete_webhook(drop_pending_updates=True) 
    print("✅ Limpieza completada.")

    # 2. CONFIGURACIÓN: Establecer el nuevo webhook
    print(f"🤖 Configurando Webhook en Telegram: {full_webhook_url}")
    await BOT_APP.bot.set_webhook(url=full_webhook_url)
    print("✅ Webhook establecido con éxito.")

# --- Función de Inicio para Render ---

def run_setup_and_flask():
    # 1. Ejecutar la configuración asíncrona (set_webhook)
    try:
        # `asyncio.run` ejecuta la tarea asíncrona de limpieza y setup.
        asyncio.run(set_telegram_webhook())
    except Exception as e:
        print(f"⚠️ Error FATAL al intentar establecer el webhook: {e}") 

    print(f"🖥️ Flask iniciando en 0.0.0.0:{PORT}")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)


# 🚀 Lanzar la Aplicación Principal
if __name__ == "__main__":
    run_setup_and_flask()
