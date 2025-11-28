from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from aiohttp import web
import os
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


# === GPT RESPONSE ===
async def ask_gpt(text):
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are KiraBot — an AI assistant for both English and Russian users.\n"
                    "Автоматически определяй язык пользователя (английский или русский) "
                    "и отвечай на том же языке. Be friendly, helpful, short and clear."
                )
            },
            {"role": "user", "content": text}
        ]
    )
    return result.choices[0].message["content"]


# === /start ===
async def start(update: Update, context):
    text_ru = (
        "🔥 Привет! Я KiraBot.\n\n"
        "Я умею:\n"
        "• Генерировать картинки\n"
        "• Отвечать на вопросы\n"
        "• Переводить\n"
        "• Анализировать фото\n"
        "Просто напиши любой запрос!"
    )

    text_en = (
        "🔥 Hello! I'm KiraBot.\n\n"
        "I can:\n"
        "• Generate images\n"
        "• Answer questions\n"
        "• Translate\n"
        "• Analyze photos\n"
        "Just send me any request!"
    )

    # Detect language
    user_language = update.message.from_user.language_code

    if user_language.startswith("ru"):
        await update.message.reply_text(text_ru)
    else:
        await update.message.reply_text(text_en)


# === Handle normal messages ===
async def handle_message(update: Update, context):
    text = update.message.text
    response = await ask_gpt(text)
    await update.message.reply_text(response)


# === TELEGRAM APP ===
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# === WEBHOOK (Render) ===
async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return web.Response(text="ok")


# === START SERVER ===
app = web.Application()
app.router.add_post("/", webhook_handler)

if __name__ == "__main__":
    web.run_app(app, port=10000)