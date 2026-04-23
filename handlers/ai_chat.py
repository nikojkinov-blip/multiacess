import random
import asyncio
from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import UserModel, db
from config import MAX_REQUESTS_PER_DAY_FREE, MAX_REQUESTS_PER_DAY_PAID
from keyboards.inline import get_main_keyboard

router = Router()

AI_RESPONSES = [
    "🤖 Ваш запрос обрабатывается ChatGPT-4o. Ожидайте ответа...",
    "⚙️ Запрос в очереди. Перед вами {n} пользователей.",
    "🔄 Claude 3.5 Sonnet генерирует ответ. Пожалуйста, подождите.",
    "🧠 Нейросеть анализирует запрос. Это займёт несколько секунд.",
    "💭 ChatGPT-4o думает над ответом...",
    "🔮 Gemini 1.5 Pro обрабатывает ваш запрос.",
    "📊 Анализ данных... Ожидайте результат.",
    "🎯 Ваш запрос принят. Обработка идёт полным ходом."
]

IMAGE_RESPONSES = [
    "🎨 Midjourney v6 генерирует изображение по вашему запросу...",
    "🖼️ Ваше изображение в очереди на генерацию. Перед вами {n} запросов.",
    "✨ DALL-E 3 создаёт изображение. Это займёт 1-2 минуты.",
    "🌈 Генерация изображения запущена. Ожидайте результат."
]

FULL_RESPONSES = [
    "Вот ответ на ваш запрос:\n\n[Содержимое ответа ChatGPT-4o]\n\nЭто демонстрационный ответ.",
    "Claude 3.5 Sonnet отвечает:\n\n[Сгенерированный ответ]\n\nНадеюсь, это поможет!",
    "Gemini 1.5 Pro:\n\n[Результат обработки]\n\nЕсть вопросы? Обращайтесь!",
]

@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_request(message: Message):
    user = UserModel.get(message.from_user.id)
    
    if not user:
        await message.answer("Сначала используйте /start", reply_markup=get_main_keyboard())
        return
    
    if not UserModel.is_premium(message.from_user.id):
        if user['requests_today'] >= MAX_REQUESTS_PER_DAY_FREE:
            builder = InlineKeyboardBuilder()
            builder.button(text="🔐 Получить доступ", callback_data="get_access")
            
            await message.answer(
                f"❌ Достигнут лимит бесплатных запросов ({MAX_REQUESTS_PER_DAY_FREE}/день).\n"
                f"Получите Premium доступ для неограниченного использования!",
                reply_markup=builder.as_markup()
            )
            return
    else:
        if user['requests_today'] >= MAX_REQUESTS_PER_DAY_PAID:
            await message.answer(
                f"⚠️ Достигнут дневной лимит запросов ({MAX_REQUESTS_PER_DAY_PAID}).\n"
                f"Лимит сбросится завтра."
            )
            return
    
    UserModel.increment_requests(message.from_user.id)
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    queue_position = random.randint(0, 5)
    if queue_position > 0:
        response = random.choice(AI_RESPONSES).replace("{n}", str(queue_position))
        await message.answer(response)
        await asyncio.sleep(random.uniform(2, 4))
    
    if random.random() < 0.7:
        final_response = random.choice(FULL_RESPONSES)
    else:
        final_response = f"✅ Запрос обработан!\n\n{random.choice(FULL_RESPONSES)}"
    
    await message.answer(final_response)

@router.message(F.photo)
async def handle_image_request(message: Message):
    user = UserModel.get(message.from_user.id)
    
    if not user:
        await message.answer("Сначала используйте /start", reply_markup=get_main_keyboard())
        return
    
    if not UserModel.is_premium(message.from_user.id):
        builder = InlineKeyboardBuilder()
        builder.button(text="🔐 Получить доступ", callback_data="get_access")
        
        await message.answer(
            "❌ Генерация изображений доступна только Premium пользователям.\n"
            "Получите доступ для использования Midjourney и DALL-E 3!",
            reply_markup=builder.as_markup()
        )
        return
    
    UserModel.increment_requests(message.from_user.id)
    
    await message.bot.send_chat_action(message.chat.id, "upload_photo")
    
    queue_position = random.randint(1, 4)
    response = random.choice(IMAGE_RESPONSES).replace("{n}", str(queue_position))
    await message.answer(response)
    
    await asyncio.sleep(random.uniform(3, 5))
    
    await message.answer(
        "✅ Изображение сгенерировано!\n\n"
        "[Ссылка на сгенерированное изображение]\n\n"
        "Спасибо за использование Midjourney v6!"
    )

@router.message(F.voice | F.video_note)
async def handle_media_request(message: Message):
    await message.answer(
        "❌ Данный тип сообщений не поддерживается.\n"
        "Отправьте текстовый запрос или изображение."
    )