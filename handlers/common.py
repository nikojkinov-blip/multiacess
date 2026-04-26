import json
import uuid
from datetime import datetime, timedelta
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import (
    UserModel, ReferralModel, TicketModel, TicketMessageModel,
    PromoModel, SimModel
)
from config import (
    ADMIN_IDS, ACHIEVEMENTS, AI_PAYMENT_AMOUNT
)
from keyboards.inline import get_main_keyboard, get_sim_keyboard
from services.ai_support import AISupport

router = Router()


class SupportStates(StatesGroup):
    waiting_question = State()
    waiting_ticket_message = State()


async def show_mode_selection(message: Message):
    """Показать выбор режима"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🤖 AI Access", callback_data="mode_ai")
    builder.button(text="📱 SIM.DL", callback_data="mode_sim")
    builder.button(text="💰 CASH.DL", callback_data="mode_cash")
    builder.button(text="🧪 WHITE MYSTIC LAB", callback_data="mode_shop")
    builder.button(text="📝 ВАКАНСИИ", callback_data="mode_jobs")
    builder.button(text="📞 Поддержка", callback_data="support")
    builder.adjust(2, 2, 1, 1)
    
    await message.answer(
        "🚀 <b>MULTIACCES — ВСЁ В ОДНОМ БОТЕ</b>\n\n"
        "🤖 <b>AI Access</b> — ChatGPT, Claude, Midjourney\n"
        "📱 <b>SIM.DL</b> — Активация сим-карт\n"
        "💰 <b>CASH.DL</b> — Обнал и сплиты\n"
        "🧪 <b>WHITE MYSTIC LAB</b> — Магазин\n"
        "📝 <b>ВАКАНСИИ</b> — Работа в лаборатории\n\n"
        "Выберите раздел:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


# ==================== СТАРТ ====================
@router.message(CommandStart(deep_link=True))
async def start_deep_link(message: Message, command: CommandObject):
    user_id = message.from_user.id
    user = UserModel.get(user_id)
    
    if not user:
        UserModel.create(user_id, message.from_user.username or '',
                        message.from_user.first_name or '',
                        message.from_user.last_name or '')
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
    if not UserModel.get(user_id):
        UserModel.create(user_id, message.from_user.username or '',
                        message.from_user.first_name or '',
                        message.from_user.last_name or '')
    await show_mode_selection(message)


# ==================== РЕЖИМЫ ====================
@router.callback_query(F.data == "mode_ai")
async def show_ai_menu(call: CallbackQuery):
    await call.message.edit_text(
        "🤖 <b>AI Access</b>\n\nДоступ к ChatGPT-4o, Claude 3.5, Midjourney\n"
        f"💰 {AI_PAYMENT_AMOUNT}₽ | 🆓 Триал 3 дня",
        reply_markup=get_main_keyboard(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "mode_sim")
async def show_sim_menu(call: CallbackQuery):
    await call.message.edit_text(
        "📱 <b>SIM.DL</b>\n\nАктивация сим-карт через доверенное лицо\n💰 299₽",
        reply_markup=get_sim_keyboard(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "main_menu")
async def back_to_main(call: CallbackQuery):
    await show_mode_selection(call.message)
    await call.answer()


# ==================== ПРОФИЛЬ ====================
@router.callback_query(F.data == "profile")
async def show_profile(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    if not user: return
    
    ref_stats = ReferralModel.get_stats(user['user_id'])
    ai = "💎 Premium" if UserModel.is_ai_premium(call.from_user.id) else ("🆓 Триал" if user.get('trial_until') else "❌ Нет")
    sim = "✅ Premium" if UserModel.is_sim_premium(call.from_user.id) else "❌ Нет"
    
    text = f"""👤 <b>Профиль</b>
🆔 <code>{user['user_id']}</code>
📛 {user.get('first_name','—')}
🤖 AI: {ai}
📱 SIM: {sim}
👥 Рефералов: {ref_stats['total']}
📊 Запросов: {user.get('total_requests',0)}"""
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 AI ключ", callback_data="my_key")
    builder.button(text="📱 SIM заказы", callback_data="sim_orders")
    builder.button(text="👥 Рефералы", callback_data="referral_menu")
    builder.button(text="🏆 Рейтинг", callback_data="rating")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(2, 2, 1)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


# ==================== ПОДДЕРЖКА ====================
@router.callback_query(F.data == "support")
async def support_menu(call: CallbackQuery):
    existing = TicketModel.get_open_by_user(call.from_user.id)
    if existing:
        builder = InlineKeyboardBuilder()
        builder.button(text="📋 Мой тикет", callback_data=f"view_ticket_{existing['ticket_id']}")
        builder.button(text="💬 Автоответчик", callback_data="ask_question")
        builder.button(text="❌ Закрыть", callback_data=f"close_ticket_{existing['ticket_id']}")
        builder.button(text="◀️ Назад", callback_data="main_menu")
        builder.adjust(1)
        await call.message.edit_text(f"📞 Открытый тикет #{existing['ticket_id']}", reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Создать тикет", callback_data="create_ticket")
        builder.button(text="💬 Задать вопрос боту", callback_data="ask_question")
        builder.button(text="◀️ Назад", callback_data="main_menu")
        builder.adjust(1)
        await call.message.edit_text("📞 <b>Поддержка</b>\n\n💬 Автоответчик\n📝 Тикет — связь с оператором",
                                     reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "create_ticket")
async def create_ticket(call: CallbackQuery, state: FSMContext):
    existing = TicketModel.get_open_by_user(call.from_user.id)
    if existing:
        await call.answer(f"❌ Уже есть тикет #{existing['ticket_id']}", show_alert=True)
        return
    ticket_id = TicketModel.create(call.from_user.id)
    await state.set_state(SupportStates.waiting_ticket_message)
    await state.update_data(ticket_id=ticket_id)
    await call.message.edit_text(f"✅ Тикет #{ticket_id} создан!\nОпишите проблему в ответном сообщении.\n/cancel_support — отмена",
                                 reply_markup=InlineKeyboardBuilder().button(text="❌ Отмена", callback_data="cancel_support").as_markup())
    await call.answer()


@router.message(SupportStates.waiting_ticket_message)
async def process_ticket_message(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_id = data['ticket_id']
    TicketMessageModel.add(ticket_id, 'user', message.from_user.id, message.text or "[Медиа]")
    await state.clear()
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id,
                f"🔔 Новое сообщение в тикете #{ticket_id}\n👤 @{message.from_user.username}\n📝 {message.text[:300]}",
                parse_mode="HTML")
        except: pass
    await message.answer(f"✅ Добавлено в тикет #{ticket_id}", reply_markup=get_main_keyboard())


@router.callback_query(F.data == "ask_question")
async def ask_question(call: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_question)
    await call.message.edit_text("💬 Задайте вопрос:\n\nПримеры: цена, триал, ключ, SIM\n/cancel_support — отмена",
                                 reply_markup=InlineKeyboardBuilder().button(text="❌ Отмена", callback_data="cancel_support").as_markup())
    await call.answer()


@router.message(SupportStates.waiting_question)
async def process_question(message: Message, state: FSMContext):
    await state.clear()
    thinking = await message.answer("🤔 Ищу ответ...")
    answer = await AISupport.get_answer(message.text)
    await thinking.delete()
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Создать тикет", callback_data="create_ticket")
    builder.button(text="💬 Ещё вопрос", callback_data="ask_question")
    builder.button(text="◀️ В меню", callback_data="main_menu")
    builder.adjust(1)
    await message.answer(answer, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "cancel_support")
async def cancel_support(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Отменено")
    await call.answer()


# ==================== ТИКЕТЫ (просмотр/закрытие) ====================
@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(call: CallbackQuery):
    ticket_id = int(call.data.split("_")[2])
    ticket = TicketModel.get(ticket_id)
    if not ticket: return
    messages = TicketMessageModel.get_by_ticket(ticket_id)
    text = f"📋 Тикет #{ticket_id} | {'🟢 Открыт' if ticket['status']=='open' else '🔴 Закрыт'}\n\n"
    for m in messages[-10:]:
        sender = "👤 Вы" if m['sender_type']=='user' else "👨‍💼 Поддержка"
        text += f"<b>{sender}:</b>\n{m.get('message','')[:200]}\n\n"
    builder = InlineKeyboardBuilder()
    if ticket['status'] == 'open':
        builder.button(text="📝 Ответить", callback_data=f"add_message_{ticket_id}")
        builder.button(text="❌ Закрыть", callback_data=f"close_ticket_{ticket_id}")
    builder.button(text="◀️ Назад", callback_data="support")
    builder.adjust(2, 1)
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("close_ticket_"))
async def close_ticket(call: CallbackQuery):
    ticket_id = int(call.data.split("_")[2])
    ticket = TicketModel.get(ticket_id)
    if not ticket or ticket['user_id'] != call.from_user.id:
        await call.answer("❌ Нет доступа"); return
    TicketModel.close(ticket_id)
    TicketMessageModel.add(ticket_id, 'system', 0, "Тикет закрыт пользователем")
    await call.message.edit_text(f"✅ Тикет #{ticket_id} закрыт\n/support — новый")
    await call.answer("✅ Закрыт")


@router.callback_query(F.data.startswith("add_message_"))
async def add_message(call: CallbackQuery, state: FSMContext):
    ticket_id = int(call.data.split("_")[2])
    await state.set_state(SupportStates.waiting_ticket_message)
    await state.update_data(ticket_id=ticket_id)
    await call.message.edit_text(f"📝 Тикет #{ticket_id}\nОтправьте сообщение.\n/cancel_support — отмена")
    await call.answer()


# ==================== КЛЮЧИ / ТРИАЛ / РЕФЕРАЛЫ ====================
@router.callback_query(F.data == "my_key")
async def show_key(call: CallbackQuery):
    if not UserModel.is_ai_premium(call.from_user.id):
        await call.answer("❌ Нет AI доступа", show_alert=True); return
    user = UserModel.get(call.from_user.id)
    keys = json.loads(user.get('api_keys', '[]'))
    if not keys:
        keys = [f"sk-pro-{uuid.uuid4().hex[:24]}"]
        UserModel.update(call.from_user.id, {'api_keys': json.dumps(keys)})
    text = "🔑 <b>Ключи:</b>\n\n" + "\n".join([f"<code>{k}</code>" for k in keys])
    await call.message.edit_text(text, reply_markup=InlineKeyboardBuilder().button(text="◀️ Назад", callback_data="profile").as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "trial")
async def activate_trial(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    if user.get('trial_until') and datetime.fromisoformat(user['trial_until']) > datetime.now():
        days = (datetime.fromisoformat(user['trial_until'])-datetime.now()).days
        await call.answer(f"❌ Триал активен! {days} дн.", show_alert=True); return
    UserModel.activate_trial(call.from_user.id)
    await call.answer("✅ Триал на 3 дня!", show_alert=True)
    await call.message.edit_text("✅ Триал активирован!\n📅 3 дня\n🔑 /key")


@router.callback_query(F.data == "referral_menu")
async def referral_menu(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    ref_stats = ReferralModel.get_stats(user['user_id'])
    bot_info = await call.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['referral_code']}"
    text = f"🎁 <b>Рефералы</b>\n🔗 <code>{ref_link}</code>\n📊 Приглашено: {ref_stats['total']}\n💰 Оплатили: {ref_stats['paid']}"
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Поделиться", switch_inline_query=ref_link)
    builder.button(text="◀️ Назад", callback_data="profile")
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "rating")
async def show_rating(call: CallbackQuery):
    top = UserModel.get_top_users(10)
    text = "🏆 <b>Топ</b>\n\n"
    for i, u in enumerate(top, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        text += f"{medal} @{u.get('username','ID:'+str(u['user_id']))} — {u['score']} баллов\n"
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="profile")
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


# ==================== SIM ЗАКАЗЫ ====================
@router.callback_query(F.data == "sim_order")
async def start_sim_order(call: CallbackQuery):
    if not UserModel.is_sim_premium(call.from_user.id):
        await call.answer("❌ Нет SIM доступа", show_alert=True); return
    builder = InlineKeyboardBuilder()
    for op in ["Билайн", "Мегафон", "МТС", "Tele2"]:
        builder.button(text=op, callback_data=f"simop_{op}")
    builder.button(text="◀️ Назад", callback_data="mode_sim")
    builder.adjust(2)
    await call.message.edit_text("📱 Выберите оператора:", reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("simop_"))
async def select_operator(call: CallbackQuery):
    op = call.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    for reg in ["Москва","СПб","Казань","Екатеринбург","Новосибирск"]:
        builder.button(text=reg, callback_data=f"simreg_{op}_{reg}")
    builder.button(text="◀️ Назад", callback_data="sim_order")
    builder.adjust(2)
    await call.message.edit_text(f"📱 {op}\n📍 Выберите регион:", reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("simreg_"))
async def select_region(call: CallbackQuery):
    parts = call.data.split("_")
    op, reg = parts[1], parts[2]
    builder = InlineKeyboardBuilder()
    for tar in ["Доверенное лицо","Корпоративный","Самозанятый"]:
        builder.button(text=tar, callback_data=f"simtar_{op}_{reg}_{tar}")
    builder.button(text="◀️ Назад", callback_data=f"simop_{op}")
    builder.adjust(1)
    await call.message.edit_text(f"📱 {op} | 📍 {reg}\n📋 Выберите тариф:", reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("simtar_"))
async def confirm_sim(call: CallbackQuery):
    parts = call.data.split("_")
    op, reg, tar = parts[1], parts[2], parts[3]
    order_id = SimModel.create_order(call.from_user.id, op, reg, tar)
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Мои заказы", callback_data="sim_orders")
    builder.button(text="◀️ В меню", callback_data="mode_sim")
    await call.message.edit_text(f"✅ Заказ #{order_id} создан!\n📱 {op}\n📍 {reg}\n📋 {tar}\n⏳ Ожидает",
                                 reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data == "sim_orders")
async def show_sim_orders(call: CallbackQuery):
    orders = SimModel.get_user_orders(call.from_user.id)
    text = "📱 <b>Заказы:</b>\n\n" if orders else "📱 Нет заказов"
    for o in orders[:10]:
        s = "✅" if o['status']=='completed' else "⏳"
        text += f"{s} #{o['order_id']}: {o['operator']} | {o['region']}\n"
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Новый", callback_data="sim_order")
    builder.button(text="◀️ Назад", callback_data="mode_sim")
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


# ==================== ПРОМОКОДЫ ====================
@router.message(lambda m: m.text and m.text.upper() in ["WELCOME","VIP50","PREMIUM"])
async def process_promo(message: Message):
    code = message.text.upper()
    if UserModel.is_ai_premium(message.from_user.id):
        await message.answer("❌ Уже есть Premium!"); return
    if PromoModel.is_used(message.from_user.id, code):
        await message.answer("❌ Уже использован!"); return
    promo = PromoModel.check(code)
    if not promo:
        await message.answer("❌ Не найден!"); return
    discount = int(AI_PAYMENT_AMOUNT * promo['discount'] / 100)
    final = AI_PAYMENT_AMOUNT - discount
    PromoModel.use(message.from_user.id, code, promo['discount'])
    await message.answer(f"✅ {code}!\nСкидка {promo['discount']}%\nЦена: <b>{final}₽</b>", parse_mode="HTML")


# ==================== КОМАНДЫ ====================
@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = UserModel.get(message.from_user.id)
    if not user: return
    await message.answer(f"👤 ID: {user['user_id']}\n🤖 AI: {'✅' if UserModel.is_ai_premium(message.from_user.id) else '❌'}")


@router.message(Command("key"))
async def cmd_key(message: Message):
    if not UserModel.is_ai_premium(message.from_user.id):
        await message.answer("❌ Нет доступа"); return
    user = UserModel.get(message.from_user.id)
    keys = json.loads(user.get('api_keys','[]'))
    if not keys:
        keys = [f"sk-pro-{uuid.uuid4().hex[:24]}"]
        UserModel.update(message.from_user.id, {'api_keys': json.dumps(keys)})
    await message.answer("🔑\n" + "\n".join([f"<code>{k}</code>" for k in keys]), parse_mode="HTML")


@router.message(Command("trial"))
async def cmd_trial(message: Message):
    user = UserModel.get(message.from_user.id)
    if user.get('trial_until') and datetime.fromisoformat(user['trial_until']) > datetime.now():
        days = (datetime.fromisoformat(user['trial_until'])-datetime.now()).days
        await message.answer(f"❌ Триал активен! {days} дн."); return
    UserModel.activate_trial(message.from_user.id)
    await message.answer("✅ Триал на 3 дня! /key")


@router.message(Command("support"))
async def cmd_support(message: Message):
    existing = TicketModel.get_open_by_user(message.from_user.id)
    if existing:
        await message.answer(f"📞 Тикет #{existing['ticket_id']} уже открыт")
    else:
        ticket_id = TicketModel.create(message.from_user.id)
        await message.answer(f"✅ Тикет #{ticket_id} создан!\nОпишите проблему.")


@router.message(Command("cancel_support"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено")


@router.message()
async def echo(message: Message):
    # Проверка на сообщение в тикет
    existing = TicketModel.get_open_by_user(message.from_user.id)
    if existing:
        TicketMessageModel.add(existing['ticket_id'], 'user', message.from_user.id, message.text or "[Медиа]")
        for admin_id in ADMIN_IDS:
            try: await message.bot.send_message(admin_id, f"🔔 Тикет #{existing['ticket_id']}\n👤 @{message.from_user.username}\n📝 {message.text[:300]}", parse_mode="HTML")
            except: pass
        await message.answer(f"✅ Добавлено в тикет #{existing['ticket_id']}")
        return
    
    await message.answer("Используйте меню или /start")
