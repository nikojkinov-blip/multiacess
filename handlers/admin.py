import asyncio
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import (
    UserModel, PaymentModel, TicketModel, BanModel,
    SettingsModel, db, SimModel
)
from database.utils import (
    backup_database, export_users_to_csv, export_payments_to_csv,
    get_stats, get_daily_stats
)
from config import (
    ADMIN_IDS, CARD_NUMBER, BANK_NAME, 
    AI_PAYMENT_AMOUNT, SIM_PAYMENT_AMOUNT
)
from keyboards.inline import get_admin_keyboard, get_main_keyboard

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============== АДМИН-ПАНЕЛЬ ==============
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    stats = get_stats()
    
    text = f"""
👑 <b>Админ-панель AI Access + SIM.DL</b>

📊 <b>Статистика:</b>
• Всего пользователей: {stats['total_users']}
• AI Premium: {stats['paid_users']}
• SIM Premium: {stats.get('sim_paid', 0)}
• Открыто тикетов: {stats['open_tickets']}
• Доход всего: {stats['total_revenue']} ₽

🛠 <b>Команды:</b>
/users — Список пользователей
/userinfo ID — Инфо о пользователе
/ban ID причина — Забанить
/unban ID — Разбанить
/opentickets — Открытые тикеты
/simorders — SIM заказы
/stats — Статистика
/broadcast — Рассылка
/export — Экспорт
/backup — Бэкап
/addsim — Добавить SIM номер
/setcard — Сменить карту
/setprice — Сменить цену
"""
    await message.answer(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")


# ============== ПОЛЬЗОВАТЕЛИ ==============
@router.message(Command("users"))
async def cmd_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    users = UserModel.get_all(limit=30)
    
    if not users:
        await message.answer("Нет пользователей")
        return
    
    text = "📋 <b>Последние 30 пользователей:</b>\n\n"
    for u in users:
        ai = "💎" if u.get('paid') else "—"
        sim = "📱" if u.get('sim_paid') else "—"
        text += f"{ai}{sim} <code>{u['user_id']}</code> — @{u.get('username', 'No')}\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("userinfo"))
async def cmd_userinfo(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /userinfo ID")
        return
    
    try:
        user_id = int(args[1])
    except:
        await message.answer("Неверный ID")
        return
    
    user = UserModel.get(user_id)
    if not user:
        await message.answer("Пользователь не найден")
        return
    
    payments = PaymentModel.get_by_user(user_id)
    sim_orders = SimModel.get_user_orders(user_id)
    
    text = f"""
👤 <b>Информация о пользователе</b>

🆔 ID: <code>{user['user_id']}</code>
📛 Имя: {user.get('first_name', '—')}
👤 Username: @{user.get('username', '—')}
🤖 AI Premium: {'✅' if user.get('paid') else '❌'}
📱 SIM Premium: {'✅' if user.get('sim_paid') else '❌'}
🚫 Забанен: {'Да' if user.get('is_banned') else 'Нет'}
📅 Регистрация: {user.get('joined_date', '—')[:10]}

💰 <b>Платежи ({len(payments)}):</b>
"""
    for p in payments[:5]:
        status = "✅" if p['status'] == 'confirmed' else "⏳"
        ptype = "SIM" if p.get('payment_type') == 'sim_dl' else "AI"
        text += f"{status} {ptype} — {p['amount']}₽\n"
    
    text += f"\n📱 <b>SIM заказы ({len(sim_orders)}):</b>\n"
    for o in sim_orders[:5]:
        status = "✅" if o['status'] == 'completed' else "⏳"
        text += f"{status} #{o['order_id']} — {o['operator']} | {o['region']}\n"
    
    builder = InlineKeyboardBuilder()
    if user.get('is_banned'):
        builder.button(text="✅ Разбанить", callback_data=f"unban_{user_id}")
    else:
        builder.button(text="🚫 Забанить", callback_data=f"ban_{user_id}")
    
    if not user.get('paid'):
        builder.button(text="🤖 Выдать AI Premium", callback_data=f"set_ai_paid_{user_id}")
    if not user.get('sim_paid'):
        builder.button(text="📱 Выдать SIM Premium", callback_data=f"set_sim_paid_{user_id}")
    
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


# ============== БАН/РАЗБАН ==============
@router.message(Command("ban"))
async def cmd_ban(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.answer("Использование: /ban ID [причина]")
        return
    
    try:
        user_id = int(args[1])
    except:
        await message.answer("Неверный ID")
        return
    
    reason = args[2] if len(args) > 2 else "Нарушение правил"
    
    BanModel.add(user_id, reason, message.from_user.id)
    
    try:
        await message.bot.send_message(user_id, f"🚫 Вы заблокированы\nПричина: {reason}")
    except:
        pass
    
    await message.answer(f"✅ Пользователь {user_id} заблокирован")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /unban ID")
        return
    
    try:
        user_id = int(args[1])
    except:
        await message.answer("Неверный ID")
        return
    
    BanModel.remove(user_id)
    
    try:
        await message.bot.send_message(user_id, "✅ Вы разблокированы!")
    except:
        pass
    
    await message.answer(f"✅ Пользователь {user_id} разблокирован")


# ============== РАССЫЛКА ==============
@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "📢 <b>Использование:</b>\n"
            "/broadcast ТЕКСТ — отправить рассылку всем\n\n"
            "После отправки команды выберите аудиторию.",
            parse_mode="HTML"
        )
        return
    
    text = args[1]
    
    # Сохраняем текст во временное хранилище
    router.temp_broadcast_text = text
    
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Всем", callback_data="bc_all")
    builder.button(text="🤖 AI Premium", callback_data="bc_ai_paid")
    builder.button(text="📱 SIM Premium", callback_data="bc_sim_paid")
    builder.button(text="🆓 Без подписки", callback_data="bc_unpaid")
    builder.button(text="❌ Отмена", callback_data="bc_cancel")
    builder.adjust(2, 2, 1)
    
    await message.answer(
        f"📢 <b>Предпросмотр рассылки:</b>\n\n{text}\n\n"
        "Выберите аудиторию:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("bc_"))
async def broadcast_execute(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Нет доступа")
        return
    
    target = call.data.split("_")[1]
    
    if target == "cancel":
        await call.message.edit_text("❌ Рассылка отменена")
        await call.answer()
        return
    
    # Получаем текст рассылки
    text = getattr(router, 'temp_broadcast_text', call.message.text)
    
    # Получаем пользователей
    if target == "ai_paid":
        users_data = db.fetchall("SELECT user_id FROM users WHERE paid = 1")
    elif target == "sim_paid":
        users_data = db.fetchall("SELECT user_id FROM users WHERE sim_paid = 1")
    elif target == "unpaid":
        users_data = db.fetchall("SELECT user_id FROM users WHERE paid = 0 AND sim_paid = 0")
    else:
        users_data = db.fetchall("SELECT user_id FROM users")
    
    users = [u['user_id'] for u in users_data]
    
    await call.message.edit_text(f"📢 Рассылка начата. Пользователей: {len(users)}")
    
    sent = 0
    failed = 0
    
    for user_id in users:
        try:
            await call.bot.send_message(user_id, f"📢 {text}", parse_mode="HTML")
            sent += 1
        except:
            failed += 1
    
    await call.message.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}",
        parse_mode="HTML"
    )
    await call.answer()


# ============== ТИКЕТЫ ==============
@router.message(Command("opentickets"))
async def cmd_open_tickets(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    tickets = TicketModel.get_all_open()
    
    if not tickets:
        await message.answer("📭 Нет открытых тикетов")
        return
    
    text = f"📋 <b>Открытые тикеты ({len(tickets)}):</b>\n\n"
    for t in tickets[:20]:
        user = UserModel.get(t['user_id'])
        username = f"@{user['username']}" if user and user.get('username') else f"ID:{t['user_id']}"
        text += f"#{t['ticket_id']} — {username}\n"
    
    await message.answer(text, parse_mode="HTML")


# ============== SIM ЗАКАЗЫ ==============
@router.message(Command("simorders"))
async def cmd_sim_orders(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    orders = db.fetchall("SELECT * FROM sim_orders WHERE status = 'pending' ORDER BY created_at DESC")
    
    if not orders:
        await message.answer("📱 Нет ожидающих SIM заказов")
        return
    
    text = f"📱 <b>Ожидающие SIM заказы ({len(orders)}):</b>\n\n"
    for o in orders[:20]:
        user = UserModel.get(o['user_id'])
        username = f"@{user['username']}" if user and user.get('username') else f"ID:{o['user_id']}"
        text += f"#{o['order_id']} — {username} | {o['operator']} | {o['region']} | {o['tariff']}\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("addsim"))
async def cmd_add_sim(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split(maxsplit=4)
    if len(args) < 5:
        await message.answer(
            "📱 <b>Использование:</b>\n"
            "/addsim НОМЕР ОПЕРАТОР РЕГИОН ТАРИФ\n\n"
            "Пример:\n"
            "/addsim +79261234567 Билайн Москва Доверенное_лицо",
            parse_mode="HTML"
        )
        return
    
    phone = args[1]
    operator = args[2]
    region = args[3]
    tariff = args[4]
    
    db.insert('sim_numbers', {
        'phone': phone,
        'operator': operator,
        'region': region,
        'tariff': tariff,
        'status': 'available',
        'added_at': datetime.now().isoformat()
    })
    
    await message.answer(f"✅ Номер {phone} добавлен в базу!\nОператор: {operator}\nРегион: {region}\nТариф: {tariff}")


# ============== СТАТИСТИКА ==============
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    stats = get_stats()
    
    text = f"""
📊 <b>Статистика бота</b>

👥 <b>Пользователи:</b>
• Всего: {stats['total_users']}
• AI Premium: {stats['paid_users']}
• Конверсия AI: {(stats['paid_users']/stats['total_users']*100):.1f}% if stats['total_users'] > 0 else 0

💰 <b>Финансы:</b>
• Доход всего: {stats['total_revenue']} ₽

📋 Тикетов открыто: {stats['open_tickets']}
📱 SIM заказов: {stats.get('pending_sim_orders', 0)}

📅 За 24 часа:
• Новых: {stats['new_users_24h']}
• Оплат: {stats['payments_24h']}
"""
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Экспорт CSV", callback_data="export_users")
    builder.button(text="💾 Бэкап", callback_data="admin_backup")
    builder.adjust(2)
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


# ============== ЭКСПОРТ ==============
@router.message(Command("export"))
async def cmd_export(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Пользователи CSV", callback_data="export_users")
    builder.button(text="💰 Платежи CSV", callback_data="export_payments")
    builder.adjust(1)
    
    await message.answer("📥 Выберите тип экспорта:", reply_markup=builder.as_markup())


@router.callback_query(F.data == "export_users")
async def export_users_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    filepath = export_users_to_csv()
    
    await call.message.answer_document(
        FSInputFile(filepath),
        caption=f"📊 Экспорт пользователей\n{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    await call.answer("✅ Готово!")


@router.callback_query(F.data == "export_payments")
async def export_payments_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    filepath = export_payments_to_csv()
    
    await call.message.answer_document(
        FSInputFile(filepath),
        caption=f"💰 Экспорт платежей\n{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    await call.answer("✅ Готово!")


# ============== БЭКАП ==============
@router.message(Command("backup"))
async def cmd_backup(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    filepath = backup_database()
    
    await message.answer_document(
        FSInputFile(filepath),
        caption=f"💾 Резервная копия БД\n{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )


@router.callback_query(F.data == "admin_backup")
async def admin_backup_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    filepath = backup_database()
    
    await call.message.answer_document(
        FSInputFile(filepath),
        caption=f"💾 Бэкап БД\n{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    await call.answer("✅ Бэкап создан!")


# ============== НАСТРОЙКИ ==============
@router.message(Command("setcard"))
async def cmd_setcard(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /setcard НОМЕР_КАРТЫ")
        return
    
    new_card = args[1].strip()
    SettingsModel.set('card_number', new_card)
    
    global CARD_NUMBER
    CARD_NUMBER = new_card
    
    await message.answer(f"✅ Номер карты обновлён: {new_card}")


@router.message(Command("setprice"))
async def cmd_setprice(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Использование: /setprice ai|sim СУММА")
        return
    
    ptype = args[1].lower()
    try:
        amount = int(args[2])
    except:
        await message.answer("Неверная сумма")
        return
    
    if ptype == "ai":
        SettingsModel.set('ai_price', amount)
        global AI_PAYMENT_AMOUNT
        AI_PAYMENT_AMOUNT = amount
        await message.answer(f"✅ Цена AI Access: {amount} ₽")
    elif ptype == "sim":
        SettingsModel.set('sim_price', amount)
        global SIM_PAYMENT_AMOUNT
        SIM_PAYMENT_AMOUNT = amount
        await message.answer(f"✅ Цена SIM.DL: {amount} ₽")
    else:
        await message.answer("Укажите ai или sim")


# ============== КОЛБЭКИ АДМИН-ПАНЕЛИ ==============
@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    stats = get_stats()
    
    text = f"""
👑 <b>Админ-панель</b>

📊 Пользователей: {stats['total_users']}
🤖 AI Premium: {stats['paid_users']}
💰 Доход: {stats['total_revenue']} ₽
"""
    
    await call.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "admin_users")
async def admin_users_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    users = UserModel.get_all(limit=20)
    
    text = "👥 <b>Последние 20:</b>\n\n"
    for u in users:
        text += f"<code>{u['user_id']}</code> — @{u.get('username', 'No')}\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "admin_payments")
async def admin_payments_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    payments = PaymentModel.get_all(limit=20)
    
    text = "💰 <b>Последние 20 платежей:</b>\n\n"
    for p in payments:
        status = "✅" if p['status'] == 'confirmed' else "⏳"
        ptype = "SIM" if p.get('payment_type') == 'sim_dl' else "AI"
        text += f"{status} #{p['payment_id']} — {ptype} — {p['amount']}₽\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "admin_sim_orders")
async def admin_sim_orders_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    orders = db.fetchall("SELECT * FROM sim_orders ORDER BY created_at DESC LIMIT 20")
    
    text = "📱 <b>Последние 20 SIM заказов:</b>\n\n"
    for o in orders:
        status = "✅" if o['status'] == 'completed' else "⏳"
        num = o.get('sim_number', '—')
        text += f"{status} #{o['order_id']} — {o['operator']} | {num}\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "admin_tickets")
async def admin_tickets_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    tickets = TicketModel.get_all_open()
    
    text = f"📋 <b>Открытые тикеты ({len(tickets)}):</b>\n\n"
    for t in tickets[:20]:
        text += f"#{t['ticket_id']} — User: {t['user_id']}\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    stats = get_stats()
    
    text = f"""
📊 <b>Статистика</b>

👥 Всего: {stats['total_users']}
🤖 AI: {stats['paid_users']}
📱 SIM: {stats.get('sim_paid', 0)}
💰 Доход: {stats['total_revenue']} ₽
📋 Тикеты: {stats['open_tickets']}
"""
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    await call.message.edit_text(
        "📢 Используйте команду /broadcast ТЕКСТ для создания рассылки.",
        reply_markup=InlineKeyboardBuilder().button(
            text="◀️ Назад", callback_data="admin_panel"
        ).as_markup()
    )
    await call.answer()


@router.callback_query(F.data == "admin_settings")
async def admin_settings_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    text = f"""
⚙️ <b>Настройки</b>

💳 Карта: {CARD_NUMBER}
🏦 Банк: {BANK_NAME}
🤖 AI цена: {AI_PAYMENT_AMOUNT} ₽
📱 SIM цена: {SIM_PAYMENT_AMOUNT} ₽

Команды:
/setcard НОМЕР — сменить карту
/setprice ai|sim СУММА — сменить цену
"""
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "close_admin")
async def close_admin_callback(call: CallbackQuery):
    await call.message.delete()
    await call.answer()


# ============== ДЕЙСТВИЯ С ПОЛЬЗОВАТЕЛЯМИ ==============
@router.callback_query(F.data.startswith("ban_"))
async def ban_user_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    user_id = int(call.data.split("_")[1])
    BanModel.add(user_id, "Нарушение правил", call.from_user.id)
    
    try:
        await call.bot.send_message(user_id, "🚫 Вы заблокированы администратором")
    except:
        pass
    
    await call.message.edit_text(call.message.text + f"\n\n✅ Пользователь {user_id} заблокирован")
    await call.answer("✅ Заблокирован")


@router.callback_query(F.data.startswith("unban_"))
async def unban_user_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    user_id = int(call.data.split("_")[1])
    BanModel.remove(user_id)
    
    try:
        await call.bot.send_message(user_id, "✅ Вы разблокированы!")
    except:
        pass
    
    await call.message.edit_text(call.message.text + f"\n\n✅ Пользователь {user_id} разблокирован")
    await call.answer("✅ Разблокирован")


@router.callback_query(F.data.startswith("set_ai_paid_"))
async def set_ai_paid_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    user_id = int(call.data.split("_")[3])
    UserModel.set_ai_paid(user_id)
    
    try:
        await call.bot.send_message(user_id, "🤖 Вам выдан AI Premium! Используйте /key")
    except:
        pass
    
    await call.message.edit_text(call.message.text + "\n\n✅ AI Premium выдан")
    await call.answer("✅ Выдан")


@router.callback_query(F.data.startswith("set_sim_paid_"))
async def set_sim_paid_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа")
        return
    
    user_id = int(call.data.split("_")[3])
    UserModel.set_sim_paid(user_id)
    
    try:
        await call.bot.send_message(user_id, "📱 Вам выдан SIM.DL доступ! Создайте заказ.")
    except:
        pass
    
    await call.message.edit_text(call.message.text + "\n\n✅ SIM.DL Premium выдан")
    await call.answer("✅ Выдан")