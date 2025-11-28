import os
import base64
import logging
from io import BytesIO

from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI, AuthenticationError, APIError

# =================== CONFIG ===================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", 10000))

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Установи переменные окружения TELEGRAM_TOKEN и OPENAI_API_KEY!")

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# =================== GPT TEXT ===================
async def ask_gpt(text: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",  # или просто "gpt-4o-mini"
            temperature=0.8,
            messages=[
                {"role": "system", "content": "Ты — KiraBot. Отвечай на русском и английском, будь дружелюбным и креативным."},
                {"role": "user", "content": text},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка GPT: {e}")
        return "Извини, не могу сейчас ответить — проблема с GPT 😔"


# =================== IMAGE GEN (DALL·E 3 / gpt-image-1) ===================
async def generate_image(prompt: str):
    try:
        response = await client.images.generate(
            model="dall-e-3",          # или "dall-e-2", если хочешь дешевле и быстрее
            prompt=prompt,
            n=1,
            size="1024x1024",          # dall-e-3 поддерживает 1024x1024, 1024x1792, 1792x1024
            quality="standard",        # или "hd" для dall-e-3
            response_format="b64_json",
        )
        img_b64 = response.data[0].b64_json
        return base64.b64decode(img_b64)
    except Exception as e:
        logger.error(f"Ошибка генерации изображения: {e}")
        return None


# =================== HANDLERS ===================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Привет! Я KiraBot.\n\n"
        "Я умею:\n"
        "• Создавать картинки (напиши «нарисуй», «создай», «draw» и т.д.)\n"
        "• Отвечать на любые вопросы\n"
        "• Переводить текст\n"
        "• Анализировать фото (просто пришли фото)\n\n"
        "Пиши что угодно! ✍️"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # === Генерация изображения ===
    trigger_words = ["нарисуй", "создай", "сгенерируй", "draw", "generate", "сделай картинку", "изобрази"]
    if any(word in text.lower() for word in trigger_words):
        await update.message.reply_chat_action("upload_photo")
        img_bytes = await generate_image(text)
        if img_bytes:
            await update.message.reply_photo(BytesIO(img_bytes), caption="🔥 Держи!")
        else:
            await update.message.reply_text("Не получилось сгенерировать картинку 😔 Попробуй ещё раз чуть позже.")
        return

    # === Обычный чат ===
    await update.message.reply_chat_action("typing")
    reply = await ask_gpt(text)
    await update.message.reply_text(reply)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Пример простой обработки фото через GPT-4 Vision
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Опиши подробно, что изображено на фото."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(photo_bytes).decode()}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        description = response.choices[0].message.content
        await update.message.reply_text(f"Анализ фото:\n\n{description}")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Не смог проанализировать фото 😔")


# =================== WEBHOOK ===================
async def webhook(request):
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return web.Response(text="ok")


# =================== MAIN ===================
if __name__ == "__main__":
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Команды и хендлеры
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Для локального тестирования polling
    # application.run_polling()

    # Для продакшена на сервере — webhook
    app = web.Application()
    app.router.add_post("/", webhook)

    # Установка вебхука (один раз)
    # await application.bot.set_webhook(url="https://your-domain.com/")

    web.run_app(app, host="0.0.0.0", port=PORT)