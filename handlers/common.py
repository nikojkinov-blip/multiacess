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
    builder = InlineKeyboardBuilder()
    builder.button(text="🤖 AI Access", callback_data="mode_ai")
    builder.button(text="📱 SIM.DL", callback_data="mode_sim")
    builder.button(text="💰 CASH.DL", callback_data="mode_cash")
    builder.button(text="🧪 WHITE MYSTIC LAB", callback_data="mode_shop")
    builder.button(text="📝 ВАКАНСИИ", callback_data="mode_jobs")
    builder.button(text="📞 Поддержка", callback_data="support")
    builder.adjust(2, 2, 1, 1)
    
    await message.answer(
        "🚀 <b>MULTIACCES</b>\n\n"
        "🤖 AI Access | 📱 SIM.DL | 💰 CASH.DL\n"
        "🧪 WHITE MYSTIC LAB | 📝 ВАКАНСИИ\n\n"
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
async def show_ai(call: CallbackQuery):
    await call.message.edit_text("🤖 AI Access", reply_markup=get_main_keyboard(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "mode_sim")
async def show_sim(call: CallbackQuery):
    await call.message.edit_text("📱 SIM.DL", reply_markup=get_sim_keyboard(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "main_menu")
async def back_main(call: CallbackQuery):
    await show_mode_selection(call.message)
    await call.answer()


# ==================== ПРОФИЛЬ ====================
@router.callback_query(F.data == "profile")
async def show_profile(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    if not user: return
    ref_stats = ReferralModel.get_stats(user['user_id'])
    ai = "💎" if UserModel.is_ai_premium(call.from_user.id) else ("🆓" if user.get('trial_until') else "❌")
    sim = "✅" if UserModel.is_sim_premium(call.from_user.id) else "❌"
    text = f"👤 Профиль\n🆔 {user['user_id']}\n🤖 AI: {ai}\n📱 SIM: {sim}\n👥 Рефералов: {ref_stats['total']}"
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 AI ключ", callback_data="my_key")
    builder.button(text="👥 Рефералы", callback_data="referral_menu")
    builder.button(text="🏆 Рейтинг", callback_data="rating")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(2,1,1)
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


# ==================== ПОДДЕРЖКА ====================
@router.callback_query(F.data == "support")
async def support_menu(call: CallbackQuery):
    existing = TicketModel.get_open_by_user(call.from_user.id)
    if existing:
        builder = InlineKeyboardBuilder()
        builder.button(text="📋 Тикет", callback_data=f"view_ticket_{existing['ticket_id']}")
        builder.button(text="💬 Автоответчик", callback_data="ask_question")
        builder.button(text="❌ Закрыть", callback_data=f"close_ticket_{existing['ticket_id']}")
        builder.button(text="◀️ Назад", callback_data="main_menu")
        builder.adjust(1)
        await call.message.edit_text(f"📞 Тикет #{existing['ticket_id']}", reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Создать тикет", callback_data="create_ticket")
        builder.button(text="💬 Задать вопрос", callback_data="ask_question")
        builder.button(text="◀️ Назад", callback_data="main_menu")
        builder.adjust(1)
        await call.message.edit_text("📞 Поддержка", reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "create_ticket")
async def create_ticket(call: CallbackQuery, state: FSMContext):
    existing = TicketModel.get_open_by_user(call.from_user.id)
    if existing:
        await call.answer(f"Уже есть #{existing['ticket_id']}", show_alert=True)
        return
    ticket_id = TicketModel.create(call.from_user.id)
    await state.set_state(SupportStates.waiting_ticket_message)
    await state.update_data(ticket_id=ticket_id)
    await call.message.edit_text(f"✅ Тикет #{ticket_id}\nОпишите проблему.\n/cancel_support",
                                 reply_markup=InlineKeyboardBuilder().button(text="❌ Отмена", callback_data="cancel_support").as_markup())
    await call.answer()


@router.message(SupportStates.waiting_ticket_message)
async def process_ticket_msg(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_id = data['ticket_id']
    TicketMessageModel.add(ticket_id, 'user', message.from_user.id, message.text or "[Медиа]")
    await state.clear()
    for admin_id in ADMIN_IDS:
        try: await message.bot.send_message(admin_id, f"🔔 Тикет #{ticket_id}\n👤 @{message.from_user.username}\n📝 {message.text[:300]}", parse_mode="HTML")
        except: pass
    await message.answer(f"✅ Добавлено в #{ticket_id}")


@router.callback_query(F.data == "ask_question")
async def ask_question(call: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_question)
    await call.message.edit_text("💬 Задайте вопрос:\n/cancel_support",
                                 reply_markup=InlineKeyboardBuilder().button(text="❌ Отмена", callback_data="cancel_support").as_markup())
    await call.answer()


@router.message(SupportStates.waiting_question)
async def process_question(message: Message, state: FSMContext):
    await state.clear()
    thinking = await message.answer("🤔 ...")
    answer = await AISupport.get_answer(message.text)
    await thinking.delete()
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Тикет", callback_data="create_ticket")
    builder.button(text="💬 Ещё", callback_data="ask_question")
    builder.button(text="◀️ Меню", callback_data="main_menu")
    builder.adjust(1)
    await message.answer(answer, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "cancel_support")
async def cancel_support(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Отменено")
    await call.answer()


# ==================== ТИКЕТЫ ====================
@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(call: CallbackQuery):
    ticket_id = int(call.data.split("_")[2])
    ticket = TicketModel.get(ticket_id)
    if not ticket: return
    messages = TicketMessageModel.get_by_ticket(ticket_id)
    text = f"📋 #{ticket_id}\n"
    for m in messages[-10:]:
        sender = "👤" if m['sender_type']=='user' else "👨‍💼"
        text += f"{sender}: {m.get('message','')[:200]}\n"
    builder = InlineKeyboardBuilder()
    if ticket['status']=='open':
        builder.button(text="📝 Ответить", callback_data=f"add_message_{ticket_id}")
        builder.button(text="❌ Закрыть", callback_data=f"close_ticket_{ticket_id}")
    builder.button(text="◀️ Назад", callback_data="support")
    await call.message.edit_text(text, reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("close_ticket_"))
async def close_ticket(call: CallbackQuery):
    ticket_id = int(call.data.split("_")[2])
    ticket = TicketModel.get(ticket_id)
    if not ticket or ticket['user_id']!=call.from_user.id: return
    TicketModel.close(ticket_id)
    TicketMessageModel.add(ticket_id,'system',0,"Закрыт пользователем")
    await call.message.edit_text(f"✅ #{ticket_id} закрыт")
    await call.answer()


@router.callback_query(F.data.startswith("add_message_"))
async def add_message(call: CallbackQuery, state: FSMContext):
    ticket_id = int(call.data.split("_")[2])
    await state.set_state(SupportStates.waiting_ticket_message)
    await state.update_data(ticket_id=ticket_id)
    await call.message.edit_text(f"📝 #{ticket_id}\nОтправьте сообщение.\n/cancel_support")
    await call.answer()


# ==================== КЛЮЧ/ТРИАЛ/РЕФЕРАЛЫ ====================
@router.callback_query(F.data == "my_key")
async def show_key(call: CallbackQuery):
    if not UserModel.is_ai_premium(call.from_user.id):
        await call.answer("❌ Нет доступа", show_alert=True); return
    user = UserModel.get(call.from_user.id)
    keys = json.loads(user.get('api_keys','[]'))
    if not keys:
        keys = [f"sk-pro-{uuid.uuid4().hex[:24]}"]
        UserModel.update(call.from_user.id, {'api_keys': json.dumps(keys)})
    text = "🔑\n" + "\n".join([f"<code>{k}</code>" for k in keys])
    await call.message.edit_text(text, reply_markup=InlineKeyboardBuilder().button(text="◀️", callback_data="profile").as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "trial")
async def activate_trial(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    if user.get('trial_until') and datetime.fromisoformat(user['trial_until'])>datetime.now():
        await call.answer("❌ Триал активен!", show_alert=True); return
    UserModel.activate_trial(call.from_user.id)
    await call.answer("✅ 3 дня!", show_alert=True)
    await call.message.edit_text("✅ Триал активирован!")


@router.callback_query(F.data == "referral_menu")
async def referral_menu(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    ref_stats = ReferralModel.get_stats(user['user_id'])
    bot_info = await call.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['referral_code']}"
    text = f"🎁 Рефералы\n🔗 {ref_link}\n📊 {ref_stats['total']}"
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Поделиться", switch_inline_query=ref_link)
    builder.button(text="◀️", callback_data="profile")
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "rating")
async def show_rating(call: CallbackQuery):
    top = UserModel.get_top_users(10)
    text = "🏆 Топ\n"
    for i, u in enumerate(top,1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        text += f"{medal} @{u.get('username','?')} — {u['score']} баллов\n"
    await call.message.edit_text(text, reply_markup=InlineKeyboardBuilder().button(text="◀️", callback_data="profile").as_markup(), parse_mode="HTML")
    await call.answer()


# ==================== SIM ====================
@router.callback_query(F.data == "sim_order")
async def sim_order(call: CallbackQuery):
    if not UserModel.is_sim_premium(call.from_user.id):
        await call.answer("❌ Нет SIM доступа", show_alert=True); return
    builder = InlineKeyboardBuilder()
    for op in ["Билайн","Мегафон","МТС","Tele2"]:
        builder.button(text=op, callback_data=f"simop_{op}")
    builder.button(text="◀️", callback_data="mode_sim")
    builder.adjust(2)
    await call.message.edit_text("📱 Оператор:", reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("simop_"))
async def sim_op(call: CallbackQuery):
    op = call.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    for reg in ["Москва","СПб","Казань"]:
        builder.button(text=reg, callback_data=f"simreg_{op}_{reg}")
    builder.button(text="◀️", callback_data="sim_order")
    builder.adjust(2)
    await call.message.edit_text(f"📱 {op}\n📍 Регион:", reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("simreg_"))
async def sim_reg(call: CallbackQuery):
    parts = call.data.split("_")
    op, reg = parts[1], parts[2]
    builder = InlineKeyboardBuilder()
    for tar in ["Доверенное лицо","Корпоративный"]:
        builder.button(text=tar, callback_data=f"simtar_{op}_{reg}_{tar}")
    builder.button(text="◀️", callback_data=f"simop_{op}")
    await call.message.edit_text(f"📱 {op} | 📍 {reg}\n📋 Тариф:", reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("simtar_"))
async def sim_tar(call: CallbackQuery):
    parts = call.data.split("_")
    op, reg, tar = parts[1], parts[2], parts[3]
    order_id = SimModel.create_order(call.from_user.id, op, reg, tar)
    await call.message.edit_text(f"✅ #{order_id}\n📱 {op}\n📍 {reg}\n📋 {tar}")
    await call.answer()


@router.callback_query(F.data == "sim_orders")
async def sim_orders_list(call: CallbackQuery):
    orders = SimModel.get_user_orders(call.from_user.id)
    text = "📱 Заказы:\n" if orders else "📱 Нет заказов"
    for o in orders[:10]:
        s = "✅" if o['status']=='completed' else "⏳"
        text += f"{s} #{o['order_id']}: {o['operator']}\n"
    await call.message.edit_text(text, reply_markup=InlineKeyboardBuilder().button(text="◀️", callback_data="mode_sim").as_markup(), parse_mode="HTML")
    await call.answer()


# ==================== ПРОМО ====================
@router.message(lambda m: m.text and m.text.upper() in ["WELCOME","VIP50","PREMIUM"])
async def promo(message: Message):
    code = message.text.upper()
    if UserModel.is_ai_premium(message.from_user.id):
        await message.answer("❌ Уже Premium!"); return
    if PromoModel.is_used(message.from_user.id, code):
        await message.answer("❌ Использован!"); return
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
    await message.answer(f"👤 {user['user_id']}")

@router.message(Command("key"))
async def cmd_key(message: Message):
    if not UserModel.is_ai_premium(message.from_user.id):
        await message.answer("❌"); return
    user = UserModel.get(message.from_user.id)
    keys = json.loads(user.get('api_keys','[]'))
    if not keys:
        keys = [f"sk-pro-{uuid.uuid4().hex[:24]}"]
        UserModel.update(message.from_user.id, {'api_keys': json.dumps(keys)})
    await message.answer("\n".join([f"<code>{k}</code>" for k in keys]), parse_mode="HTML")

@router.message(Command("trial"))
async def cmd_trial(message: Message):
    user = UserModel.get(message.from_user.id)
    if user.get('trial_until') and datetime.fromisoformat(user['trial_until'])>datetime.now():
        await message.answer("❌ Триал активен!"); return
    UserModel.activate_trial(message.from_user.id)
    await message.answer("✅ 3 дня!")

@router.message(Command("support"))
async def cmd_support(message: Message):
    existing = TicketModel.get_open_by_user(message.from_user.id)
    if existing:
        await message.answer(f"📞 #{existing['ticket_id']}")
    else:
        ticket_id = TicketModel.create(message.from_user.id)
        await message.answer(f"✅ #{ticket_id}. Опишите проблему.")

@router.message(Command("cancel_support"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено")


# ==================== ECHO (САМЫЙ ПОСЛЕДНИЙ) ====================
@router.message()
async def echo(message: Message, state: FSMContext):
    # Не перехватываем если есть активное состояние
    current_state = await state.get_state()
    if current_state:
        return
    
    # Проверка на сообщение в тикет
    existing = TicketModel.get_open_by_user(message.from_user.id)
    if existing:
        TicketMessageModel.add(existing['ticket_id'], 'user', message.from_user.id, message.text or "[Медиа]")
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(admin_id,
                    f"🔔 Тикет #{existing['ticket_id']}\n👤 @{message.from_user.username}\n📝 {message.text[:300]}",
                    parse_mode="HTML")
            except: pass
        await message.answer(f"✅ Добавлено в #{existing['ticket_id']}")
        return
    
    await message.answer("Используйте меню или /start")
