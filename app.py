import os
import base64
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ============ GPT TEXT ============
async def ask_gpt(text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are KiraBot. Speak English and Russian."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content


# ============ GPT IMAGE ============
async def generate_image(prompt):
    img = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="512x512"
    )
    img_b64 = img.data[0].b64_json
    return base64.b64decode(img_b64)


# ============ HANDLERS ============
async def start(update: Update, context):
    await update.message.reply_text(
        "🔥 Привет! Я KiraBot.\n\n"
        "Я умею:\n"
        "• Создавать картинки\n"
        "• Отвечать на вопросы\n"
        "• Переводить\n"
        "• Анализировать фото\n\n"
        "Просто напиши мне ✍️"
    )


async def handle_message(update: Update, context):
    text = update.message.text

    # If user asks to create picture
    if any(word in text.lower() for word in ["создай", "нарисуй", "draw", "generate"]):
        img_bytes = await generate_image(text)
        await update.message.reply_photo(img_bytes)
        return

    # General chat
    reply = await ask_gpt(text)
    await update.message.reply_text(reply)


# ============ TELEGRAM APP ============
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT, handle_message))


# ============ WEBHOOK ============
async def webhook(request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return web.Response(text="OK")


app = web.Application()
app.router.add_post("/", webhook)

web.run_app(app, port=10000)