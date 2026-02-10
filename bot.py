import os
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not TOKEN or not GROQ_API_KEY:
    raise ValueError("Missing environment variables")

ROLES = {
    "professional": "You are a professional AI assistant.",
    "comedy": "You are a funny AI assistant.",
    "mod": "You are a strict moderator AI.",
}

BLOCKED_WORDS = ["sex", "porn", "xxx", "adult", "nude", "fuck"]
user_roles = {}

flask_app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()

# ---------- START ----------
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

# ---------- ROLE ----------
async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_roles[query.from_user.id] = query.data
    await query.edit_message_text(f"Role set to {query.data}")

# ---------- CHAT ----------
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id

    if any(w in user_text.lower() for w in BLOCKED_WORDS):
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
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=20,
        )
        reply = r.json()["choices"][0]["message"]["content"]
    except:
        reply = "⚠️ AI server error."

    await update.message.reply_text(reply)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(set_role))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# ---------- WEBHOOK ----------
@flask_app.route("/", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"

@flask_app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
