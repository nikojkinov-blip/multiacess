from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


@router.callback_query(F.data == "open_webapp")
async def open_webapp(call: CallbackQuery):
    """Открыть WebApp"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🚀 Открыть приложение",
        web_app=WebAppInfo(url="https://твой-сайт.com/webapp")
    )
    
    await call.message.edit_text(
        "📱 <b>WebApp</b>\n\n"
        "Нажмите кнопку ниже чтобы открыть приложение.\n\n"
        "В приложении доступно:\n"
        "• 📊 Статистика\n"
        "• 🔑 API ключи\n"
        "• 💰 Платежи\n"
        "• 📞 Поддержка",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    """Обработка данных из WebApp"""
    data = message.web_app_data.data
    
    await message.answer(
        f"✅ Данные получены из WebApp!\n\n"
        f"<code>{data}</code>",
        parse_mode="HTML"
    )