import os
import base64
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# === GPT TEXT ===
async def ask_gpt(text):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Kira, an AI assistant."},
            {"role": "user", "content": text}
        ]
    )
    return res.choices[0].message["content"]


# === IMAGE GEN ===
async def generate_image(prompt):
    res = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )
    b64_img = res.data[0].b64_json
    return base64.b64decode(b64_img)


# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Привет! Я KiraBot.\n\n"
        "Я умею:\n"
        "• Создавать картинки\n"
        "• Отвечать на вопросы\n"
        "• Переводить\n"
        "• Анализировать фото\n"
        "Напиши любой запрос!"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()

    if msg.startswith("картинка"):
        prompt = msg.replace("картинка", "").strip()
        await update.message.reply_text("Генерирую изображение...")
        img = await generate_image(prompt)
        await update.message.reply_photo(img)
        return

    response = await ask_gpt(update.message.text)
    await update.message.reply_text(response)


# === TELEGRAM APP ===
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


# === WEBHOOK HANDLER ===
async def webhook_handler(request):
    data = await request.json()
    await telegram_app.initialize()
    await telegram_app.process_update(
        Update.de_json(data, telegram_app.bot)
    )
    return web.Response(status=200, text="ok")


# === SERVER START ===
app = web.Application()
app.router.add_post("/", webhook_handler)


if __name__ == "__main__":
    web.run_app(app, port=10000)