import os
import threading
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= ENV =================
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN not set")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set")

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# ================= BOT =================
ROLES = {
    "professional": "You are a professional AI assistant.",
    "comedy": "You are a funny AI assistant.",
    "mod": "You are a strict moderator AI.",
}

BLOCKED_WORDS = ["sex", "porn", "xxx", "adult", "nude", "fuck"]
user_roles = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("👔 Professional", callback_data="professional"),
            InlineKeyboardButton("😂 Comedy", callback_data="comedy"),
        ],
        [InlineKeyboardButton("🛡 Moderator", callback_data="mod")],
    ]
    await update.message.reply_text(
        "Select AI personality:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_roles[query.from_user.id] = query.data
    await query.edit_message_text(f"Role set to {query.data}")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id

    if any(word in user_text.lower() for word in BLOCKED_WORDS):
        await update.message.reply_text("❌ I can't respond to that.")
        return

    role = user_roles.get(user_id, "professional")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": ROLES[role]},
            {"role": "user", "content": user_text},
        ],
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=20,
        )
        reply = response.json()["choices"][0]["message"]["content"]
    except Exception:
        reply = "⚠️ AI server error. Try again."

    await update.message.reply_text(reply)

def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(set_role))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    application.run_polling()

# ================= MAIN =================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
