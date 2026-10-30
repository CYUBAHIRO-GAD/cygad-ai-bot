import asyncio
import logging
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

from .config import TELEGRAM_BOT_TOKEN, ADMIN_IDS, BOT_NAME
from .database import (
    init_db, touch_user, get_language, set_language,
    save_message, clear_history, counts
)
from .ai import ask, ask_photo, generate_image
from .resources import format_resources

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("cygad")

MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🧠 Ask CYGAD", callback_data="ask"),
     InlineKeyboardButton("🎓 Project ideas", callback_data="ideas")],
    [InlineKeyboardButton("🔌 Circuit help", callback_data="circuit"),
     InlineKeyboardButton("💻 Code help", callback_data="code")],
    [InlineKeyboardButton("📚 Resources", callback_data="resources"),
     InlineKeyboardButton("🌐 Language", callback_data="language")],
    [InlineKeyboardButton("🖼 Generate image", callback_data="image"),
     InlineKeyboardButton("ℹ️ About", callback_data="about")]
])

def split_message(text: str, limit: int = 3900):
    parts = []
    text = text or "No response was returned."
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:].lstrip()
    if text:
        parts.append(text)
    return parts

async def send_long(message, text):
    for part in split_message(text):
        await message.reply_text(part, disable_web_page_preview=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    touch_user(user.id, user.username or "")
    text = (
        f"⚡ Welcome to {BOT_NAME}!\n\n"
        "Your engineering learning assistant for IoT, electronics, embedded systems, "
        "robotics and automation.\n\n"
        "You can ask questions, request project ideas, generate code, share circuit "
        "photos or explore engineering resources.\n\n"
        "Languages: English • Kinyarwanda • Français\n"
        "Choose an option below or simply type your question."
    )
    await update.effective_message.reply_text(text, reply_markup=MENU)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "/start - Main menu\n"
        "/help - Show commands\n"
        "/project [topic] - Final-year project ideas\n"
        "/resources - Engineering websites and documentation\n"
        "/language - Choose English, Kinyarwanda or French\n"
        "/image [description] - Generate an engineering illustration\n"
        "/reset - Clear your saved conversation history\n"
        "/stats - Administrator statistics\n\n"
        "Send a circuit photo with an optional caption to request analysis.",
        reply_markup=MENU
    )

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
    user = update.effective_user
    touch_user(user.id, user.username or "")
    language = get_language(user.id)
    status = await update.effective_message.reply_text("⚙️ CYGAD is working on your engineering question...")
    try:
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        answer = await asyncio.to_thread(ask, user.id, prompt, language)
        await status.delete()
        await send_long(update.effective_message, answer)
    except Exception as exc:
        log.exception("AI answer failed")
        safe_error = (
            "CYGAD could not complete that request. Please check the server's internet "
            "connection, API key, API billing and configured model. "
            f"Technical error: {type(exc).__name__}."
        )
        await status.edit_text(safe_error)

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer_question(update, context, update.message.text)

async def project_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args).strip() or "general IoT and embedded systems"
    prompt = (
        "Suggest 5 feasible university final-year projects related to "
        f"{topic}. For each include: title, problem statement, objectives, "
        "components, block-diagram description, methodology, implementation stages, "
        "testing plan, risks, expected results and possible improvements. "
        "Keep projects realistic for students and state assumptions."
    )
    await answer_question(update, context, prompt)

async def resources_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📚 CYGAD engineering resources\n\n" + format_resources(),
        disable_web_page_preview=True
    )

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("English", callback_data="lang_en"),
        InlineKeyboardButton("Kinyarwanda", callback_data="lang_rw"),
        InlineKeyboardButton("Français", callback_data="lang_fr")
    ]])
    await update.effective_message.reply_text("Choose your preferred language:", reply_markup=keyboard)

async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args).strip()
    if not prompt:
        await update.effective_message.reply_text(
            "Usage: /image ESP32 smart irrigation prototype with soil-moisture sensor and pump"
        )
        return
    status = await update.effective_message.reply_text("🎨 Generating your engineering illustration...")
    try:
        raw = await asyncio.to_thread(generate_image, prompt)
        photo = BytesIO(raw)
        photo.name = "cygad-engineering-concept.png"
        await update.effective_message.reply_photo(
            photo=photo,
            caption="Concept illustration. Verify datasheets, pinouts and electrical ratings before building."
        )
        await status.delete()
    except Exception as exc:
        log.exception("Image generation failed")
        await status.edit_text(
            "Image generation failed. Check API image-model access, billing and internet. "
            f"Technical error: {type(exc).__name__}."
        )

async def photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = await update.effective_message.reply_text("📷 Analyzing your engineering photo...")
    try:
        photo = update.message.photo[-1]
        telegram_file = await context.bot.get_file(photo.file_id)
        raw = bytes(await telegram_file.download_as_bytearray())
        answer = await asyncio.to_thread(
            ask_photo,
            update.message.caption or "",
            raw,
            "image/jpeg"
        )
        await status.delete()
        await send_long(update.effective_message, answer)
    except Exception as exc:
        log.exception("Photo analysis failed")
        await status.edit_text(
            "Photo analysis failed. Check cloud vision access, API billing and internet. "
            f"Technical error: {type(exc).__name__}."
        )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_history(update.effective_user.id)
    await update.effective_message.reply_text("Your saved CYGAD conversation history has been cleared.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.effective_message.reply_text("This command is restricted to CYGAD administrators.")
        return
    users, messages = counts()
    await update.effective_message.reply_text(
        f"📊 CYGAD statistics\nRegistered users: {users}\nSaved messages: {messages}"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("lang_"):
        language = data.split("_", 1)[1]
        set_language(query.from_user.id, language)
        labels = {
            "en": "Language set to English.",
            "rw": "Ururimi rwashyizwe mu Kinyarwanda.",
            "fr": "Langue définie sur le français."
        }
        await query.edit_message_text(labels[language])
        return

    if data == "language":
        await language_command_from_callback(query)
    elif data == "resources":
        await query.edit_message_text(
            "📚 Engineering resources\n\n" + format_resources(),
            disable_web_page_preview=True
        )
    elif data == "about":
        await query.edit_message_text(
            "CYGAD AI is an educational assistant focused on IoT, electronics, "
            "embedded systems, robotics and automation.\n\n"
            "Cloud AI, photo analysis, web search and image generation need internet "
            "and may incur API costs. Verify critical circuit designs against datasheets."
        )
    else:
        prompts = {
            "ask": "Introduce yourself briefly as CYGAD AI and invite an IoT or embedded-systems question.",
            "ideas": "Suggest 5 feasible university final-year IoT and embedded-systems project ideas.",
            "circuit": "Help me design or troubleshoot an electronics circuit. Ask for the board, components, voltage and current if important details are missing.",
            "code": "Help me write or debug embedded code. Ask for the board, programming language and error details when needed.",
            "image": "To generate a project illustration, send /image followed by your description."
        }
        await query.edit_message_text("Tell CYGAD what you want to learn or build.")
        if data in prompts:
            await context.bot.send_message(query.message.chat_id, prompts[data])

async def language_command_from_callback(query):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("English", callback_data="lang_en"),
        InlineKeyboardButton("Kinyarwanda", callback_data="lang_rw"),
        InlineKeyboardButton("Français", callback_data="lang_fr")
    ]])
    await query.edit_message_text("Choose your preferred language:", reply_markup=keyboard)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled Telegram bot error", exc_info=context.error)

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN. Copy .env.example to .env and add your BotFather token.")
    if not ADMIN_IDS:
        log.warning("ADMIN_IDS is empty; /stats will be unavailable to everyone.")
    init_db()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("project", project_command))
    app.add_handler(CommandHandler("resources", resources_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("image", image_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.PHOTO, photo_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    app.add_error_handler(error_handler)

    log.info("Starting %s in Telegram polling mode", BOT_NAME)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
