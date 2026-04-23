import json
import uuid
from datetime import datetime, timedelta
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import (
    UserModel, ReferralModel, TicketModel, TicketMessageModel,
    PromoModel, PaymentModel, SimModel
)
from config import (
    ADMIN_IDS, CHANNEL_USERNAME, CHANNEL_ID, ACHIEVEMENTS,
    AI_PAYMENT_AMOUNT, SIM_PAYMENT_AMOUNT
)
from keyboards.inline import get_main_keyboard, get_sim_keyboard, get_profile_keyboard
from services.ai_support import AISupport

router = Router()


class SupportStates(StatesGroup):
    waiting_question = State()
    waiting_ticket_message = State()


# ============== ВСПОМОГАТЕЛЬНЫЕ ==============
async def check_channel_subscription(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ['left', 'kicked']
    except:
        return True


async def show_mode_selection(message: Message):
    """Показать выбор режима"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🤖 AI Access", callback_data="mode_ai")
    builder.button(text="📱 SIM.DL", callback_data="mode_sim")
    builder.button(text="📞 Поддержка", callback_data="support")
    builder.adjust(2, 1)
    
    await message.answer(
        "🚀 <b>Добро пожаловать!</b>\n\n"
        "Выберите режим:\n\n"
        "🤖 <b>AI Access</b> — ChatGPT, Midjourney\n"
        "📱 <b>SIM.DL</b> — активация сим-карт\n\n"
        "📞 <b>Поддержка</b> — задать вопрос или создать тикет",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


# ============== СТАРТ ==============
@router.message(CommandStart(deep_link=True))
async def start_deep_link(message: Message, command: CommandObject):
    user_id = message.from_user.id
    user = UserModel.get(user_id)
    
    if not user:
        UserModel.create(
            user_id=user_id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or '',
            last_name=message.from_user.last_name or ''
        )
        
        args = command.args
        if args and args.startswith("ref_"):
            referrer_code = args[4:]
            referrer = UserModel.get_by_referral(referrer_code)
            if referrer and referrer['user_id'] != user_id:
                UserModel.update(user_id, {'referred_by': referrer['user_id']})
                ReferralModel.add(referrer['user_id'], user_id)
                await message.answer(f"🎉 Вы приглашены пользователем {referrer.get('first_name', 'Unknown')}!")
    
    await show_mode_selection(message)


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user = UserModel.get(user_id)
    
    if not user:
        UserModel.create(
            user_id=user_id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or '',
            last_name=message.from_user.last_name or ''
        )
    
    await show_mode_selection(message)


# ============== ВЫБОР РЕЖИМА ==============
@router.callback_query(F.data == "mode_ai")
async def show_ai_menu(call: CallbackQuery):
    await call.message.edit_text(
        "🤖 <b>AI Access</b>\n\n"
        "Доступ к ChatGPT-4o, Claude 3.5, Midjourney v6\n\n"
        f"💰 Цена: {AI_PAYMENT_AMOUNT} ₽\n"
        f"🆓 Триал: 3 дня бесллатно\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "mode_sim")
async def show_sim_menu(call: CallbackQuery):
    await call.message.edit_text(
        "📱 <b>SIM.DL — Активация сим-карт</b>\n\n"
        "🔹 Доступ к базе номеров\n"
        "🔹 Оформление доверенного лица\n"
        "🔹 Все операторы\n\n"
        f"💰 Цена: {SIM_PAYMENT_AMOUNT} ₽\n\n"
        "Выберите действие:",
        reply_markup=get_sim_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "main_menu")
async def back_to_main(call: CallbackQuery):
    await show_mode_selection(call.message)
    await call.answer()


# ============== ПРОФИЛЬ ==============
@router.callback_query(F.data == "profile")
async def show_profile(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    if not user:
        await call.answer("Сначала /start")
        return
    
    ref_stats = ReferralModel.get_stats(user['user_id'])
    ai_premium = UserModel.is_ai_premium(call.from_user.id)
    sim_premium = UserModel.is_sim_premium(call.from_user.id)
    
    ai_status = "💎 Premium" if ai_premium else ("🆓 Триал" if user.get('trial_until') else "❌ Нет")
    sim_status = "✅ Активен" if sim_premium else "❌ Нет"
    
    text = f"""
👤 <b>Профиль</b>

🆔 ID: <code>{user['user_id']}</code>
📛 Имя: {user.get('first_name', '—')}
🤖 AI: {ai_status}
📱 SIM: {sim_status}
👥 Рефералов: {ref_stats['total']}
📊 Запросов: {user.get('total_requests', 0)}
"""
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 AI ключ", callback_data="my_key")
    builder.button(text="📱 SIM заказы", callback_data="sim_orders")
    builder.button(text="👥 Рефералы", callback_data="referral_menu")
    builder.button(text="🏆 Рейтинг", callback_data="rating")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(2, 2, 1)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


# ============== ПОДДЕРЖКА ==============
@router.callback_query(F.data == "support")
async def support_menu(call: CallbackQuery):
    """Меню поддержки"""
    existing = TicketModel.get_open_by_user(call.from_user.id)
    
    if existing:
        builder = InlineKeyboardBuilder()
        builder.button(text="📋 Мой тикет", callback_data=f"view_ticket_{existing['ticket_id']}")
        builder.button(text="💬 Автоответчик", callback_data="ask_question")
        builder.button(text="❌ Закрыть тикет", callback_data=f"close_ticket_{existing['ticket_id']}")
        builder.button(text="◀️ Назад", callback_data="main_menu")
        builder.adjust(1)
        
        await call.message.edit_text(
            f"📞 У вас есть открытый тикет #{existing['ticket_id']}\n\n"
            "Выберите действие:",
            reply_markup=builder.as_markup()
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Создать тикет", callback_data="create_ticket")
        builder.button(text="💬 Задать вопрос боту", callback_data="ask_question")
        builder.button(text="◀️ Назад", callback_data="main_menu")
        builder.adjust(1)
        
        await call.message.edit_text(
            "📞 <b>Поддержка</b>\n\n"
            "💬 <b>Автоответчик</b> — бот ответит на частые вопросы\n"
            "📝 <b>Тикет</b> — связь с оператором",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    
    await call.answer()


@router.callback_query(F.data == "create_ticket")
async def create_ticket_callback(call: CallbackQuery, state: FSMContext):
    """Создание тикета"""
    existing = TicketModel.get_open_by_user(call.from_user.id)
    if existing:
        await call.answer(f"❌ Уже есть тикет #{existing['ticket_id']}", show_alert=True)
        return
    
    ticket_id = TicketModel.create(call.from_user.id)
    
    await state.set_state(SupportStates.waiting_ticket_message)
    await state.update_data(ticket_id=ticket_id)
    
    await call.message.edit_text(
        f"✅ <b>Тикет #{ticket_id} создан!</b>\n\n"
        f"Опишите проблему в ответном сообщении.\n"
        f"Для отмены: /cancel_support",
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data="cancel_support"
        ).as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(SupportStates.waiting_ticket_message)
async def process_ticket_message(message: Message, state: FSMContext):
    """Обработка сообщения для тикета"""
    data = await state.get_data()
    ticket_id = data['ticket_id']
    
    TicketMessageModel.add(ticket_id, 'user', message.from_user.id, message.text or "[Медиа]")
    
    await state.clear()
    
    # Уведомляем админов
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"🔔 <b>Новое сообщение в тикете #{ticket_id}</b>\n"
                f"👤 @{message.from_user.username} (ID:{message.from_user.id})\n"
                f"📝 {message.text[:300]}",
                parse_mode="HTML"
            )
        except:
            pass
    
    await message.answer(
        f"✅ Сообщение добавлено в тикет #{ticket_id}\n"
        f"Ожидайте ответа оператора.",
        reply_markup=get_main_keyboard()
    )


@router.callback_query(F.data == "cancel_support")
async def cancel_support(call: CallbackQuery, state: FSMContext):
    """Отмена поддержки"""
    await state.clear()
    await call.message.edit_text("❌ Действие отменено", reply_markup=get_main_keyboard())
    await call.answer()


@router.callback_query(F.data == "ask_question")
async def ask_question(call: CallbackQuery, state: FSMContext):
    """Режим вопроса боту"""
    await state.set_state(SupportStates.waiting_question)
    
    await call.message.edit_text(
        "💬 <b>Задайте ваш вопрос</b>\n\n"
        "Отправьте сообщение, и я попробую ответить автоматически.\n\n"
        "Например:\n"
        "• Сколько стоит?\n"
        "• Как получить ключ?\n"
        "• Не работает оплата\n\n"
        "Для отмены: /cancel_support",
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data="cancel_support"
        ).as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(SupportStates.waiting_question)
async def process_question(message: Message, state: FSMContext):
    """Обработка вопроса через автоответчик"""
    await state.clear()
    
    # Показываем что бот думает
    thinking_msg = await message.answer("🤔 <i>Ищу ответ...</i>", parse_mode="HTML")
    
    # Получаем ответ
    answer = await AISupport.get_answer(message.text)
    
    # Удаляем "думает" и отправляем ответ
    await thinking_msg.delete()
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Создать тикет", callback_data="create_ticket")
    builder.button(text="💬 Ещё вопрос", callback_data="ask_question")
    builder.button(text="◀️ В меню", callback_data="main_menu")
    builder.adjust(1)
    
    await message.answer(answer, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(call: CallbackQuery):
    """Просмотр тикета"""
    ticket_id = int(call.data.split("_")[2])
    ticket = TicketModel.get(ticket_id)
    
    if not ticket:
        await call.answer("Тикет не найден")
        return
    
    messages = TicketMessageModel.get_by_ticket(ticket_id)
    
    text = f"📋 <b>Тикет #{ticket_id}</b>\n"
    text += f"Статус: {'🟢 Открыт' if ticket['status'] == 'open' else '🔴 Закрыт'}\n\n"
    
    for m in messages[-10:]:
        sender = "👤 Вы" if m['sender_type'] == 'user' else "👨‍💼 Поддержка"
        if m['sender_type'] == 'system':
            sender = "🤖 Система"
        text += f"<b>{sender}:</b>\n{m.get('message','')[:200]}\n\n"
    
    builder = InlineKeyboardBuilder()
    if ticket['status'] == 'open':
        builder.button(text="📝 Ответить", callback_data=f"add_message_{ticket_id}")
        builder.button(text="❌ Закрыть", callback_data=f"close_ticket_{ticket_id}")
    builder.button(text="◀️ Назад", callback_data="support")
    builder.adjust(2, 1)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("add_message_"))
async def add_message(call: CallbackQuery, state: FSMContext):
    """Добавить сообщение в тикет"""
    ticket_id = int(call.data.split("_")[2])
    
    await state.set_state(SupportStates.waiting_ticket_message)
    await state.update_data(ticket_id=ticket_id)
    
    await call.message.edit_text(
        f"📝 <b>Тикет #{ticket_id}</b>\n\n"
        "Отправьте сообщение — оно будет добавлено в тикет.\n"
        "Для отмены: /cancel_support",
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data="cancel_support"
        ).as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("close_ticket_"))
async def close_ticket(call: CallbackQuery):
    """Закрыть тикет"""
    ticket_id = int(call.data.split("_")[2])
    ticket = TicketModel.get(ticket_id)
    
    if not ticket or ticket['user_id'] != call.from_user.id:
        await call.answer("❌ Нет доступа")
        return
    
    TicketModel.close(ticket_id)
    TicketMessageModel.add(ticket_id, 'system', 0, "Тикет закрыт пользователем")
    
    await call.message.edit_text(
        f"✅ Тикет #{ticket_id} закрыт.\n\n"
        "Если остались вопросы — создайте новый /support",
        reply_markup=InlineKeyboardBuilder().button(
            text="📞 Новый тикет", callback_data="create_ticket"
        ).as_markup()
    )
    await call.answer("✅ Тикет закрыт")


# ============== ОСТАЛЬНЫЕ ФУНКЦИИ ==============
@router.callback_query(F.data == "my_key")
async def show_key(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    if not UserModel.is_ai_premium(call.from_user.id):
        await call.answer("❌ Сначала получите AI доступ", show_alert=True)
        return
    
    api_keys = json.loads(user.get('api_keys', '[]'))
    if not api_keys:
        api_keys = [f"sk-pro-{uuid.uuid4().hex[:24]}"]
        UserModel.update(call.from_user.id, {'api_keys': json.dumps(api_keys)})
    
    text = "🔑 <b>API-ключи:</b>\n\n"
    for key in api_keys:
        text += f"<code>{key}</code>\n"
    
    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardBuilder().button(
            text="◀️ Назад", callback_data="profile"
        ).as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "trial")
async def activate_trial(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    if user.get('trial_until'):
        trial_date = datetime.fromisoformat(user['trial_until'])
        if trial_date > datetime.now():
            days_left = (trial_date - datetime.now()).days
            await call.answer(f"❌ Триал уже активен! Осталось {days_left} дн.", show_alert=True)
            return
    
    UserModel.activate_trial(call.from_user.id)
    await call.answer("✅ Триал активирован на 3 дня!", show_alert=True)
    
    await call.message.edit_text(
        "✅ <b>Триал активирован!</b>\n\n📅 3 дня\n🔑 Используйте «Мой ключ»",
        reply_markup=InlineKeyboardBuilder().button(
            text="🔑 Ключ", callback_data="my_key"
        ).as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "referral_menu")
async def referral_menu(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    ref_stats = ReferralModel.get_stats(user['user_id'])
    bot_info = await call.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['referral_code']}"
    
    text = f"""
🎁 <b>Рефералы</b>

🔗 <code>{ref_link}</code>

📊 Приглашено: {ref_stats['total']}
💰 Оплатили: {ref_stats['paid']}
"""
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Поделиться", switch_inline_query=ref_link)
    builder.button(text="◀️ Назад", callback_data="profile")
    builder.adjust(1)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "rating")
async def show_rating(call: CallbackQuery):
    top_users = UserModel.get_top_users(10)
    
    text = "🏆 <b>Топ пользователей</b>\n\n"
    for i, u in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        username = f"@{u.get('username', 'ID:' + str(u['user_id']))}"
        text += f"{medal} {username} — {u.get('score', 0)} баллов\n"
    
    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardBuilder().button(
            text="◀️ Назад", callback_data="profile"
        ).as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "promo_code")
async def promo_code_menu(call: CallbackQuery):
    await call.message.edit_text(
        "🎫 <b>Промокоды</b>\n\n"
        "Отправьте код в чат:\n"
        "<code>WELCOME</code> — 20%\n"
        "<code>VIP50</code> — 50%\n"
        "<code>PREMIUM</code> — 30%",
        reply_markup=InlineKeyboardBuilder().button(
            text="◀️ Назад", callback_data="profile"
        ).as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


# ============== SIM ЗАКАЗЫ ==============
@router.callback_query(F.data == "sim_order")
async def start_sim_order(call: CallbackQuery):
    if not UserModel.is_sim_premium(call.from_user.id):
        await call.answer("❌ Сначала оплатите доступ к SIM.DL!", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for op in ["Билайн", "Мегафон", "МТС", "Tele2"]:
        builder.button(text=op, callback_data=f"simop_{op}")
    builder.button(text="◀️ Назад", callback_data="mode_sim")
    builder.adjust(2)
    
    await call.message.edit_text(
        "📱 <b>Выберите оператора:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("simop_"))
async def select_sim_operator(call: CallbackQuery):
    operator = call.data.split("_")[1]
    
    builder = InlineKeyboardBuilder()
    for reg in ["Москва", "СПб", "Казань", "Екатеринбург", "Новосибирск"]:
        builder.button(text=reg, callback_data=f"simreg_{operator}_{reg}")
    builder.button(text="◀️ Назад", callback_data="sim_order")
    builder.adjust(2)
    
    await call.message.edit_text(
        f"📱 Оператор: <b>{operator}</b>\n\n📍 <b>Выберите регион:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("simreg_"))
async def select_sim_region(call: CallbackQuery):
    parts = call.data.split("_")
    operator = parts[1]
    region = parts[2]
    
    builder = InlineKeyboardBuilder()
    for tar in ["Доверенное лицо", "Корпоративный", "Самозанятый"]:
        builder.button(text=tar, callback_data=f"simtar_{operator}_{region}_{tar}")
    builder.button(text="◀️ Назад", callback_data=f"simop_{operator}")
    builder.adjust(1)
    
    await call.message.edit_text(
        f"📱 {operator} | 📍 {region}\n\n📋 <b>Выберите тариф:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("simtar_"))
async def confirm_sim_order(call: CallbackQuery):
    parts = call.data.split("_")
    operator = parts[1]
    region = parts[2]
    tariff = parts[3]
    
    order_id = SimModel.create_order(call.from_user.id, operator, region, tariff)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Мои заказы", callback_data="sim_orders")
    builder.button(text="◀️ В меню", callback_data="mode_sim")
    builder.adjust(1)
    
    await call.message.edit_text(
        f"✅ <b>Заказ #{order_id} создан!</b>\n\n"
        f"📱 {operator}\n📍 {region}\n📋 {tariff}\n\n"
        f"⏳ Ожидает обработки",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "sim_orders")
async def show_sim_orders(call: CallbackQuery):
    orders = SimModel.get_user_orders(call.from_user.id)
    
    if not orders:
        text = "📱 У вас пока нет заказов."
    else:
        text = "📱 <b>Ваши заказы:</b>\n\n"
        for o in orders[:10]:
            status = "✅" if o['status'] == 'completed' else "⏳"
            sim = f" — {o.get('sim_number', '')}" if o.get('sim_number') else ""
            text += f"{status} #{o['order_id']}: {o['operator']} | {o['region']}{sim}\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Новый заказ", callback_data="sim_order")
    builder.button(text="◀️ Назад", callback_data="mode_sim")
    builder.adjust(1)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


# ============== ПРОМОКОДЫ ==============
@router.message(lambda m: m.text and m.text.upper() in ["WELCOME", "VIP50", "PREMIUM"])
async def process_promo_code(message: Message):
    code = message.text.upper()
    user_id = message.from_user.id
    
    if UserModel.is_ai_premium(user_id):
        await message.answer("❌ У вас уже есть Premium!")
        return
    
    if PromoModel.is_used(user_id, code):
        await message.answer("❌ Вы уже использовали этот промокод!")
        return
    
    promo = PromoModel.check(code)
    if not promo:
        await message.answer("❌ Промокод не найден!")
        return
    
    discount_amount = int(AI_PAYMENT_AMOUNT * promo['discount'] / 100)
    final_price = AI_PAYMENT_AMOUNT - discount_amount
    
    PromoModel.use(user_id, code, promo['discount'])
    
    await message.answer(
        f"✅ <b>Промокод {code} активирован!</b>\n\n"
        f"Скидка: {promo['discount']}%\n"
        f"Цена: <b>{final_price} ₽</b>\n\n"
        f"Используйте кнопку «Получить доступ» для оплаты.",
        parse_mode="HTML"
    )


# ============== КОМАНДЫ ==============
@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = UserModel.get(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return
    
    await message.answer(
        f"👤 ID: {user['user_id']}\n🤖 AI: {'✅' if UserModel.is_ai_premium(message.from_user.id) else '❌'}\n📱 SIM: {'✅' if UserModel.is_sim_premium(message.from_user.id) else '❌'}",
        parse_mode="HTML"
    )


@router.message(Command("key"))
async def cmd_key(message: Message):
    user = UserModel.get(message.from_user.id)
    if not UserModel.is_ai_premium(message.from_user.id):
        await message.answer("❌ Сначала получите доступ /start")
        return
    
    api_keys = json.loads(user.get('api_keys', '[]'))
    if not api_keys:
        api_keys = [f"sk-pro-{uuid.uuid4().hex[:24]}"]
        UserModel.update(message.from_user.id, {'api_keys': json.dumps(api_keys)})
    
    text = "🔑 <b>API-ключи:</b>\n\n"
    for key in api_keys:
        text += f"<code>{key}</code>\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("trial"))
async def cmd_trial(message: Message):
    user = UserModel.get(message.from_user.id)
    if user.get('trial_until'):
        trial_date = datetime.fromisoformat(user['trial_until'])
        if trial_date > datetime.now():
            days_left = (trial_date - datetime.now()).days
            await message.answer(f"❌ Триал уже активен! Осталось {days_left} дн.")
            return
    
    UserModel.activate_trial(message.from_user.id)
    await message.answer("✅ Триал активирован на 3 дня! /key")


@router.message(Command("support"))
async def cmd_support(message: Message):
    existing = TicketModel.get_open_by_user(message.from_user.id)
    
    if existing:
        await message.answer(f"📞 У вас уже есть тикет #{existing['ticket_id']}")
    else:
        ticket_id = TicketModel.create(message.from_user.id)
        await message.answer(
            f"✅ Тикет #{ticket_id} создан!\nОпишите проблему в ответном сообщении."
        )


@router.message(Command("cancel_support"))
async def cmd_cancel_support(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено", reply_markup=get_main_keyboard())


@router.message()
async def echo_text(message: Message):
    """Обработка обычных сообщений"""
    # Проверяем, не ответ ли в тикет
    user = UserModel.get(message.from_user.id)
    if user:
        existing = TicketModel.get_open_by_user(message.from_user.id)
        if existing:
            TicketMessageModel.add(existing['ticket_id'], 'user', message.from_user.id, message.text or "[Медиа]")
            
            for admin_id in ADMIN_IDS:
                try:
                    await message.bot.send_message(
                        admin_id,
                        f"🔔 Новое сообщение в тикете #{existing['ticket_id']}\n"
                        f"👤 @{message.from_user.username}\n"
                        f"📝 {message.text[:300]}",
                        parse_mode="HTML"
                    )
                except:
                    pass
            
            await message.answer(f"✅ Добавлено в тикет #{existing['ticket_id']}")
            return
    
    await message.answer("Используйте меню или /start")