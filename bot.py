import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ========= ENV VARIABLES =========
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is missing")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing")

# ========= AI ROLES =========
ROLES = {
    "professional": "You are a professional AI assistant.",
    "comedy": "You are a funny AI assistant.",
    "mod": "You are a strict moderator AI.",
}

BLOCKED_WORDS = ["sex", "porn", "xxx", "adult", "nude", "fuck"]
user_roles = {}

# ========= START =========
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

# ========= SET ROLE =========
async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_roles[query.from_user.id] = query.data
    await query.edit_message_text(f"✅ Role set to {query.data}")

# ========= CHAT =========
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id

    if any(w in user_text.lower() for w in BLOCKED_WORDS):
        await update.message.reply_text("❌ I can’t reply to that.")
        return

    role = user_roles.get(user_id, "professional")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": ROLES[role]},
            {"role": "user", "content": user_text},
        ],
    }

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        reply = res.json()["choices"][0]["message"]["content"]
    except:
        reply = "⚠️ AI server error. Try again."

    await update.message.reply_text(reply)

# ========= MAIN =========
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_role))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

