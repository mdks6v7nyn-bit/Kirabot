from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp import web
import os
from openai import OpenAI
import base64

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# === AI TEXT REPLY ===
async def ask_gpt(text):
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты KiraBot — умный ассистент, говори дружелюбно."},
            {"role": "user", "content": text}
        ]
    )
    return result.choices[0].message["content"]

# === IMAGE GENERATION ===
async def generate_image(prompt):
    img = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )
    img_b64 = img.data[0].b64_json
    return base64.b64decode(img_b64)

# === PHOTO ANALYSIS ===
async def analyze_photo(url):
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Опиши фото максимально подробно."},
            {"role": "user", "content": [
                {"type": "input_image", "image_url": url}
            ]}
        ]
    )
    return result.choices[0].message["content"]

# === TEXT TO VOICE ===
async def text_to_voice(text):
    audio = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    )
    return audio.read()

# === TRANSLATION ===
async def translate(text):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Переводи максимально точно на английский."},
            {"role": "user", "content": text}
        ]
    )
    return res.choices[0].message["content"]

# === COMMAND HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Привет! Я KiraBot.\n"
        "Вот что я умею:\n"
        "• ИИ-ответы\n"
        "• Создание картинок\n"
        "• Анализ фото\n"
        "• Переводы\n"
        "• Голосовые\n\n"
        "Напиши любой запрос!"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()

    if msg.startswith("картинка") or msg.startswith("image"):
        prompt = msg.replace("картинка", "").replace("image", "").strip()
        await update.message.reply_text("Генерирую изображение…")
        img = await generate_image(prompt)
        await update.message.reply_photo(img)
        return

    if msg.startswith("переведи"):
        text = msg.replace("переведи", "").strip()
        tr = await translate(text)
        await update.message.reply_text(tr)
        return

    if msg.startswith("голос"):
        text = msg.replace("голос", "").strip()
        audio = await text_to_voice(text)
        await update.message.reply_voice(audio)
        return

    answer = await ask_gpt(msg)
    await update.message.reply_text(answer)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    await update.message.reply_text("Анализирую фото…")
    res = await analyze_photo(file.file_path)
    await update.message.reply_text(res)

# === WEBHOOK SERVER ===
async def webhook(request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return web.Response()

application = Application.builder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

app = web.Application()
app.router.add_post("/", webhook)

if __name__ == "__main__":
    web.run_app(app, port=8080)
