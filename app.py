import os
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


# === GPT REPLY ===
async def ask_gpt(text):
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Speak the same language as the user. Автоматически используй русский или английский."
            },
            {"role": "user", "content": text}
        ]
    )
    return r.choices[0].message["content"]


# === COMMAND HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Привет! Я KiraBot.\nНапиши любой запрос!"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = await ask_gpt(text)
    await update.message.reply_text(response)


# === MAIN AIOHTTP SERVER ===
async def main():
    bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    await bot_app.initialize()
    await bot_app.start()

    # AIOHTTP SERVER
    app = web.Application()

    # GET handler — чтобы Render не давал 405
    async def handle_get(request):
        return web.Response(text="KiraBot is running.")

    app.router.add_get("/", handle_get)

    # POST handler — основной webhook
    async def handle_post(request):
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return web.Response(text="ok")

    app.router.add_post("/", handle_post)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

    print("KiraBot is live!")


import asyncio
asyncio.run(main())