from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from aiohttp import web
import os
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


# === GPT ANSWER ===
async def ask_gpt(text):
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are KiraBot — a bilingual assistant. "
                    "Автоматически определяй язык пользователя и отвечай на том же."
                )
            },
            {"role": "user", "content": text}
        ]
    )
    return result.choices[0].message["content"]


# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.from_user.language_code

    if lang.startswith("ru"):
        text = (
            "🔥 Привет! Я KiraBot.\n\n"
            "Я умею:\n"
            "• Создавать картинки\n"
            "• Отвечать на вопросы\n"
            "• Переводить\n"
            "• Анализировать фото\n"
            "Напиши что-нибудь!"
        )
    else:
        text = (
            "🔥 Hello! I'm KiraBot.\n\n"
            "I can:\n"
            "• Create images\n"
            "• Answer questions\n"
            "• Translate\n"
            "• Analyze photos\n"
            "Send me a message!"
        )

    await update.message.reply_text(text)


# === TEXT HANDLER ===
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    answer = await ask_gpt(user_text)
    await update.message.reply_text(answer)


# === TELEGRAM APP ===
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


# === WEBHOOK HANDLER (Render) ===
async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return web.Response(text="ok")


# === RUN SERVER ===
app = web.Application()
app.router.add_post("/", webhook_handler)

if __name__ == "__main__":
    web.run_app(app, port=10000)