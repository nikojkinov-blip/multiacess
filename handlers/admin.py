import asyncio
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import UserModel, PaymentModel, TicketModel, BanModel, SettingsModel, db
from database.utils import backup_database, export_users_to_csv, get_stats
from config import ADMIN_IDS, CARD_NUMBER, BANK_NAME, AI_PAYMENT_AMOUNT, SIM_PAYMENT_AMOUNT, FRAGMENT_ITEMS
from keyboards.inline import get_admin_keyboard

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ==================== АДМИН-ПАНЕЛЬ ====================
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id): return
    stats = get_stats()
    text = f"👑 Админ-панель\n👥 {stats['total_users']} | 🤖 {stats['paid_users']} | 💰 {stats['total_revenue']}₽"
    await message.answer(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")

@router.message(Command("users"))
async def cmd_users(message: Message):
    if not is_admin(message.from_user.id): return
    users = UserModel.get_all(30)
    text = "👥 Пользователи:\n"
    for u in users: text += f"<code>{u['user_id']}</code> @{u.get('username','?')}\n"
    await message.answer(text, parse_mode="HTML")

@router.message(Command("userinfo"))
async def cmd_userinfo(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2: return
    user = UserModel.get(int(args[1]))
    if not user: return
    text = f"👤 {user['user_id']}\n🤖 {'✅' if user.get('paid') else '❌'} | 📱 {'✅' if user.get('sim_paid') else '❌'}"
    builder = InlineKeyboardBuilder()
    builder.button(text="🤖 AI Premium", callback_data=f"set_ai_{user['user_id']}")
    builder.button(text="📱 SIM Premium", callback_data=f"set_sim_{user['user_id']}")
    builder.button(text="🚫 Бан" if not user.get('is_banned') else "✅ Разбан", callback_data=f"ban_{user['user_id']}")
    builder.adjust(2,1)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

# ==================== ДЕЙСТВИЯ ====================
@router.callback_query(F.data.startswith("set_ai_"))
async def set_ai(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    UserModel.set_ai_paid(int(call.data.split("_")[2]))
    await call.answer("✅ AI Premium выдан!")

@router.callback_query(F.data.startswith("set_sim_"))
async def set_sim(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    UserModel.set_sim_paid(int(call.data.split("_")[2]))
    await call.answer("✅ SIM Premium выдан!")

@router.callback_query(F.data.startswith("ban_"))
async def toggle_ban(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    user_id = int(call.data.split("_")[1])
    if BanModel.is_banned(user_id): BanModel.remove(user_id); await call.answer("✅ Разбанен")
    else: BanModel.add(user_id, "Нарушение", call.from_user.id); await call.answer("🚫 Забанен")

# ==================== ВЫДАЧА CASH ====================
@router.message(Command("cashorders"))
async def cmd_cash_orders(message: Message):
    if not is_admin(message.from_user.id): return
    from config import CASH_ITEMS
    orders = db.fetchall("SELECT * FROM cash_orders WHERE status='pending' ORDER BY created_at DESC")
    if not orders: await message.answer("Нет заказов Cash"); return
    text = "💰 Заказы Cash:\n\n"
    for o in orders:
        item = CASH_ITEMS.get(o['item_key'], {})
        text += f"#{o['order_id']} | {item.get('name', o['item_key'])} | {o['amount']}₽ | User: <code>{o['user_id']}</code>\n"
    builder = InlineKeyboardBuilder()
    for o in orders[:10]: builder.button(text=f"Выдать #{o['order_id']}", callback_data=f"cashdone_{o['order_id']}")
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("cashdone_"))
async def complete_cash(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    order_id = int(call.data.split("_")[1])
    db.update('cash_orders', {'status': 'completed', 'completed_at': datetime.now().isoformat()}, 'order_id=?', (order_id,))
    order = db.fetchone("SELECT * FROM cash_orders WHERE order_id=?", (order_id,))
    if order:
        try: await call.bot.send_message(order['user_id'], f"✅ Заказ #{order_id} выполнен!")
        except: pass
    await call.message.edit_text(call.message.text + f"\n\n✅ #{order_id} ВЫДАН")
    await call.answer("✅ Выдан!")

# ==================== ВЫДАЧА FRAGMENT ====================
@router.message(Command("fragorders"))
async def cmd_frag_orders(message: Message):
    if not is_admin(message.from_user.id): return
    orders = db.fetchall("SELECT * FROM fragment_orders WHERE status='pending' ORDER BY created_at DESC")
    if not orders: await message.answer("📛 Нет заказов Fragment"); return
    text = "📛 Заказы Fragment:\n\n"
    for o in orders:
        item = FRAGMENT_ITEMS.get(o['item_key'], {})
        phone = o.get('phone', 'Не указан')
        text += f"#{o['order_id']} | {item.get('name', o['item_key'])} | {o['amount']}₽ | 📱 <code>{phone}</code> | User: <code>{o['user_id']}</code>\n"
    builder = InlineKeyboardBuilder()
    for o in orders[:10]: builder.button(text=f"✅ Выдать #{o['order_id']}", callback_data=f"fragdone_{o['order_id']}")
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("fragdone_"))
async def complete_frag(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    order_id = int(call.data.split("_")[1])
    db.update('fragment_orders', {'status': 'completed', 'completed_at': datetime.now().isoformat()}, 'order_id=?', (order_id,))
    order = db.fetchone("SELECT * FROM fragment_orders WHERE order_id=?", (order_id,))
    if order:
        try: await call.bot.send_message(order['user_id'], f"✅ Заказ #{order_id} выполнен! Юзернейм привязан.", parse_mode="HTML")
        except: pass
    await call.message.edit_text(call.message.text + f"\n\n✅ #{order_id} ВЫДАН")
    await call.answer("✅ Выдан!")

# ==================== РАССЫЛКА ====================
@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split(maxsplit=1)
    if len(args) < 2: await message.answer("/broadcast ТЕКСТ"); return
    text = args[1]
    users = db.fetchall("SELECT user_id FROM users")
    sent = 0
    for u in users:
        try: await message.bot.send_message(u['user_id'], f"📢 {text}", parse_mode="HTML"); sent += 1
        except: pass
    await message.answer(f"✅ Отправлено: {sent}/{len(users)}")

# ==================== БЭКАП ====================
@router.message(Command("backup"))
async def cmd_backup(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer_document(FSInputFile(backup_database()), caption="💾 Бэкап")

@router.message(Command("export"))
async def cmd_export(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer_document(FSInputFile(export_users_to_csv()), caption="📊 Экспорт")
