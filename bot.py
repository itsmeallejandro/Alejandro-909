import os
import logging
import zipfile
from yt_dlp import YoutubeDL
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Configuración del bot
BOT_TOKEN = os.getenv('5550034274:AAH4BSeWk-mpM4lTo_y5JSYrQQALxZSHFoM')
BOT_USERNAME = '@itsmeallejandro'
BOT_DESCRIPTION = """
🎥 **Descargador Universal** 🎵
¡Hola! Soy un bot creado por @itsmeallejandro. Conmigo puedes descargar:
- Vídeos de YouTube, TikTok, Instagram, etc.
- Música de YouTube y más.
- Archivos de todo tipo (comprimidos en ZIP).

✨ **Características principales:**
✅ Descargas rápidas y directas.
✅ Soporte para múltiples plataformas.
✅ Selección de calidad (desde baja hasta altísima).
✅ Compresión automática en ZIP para archivos grandes.
✅ Interfaz minimalista y fácil de usar.

📌 **Cómo usarme:**
1. Envíame el enlace del contenido que deseas descargar.
2. Elige el formato y la calidad.
3. ¡Recibe el archivo directamente en el chat!

👤 **Creado por:** @itsmeallejandro
"""

# Configuración de yt-dlp
YDL_OPTS = {
    'restrictfilenames': True,
    'outtmpl': '%(title)s.%(ext)s',
    'quiet': True,
}

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Funciones principales
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    welcome_message = (
        f"👋 ¡Hola {user.first_name}! Soy tu asistente de descargas.\n\n"
        f"{BOT_DESCRIPTION}"
    )
    await update.message.reply_text(
        text=welcome_message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 Descargar Vídeo", callback_data="help_video")],
            [InlineKeyboardButton("🎵 Descargar Audio", callback_data="help_audio")],
            [InlineKeyboardButton("📦 Descargar Archivos", callback_data="help_files")],
            [InlineKeyboardButton("🌟 Soporte", url="https://t.me/itsmeallejandro")]
        ])
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url:
        await update.message.reply_text("Por favor, envía un enlace válido.")
        return

    # Mostrar opciones de descarga
    keyboard = [
        [InlineKeyboardButton("🎥 Descargar Vídeo", callback_data=f"video:{url}")],
        [InlineKeyboardButton("🎵 Descargar Audio", callback_data=f"audio:{url}")],
        [InlineKeyboardButton("📦 Descargar Archivo", callback_data=f"file:{url}")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "¿Qué formato deseas descargar?",
        reply_markup=reply_markup
    )

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, url, audio_only=False, file_only=False):
    try:
        opts = YDL_OPTS.copy()
        if audio_only:
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            })
        elif file_only:
            opts['format'] = 'best'
        else:
            opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            file_path = ydl.prepare_filename(info)
            ydl.process_info(info)

        # Comprimir archivos grandes en ZIP
        if os.path.getsize(file_path) > 50 * 1024 * 1024:  # 50 MB
            zip_path = file_path + '.zip'
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(file_path, os.path.basename(file_path))
            os.remove(file_path)
            file_path = zip_path

        if audio_only:
            await update.message.reply_audio(audio=open(file_path, 'rb'))
        elif file_only:
            await update.message.reply_document(document=open(file_path, 'rb'))
        else:
            await update.message.reply_video(video=open(file_path, 'rb'))

        os.remove(file_path)  # Eliminar el archivo después de enviarlo
    except Exception as e:
        await update.message.reply_text(f"Error al descargar: {str(e)}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cancel":
        await query.edit_message_text("Descarga cancelada.")
    elif data.startswith("video:"):
        url = data.split(":", 1)[1]
        await download_and_send(query, context, url, audio_only=False)
    elif data.startswith("audio:"):
        url = data.split(":", 1)[1]
        await download_and_send(query, context, url, audio_only=True)
    elif data.startswith("file:"):
        url = data.split(":", 1)[1]
        await download_and_send(query, context, url, file_only=True)
    elif data == "help_video":
        await query.edit_message_text(
            "📥 **Descargar Vídeo:**\n"
            "Envía el enlace del vídeo que deseas descargar y selecciona la opción 'Descargar Vídeo'.",
            parse_mode='Markdown'
        )
    elif data == "help_audio":
        await query.edit_message_text(
            "🎵 **Descargar Audio:**\n"
            "Envía el enlace de la canción o vídeo que deseas descargar y selecciona la opción 'Descargar Audio'.",
            parse_mode='Markdown'
        )
    elif data == "help_files":
        await query.edit_message_text(
            "📦 **Descargar Archivos:**\n"
            "Envía el enlace del archivo que deseas descargar y selecciona la opción 'Descargar Archivo'.",
            parse_mode='Markdown'
        )

# Configuración del bot de Telegram
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Iniciar el bot
    application.run_polling()

if __name__ == "__main__":
    main()
