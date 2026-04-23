from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import TicketModel, TicketMessageModel, UserModel, db
from config import ADMIN_IDS
from keyboards.inline import get_main_keyboard

router = Router()

class SupportStates(StatesGroup):
    waiting_message = State()
    waiting_reply = State()

@router.message(Command("support"))
async def cmd_support(message: Message, state: FSMContext):
    user = UserModel.get(message.from_user.id)
    if not user:
        await message.answer("Сначала используйте /start")
        return
    
    existing = TicketModel.get_open_by_user(message.from_user.id)
    if existing:
        builder = InlineKeyboardBuilder()
        builder.button(text="📋 Просмотреть тикет", callback_data=f"view_ticket_{existing['ticket_id']}")
        builder.button(text="❌ Закрыть тикет", callback_data=f"close_ticket_{existing['ticket_id']}")
        builder.button(text="◀️ Назад", callback_data="main_menu")
        builder.adjust(1)
        
        await message.answer(
            f"У вас уже есть открытый тикет #{existing['ticket_id']}.\n"
            "Выберите действие:",
            reply_markup=builder.as_markup()
        )
        return
    
    ticket_id = TicketModel.create(message.from_user.id)
    
    await state.set_state(SupportStates.waiting_message)
    await state.update_data(ticket_id=ticket_id)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отменить", callback_data="cancel_support")
    
    await message.answer(
        f"📞 <b>Техподдержка AI Access Bot</b>\n\n"
        f"🆔 Номер тикета: <code>#{ticket_id}</code>\n\n"
        f"Опишите вашу проблему или вопрос.\n"
        f"Оператор ответит в течение 24 часов.\n\n"
        f"Для отмены нажмите кнопку ниже или /cancel_support",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.message(Command("cancel_support"))
@router.callback_query(F.data == "cancel_support")
async def cancel_support(event: Message | CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        if isinstance(event, CallbackQuery):
            await event.message.edit_text("Нет активных действий.", reply_markup=get_main_keyboard())
            await event.answer()
        else:
            await event.answer("Нет активных действий.", reply_markup=get_main_keyboard())
        return
    
    await state.clear()
    
    text = "❌ Действие отменено."
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_main_keyboard())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_main_keyboard())

@router.message(SupportStates.waiting_message)
async def process_support_message(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_id = data['ticket_id']
    
    TicketMessageModel.add(
        ticket_id=ticket_id,
        sender_type='user',
        sender_id=message.from_user.id,
        message=message.text or "[Медиа]"
    )
    
    await state.clear()
    
    for admin_id in ADMIN_IDS:
        try:
            builder = InlineKeyboardBuilder()
            builder.button(text="✉️ Ответить", callback_data=f"reply_ticket_{ticket_id}")
            builder.button(text="👁️ Просмотр", callback_data=f"view_ticket_{ticket_id}")
            builder.button(text="❌ Закрыть", callback_data=f"close_ticket_{ticket_id}")
            builder.adjust(2, 1)
            
            user = UserModel.get(message.from_user.id)
            await message.bot.send_message(
                admin_id,
                f"🔔 <b>Новый тикет #{ticket_id}</b>\n\n"
                f"👤 От: @{user.get('username', 'No username')} (ID: {message.from_user.id})\n"
                f"📝 Сообщение:\n{message.text[:500]}",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        except:
            pass
    
    await message.answer(
        f"✅ Ваше сообщение отправлено в тикет #{ticket_id}.\n"
        f"Ожидайте ответа оператора.",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(call: CallbackQuery):
    ticket_id = int(call.data.split("_")[2])
    ticket = TicketModel.get(ticket_id)
    
    if not ticket:
        await call.answer("Тикет не найден")
        return
    
    messages = TicketMessageModel.get_by_ticket(ticket_id)
    user = UserModel.get(ticket['user_id'])
    
    text = f"📋 <b>Тикет #{ticket_id}</b>\n"
    text += f"👤 Пользователь: @{user.get('username', 'No username')} (ID: {ticket['user_id']})\n"
    text += f"📊 Статус: {ticket['status']}\n"
    text += f"📅 Создан: {ticket['created_at'][:16]}\n\n"
    text += "<b>Переписка:</b>\n\n"
    
    for msg in messages[-10:]:
        sender = "👤 Пользователь" if msg['sender_type'] == 'user' else "👨‍💼 Поддержка"
        text += f"{sender}:\n{msg['message'][:200]}\n"
        text += f"<i>{msg['timestamp'][:16]}</i>\n\n"
    
    if call.from_user.id in ADMIN_IDS:
        builder = InlineKeyboardBuilder()
        builder.button(text="✉️ Ответить", callback_data=f"reply_ticket_{ticket_id}")
        builder.button(text="❌ Закрыть", callback_data=f"close_ticket_{ticket_id}")
        builder.button(text="🔄 Обновить", callback_data=f"view_ticket_{ticket_id}")
        builder.adjust(2, 1)
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ Добавить сообщение", callback_data=f"add_message_{ticket_id}")
        if ticket['status'] == 'open':
            builder.button(text="❌ Закрыть тикет", callback_data=f"close_ticket_{ticket_id}")
        builder.button(text="◀️ Назад", callback_data="main_menu")
        builder.adjust(1)
    
    await call.message.edit_text(
        text[:4000],
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("reply_ticket_"))
async def reply_ticket_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Нет доступа")
        return
    
    ticket_id = int(call.data.split("_")[2])
    
    await state.set_state(SupportStates.waiting_reply)
    await state.update_data(ticket_id=ticket_id, admin_id=call.from_user.id)
    
    await call.message.edit_text(
        f"✉️ Введите ответ для тикета #{ticket_id}:",
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data=f"view_ticket_{ticket_id}"
        ).as_markup()
    )
    await call.answer()

@router.message(SupportStates.waiting_reply)
async def process_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_id = data['ticket_id']
    admin_id = data['admin_id']
    
    TicketMessageModel.add(
        ticket_id=ticket_id,
        sender_type='admin',
        sender_id=admin_id,
        message=message.text
    )
    
    ticket = TicketModel.get(ticket_id)
    if ticket:
        TicketModel.assign(ticket_id, admin_id)
        
        try:
            builder = InlineKeyboardBuilder()
            builder.button(text="📋 Просмотреть", callback_data=f"view_ticket_{ticket_id}")
            builder.button(text="➕ Добавить", callback_data=f"add_message_{ticket_id}")
            
            await message.bot.send_message(
                ticket['user_id'],
                f"📞 <b>Ответ от поддержки в тикете #{ticket_id}:</b>\n\n"
                f"{message.text}\n\n"
                f"Для ответа нажмите кнопку ниже.",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        except:
            pass
    
    await state.clear()
    await message.answer(f"✅ Ответ отправлен в тикет #{ticket_id}")

@router.callback_query(F.data.startswith("add_message_"))
async def add_message_start(call: CallbackQuery, state: FSMContext):
    ticket_id = int(call.data.split("_")[2])
    ticket = TicketModel.get(ticket_id)
    
    if not ticket or ticket['user_id'] != call.from_user.id:
        await call.answer("❌ Нет доступа")
        return
    
    if ticket['status'] != 'open':
        await call.answer("❌ Тикет закрыт")
        return
    
    await state.set_state(SupportStates.waiting_message)
    await state.update_data(ticket_id=ticket_id)
    
    await call.message.edit_text(
        f"📝 Введите дополнительное сообщение для тикета #{ticket_id}:",
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data=f"view_ticket_{ticket_id}"
        ).as_markup()
    )
    await call.answer()

@router.callback_query(F.data.startswith("close_ticket_"))
async def close_ticket(call: CallbackQuery):
    ticket_id = int(call.data.split("_")[2])
    ticket = TicketModel.get(ticket_id)
    
    if not ticket:
        await call.answer("Тикет не найден")
        return
    
    if call.from_user.id not in ADMIN_IDS and ticket['user_id'] != call.from_user.id:
        await call.answer("❌ Нет доступа")
        return
    
    TicketModel.close(ticket_id)
    TicketMessageModel.add(
        ticket_id=ticket_id,
        sender_type='system',
        sender_id=call.from_user.id,
        message="Тикет закрыт"
    )
    
    try:
        await call.bot.send_message(
            ticket['user_id'],
            f"📞 Тикет #{ticket_id} закрыт.\n"
            f"Если у вас остались вопросы, создайте новый тикет /support"
        )
    except:
        pass
    
    await call.message.edit_text(
        f"✅ Тикет #{ticket_id} закрыт",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

@router.message(Command("opentickets"))
async def cmd_open_tickets(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Нет доступа")
        return
    
    tickets = TicketModel.get_all_open()
    
    if not tickets:
        await message.answer("📭 Нет открытых тикетов")
        return
    
    builder = InlineKeyboardBuilder()
    for ticket in tickets[:20]:
        user = UserModel.get(ticket['user_id'])
        username = user.get('username', 'No username') if user else 'Unknown'
        builder.button(
            text=f"#{ticket['ticket_id']} - @{username}",
            callback_data=f"view_ticket_{ticket['ticket_id']}"
        )
    builder.adjust(1)
    
    await message.answer(
        f"📋 <b>Открытые тикеты ({len(tickets)})</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )