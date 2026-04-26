import json
import uuid
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import UserModel, ReferralModel, TicketModel, TicketMessageModel, PromoModel, SimModel
from config import ADMIN_IDS, AI_PAYMENT_AMOUNT
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
    builder.button(text="📛 FRAGMENT", callback_data="mode_fragment")
    builder.button(text="📞 Поддержка", callback_data="support")
    builder.adjust(2, 2, 1)
    await message.answer("🚀 <b>MULTIACCES</b>\n\n🤖 AI | 📱 SIM | 💰 CASH | 📛 FRAGMENT\n\nВыберите раздел:", reply_markup=builder.as_markup(), parse_mode="HTML")

# ==================== СТАРТ ====================
@router.message(CommandStart(deep_link=True))
async def start_deep(message: Message, command: CommandObject):
    user_id = message.from_user.id
    if not UserModel.get(user_id): UserModel.create(user_id, message.from_user.username or '', message.from_user.first_name or '', message.from_user.last_name or '')
    await show_mode_selection(message)

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if not UserModel.get(user_id): UserModel.create(user_id, message.from_user.username or '', message.from_user.first_name or '', message.from_user.last_name or '')
    await show_mode_selection(message)

@router.callback_query(F.data == "mode_ai")
async def mode_ai(call: CallbackQuery): await call.message.edit_text("🤖 AI Access", reply_markup=get_main_keyboard()); await call.answer()

@router.callback_query(F.data == "mode_sim")
async def mode_sim(call: CallbackQuery): await call.message.edit_text("📱 SIM.DL", reply_markup=get_sim_keyboard()); await call.answer()

@router.callback_query(F.data == "main_menu")
async def back_main(call: CallbackQuery): await show_mode_selection(call.message); await call.answer()

# ==================== ПРОФИЛЬ ====================
@router.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    if not user: return
    ai = "💎" if UserModel.is_ai_premium(call.from_user.id) else "❌"
    text = f"👤 {user['user_id']}\n🤖 AI: {ai}"
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 Ключ", callback_data="my_key")
    builder.button(text="👥 Рефералы", callback_data="referral_menu")
    builder.button(text="◀️", callback_data="main_menu")
    await call.message.edit_text(text, reply_markup=builder.as_markup()); await call.answer()

# ==================== ПОДДЕРЖКА ====================
@router.callback_query(F.data == "support")
async def support(call: CallbackQuery):
    existing = TicketModel.get_open_by_user(call.from_user.id)
    if existing:
        builder = InlineKeyboardBuilder()
        builder.button(text="📋 Тикет", callback_data=f"view_ticket_{existing['ticket_id']}")
        builder.button(text="💬 Автоответчик", callback_data="ask_question")
        builder.button(text="◀️", callback_data="main_menu"); builder.adjust(1)
        await call.message.edit_text(f"📞 Тикет #{existing['ticket_id']}", reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Создать тикет", callback_data="create_ticket")
        builder.button(text="💬 Задать вопрос", callback_data="ask_question")
        builder.button(text="◀️", callback_data="main_menu"); builder.adjust(1)
        await call.message.edit_text("📞 Поддержка", reply_markup=builder.as_markup())
    await call.answer()

@router.callback_query(F.data == "create_ticket")
async def create_ticket(call: CallbackQuery, state: FSMContext):
    existing = TicketModel.get_open_by_user(call.from_user.id)
    if existing: await call.answer(f"Уже есть #{existing['ticket_id']}", show_alert=True); return
    ticket_id = TicketModel.create(call.from_user.id)
    await state.set_state(SupportStates.waiting_ticket_message)
    await state.update_data(ticket_id=ticket_id)
    await call.message.edit_text(f"✅ Тикет #{ticket_id}\nОпишите проблему.\n/cancel_support")

@router.message(SupportStates.waiting_ticket_message)
async def ticket_msg(message: Message, state: FSMContext):
    data = await state.get_data()
    TicketMessageModel.add(data['ticket_id'], 'user', message.from_user.id, message.text or "")
    await state.clear()
    await message.answer(f"✅ Добавлено в #{data['ticket_id']}")

@router.callback_query(F.data == "ask_question")
async def ask_q(call: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_question)
    await call.message.edit_text("💬 Задайте вопрос:")

@router.message(SupportStates.waiting_question)
async def process_q(message: Message, state: FSMContext):
    await state.clear()
    answer = await AISupport.get_answer(message.text)
    await message.answer(answer, parse_mode="HTML")

@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(call: CallbackQuery):
    ticket_id = int(call.data.split("_")[2])
    messages = TicketMessageModel.get_by_ticket(ticket_id)
    text = f"📋 #{ticket_id}\n"
    for m in messages[-10:]: text += f"{'👤' if m['sender_type']=='user' else '👨‍💼'}: {m.get('message','')[:200]}\n"
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Ответить", callback_data=f"add_msg_{ticket_id}")
    builder.button(text="❌ Закрыть", callback_data=f"close_tkt_{ticket_id}")
    builder.button(text="◀️", callback_data="support"); builder.adjust(2,1)
    await call.message.edit_text(text, reply_markup=builder.as_markup()); await call.answer()

@router.callback_query(F.data.startswith("close_tkt_"))
async def close_tkt(call: CallbackQuery):
    TicketModel.close(int(call.data.split("_")[2]))
    await call.message.edit_text("✅ Закрыт"); await call.answer()

@router.callback_query(F.data.startswith("add_msg_"))
async def add_msg(call: CallbackQuery, state: FSMContext):
    ticket_id = int(call.data.split("_")[2])
    await state.set_state(SupportStates.waiting_ticket_message)
    await state.update_data(ticket_id=ticket_id)
    await call.message.edit_text(f"📝 Отправьте сообщение для #{ticket_id}")

# ==================== КЛЮЧ/ТРИАЛ/РЕФЕРАЛЫ ====================
@router.callback_query(F.data == "my_key")
async def my_key(call: CallbackQuery):
    if not UserModel.is_ai_premium(call.from_user.id): await call.answer("❌ Нет доступа"); return
    user = UserModel.get(call.from_user.id)
    keys = json.loads(user.get('api_keys','[]'))
    if not keys: keys = [f"sk-pro-{uuid.uuid4().hex[:24]}"]; UserModel.update(call.from_user.id, {'api_keys': json.dumps(keys)})
    await call.message.edit_text("🔑\n" + "\n".join([f"<code>{k}</code>" for k in keys]), parse_mode="HTML"); await call.answer()

@router.callback_query(F.data == "trial")
async def trial(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    if user.get('trial_until') and datetime.fromisoformat(user['trial_until'])>datetime.now(): await call.answer("❌ Активен!"); return
    UserModel.activate_trial(call.from_user.id); await call.answer("✅ 3 дня!"); await call.message.edit_text("✅ Триал!")

@router.callback_query(F.data == "referral_menu")
async def ref_menu(call: CallbackQuery):
    user = UserModel.get(call.from_user.id)
    ref = ReferralModel.get_stats(user['user_id'])
    bot_info = await call.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref_{user['referral_code']}"
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Поделиться", switch_inline_query=link)
    builder.button(text="◀️", callback_data="profile")
    await call.message.edit_text(f"🎁 Рефералы\n🔗 {link}\n📊 {ref['total']}", reply_markup=builder.as_markup()); await call.answer()

# ==================== ПРОМО ====================
@router.message(lambda m: m.text and m.text.upper() in ["WELCOME","VIP50","PREMIUM"])
async def promo(message: Message):
    code = message.text.upper()
    if UserModel.is_ai_premium(message.from_user.id): await message.answer("❌ Уже Premium!"); return
    promo = PromoModel.check(code)
    if not promo: await message.answer("❌ Не найден!"); return
    discount = int(AI_PAYMENT_AMOUNT * promo['discount'] / 100)
    PromoModel.use(message.from_user.id, code, promo['discount'])
    await message.answer(f"✅ {code}! Скидка {promo['discount']}%\nЦена: <b>{AI_PAYMENT_AMOUNT - discount}₽</b>", parse_mode="HTML")

# ==================== ECHO ====================
@router.message()
async def echo(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state: return
    existing = TicketModel.get_open_by_user(message.from_user.id)
    if existing:
        TicketMessageModel.add(existing['ticket_id'], 'user', message.from_user.id, message.text or "")
        await message.answer(f"✅ Добавлено в #{existing['ticket_id']}")
        return
    await message.answer("Меню: /start")
