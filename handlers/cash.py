from aiogram import Router, F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import db
from config import CASH_ITEMS, CASH_CATEGORIES, CARD_NUMBER, BANK_NAME, ADMIN_IDS
from datetime import datetime

router = Router()


@router.callback_query(F.data == "mode_cash")
async def show_cash_menu(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for cat_key, cat_name in CASH_CATEGORIES.items():
        builder.button(text=cat_name, callback_data=f"cashcat_{cat_key}")
    builder.button(text="📋 МОИ ПОКУПКИ", callback_data="cash_orders")
    builder.button(text="◀️ СМЕНИТЬ РЕЖИМ", callback_data="main_menu")
    builder.adjust(1)
    
    await call.message.edit_text(
        "💰 <b>CASH.DL — ОБНАЛ И СПЛИТЫ</b>\n\n"
        "💳 Схемы обнала через самозанятых\n"
        "₿ Крипто-сплиты без KYC\n"
        "🏢 Оформление дропов\n"
        "📊 Схемы возвратов\n\n"
        "Выберите категорию:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("cashcat_"))
async def show_cash_items(call: CallbackQuery):
    category = call.data.split("_")[1]
    cat_name = CASH_CATEGORIES.get(category, category)
    
    builder = InlineKeyboardBuilder()
    for key, item in CASH_ITEMS.items():
        if item['category'] == category:
            builder.button(
                text=f"{item['name']} — {item['price']}₽",
                callback_data=f"cashbuy_{key}"
            )
    builder.button(text="◀️ НАЗАД", callback_data="mode_cash")
    builder.adjust(1)
    
    await call.message.edit_text(
        f"💰 {cat_name}\n\n<b>Доступные схемы:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("cashbuy_"))
async def buy_cash_item(call: CallbackQuery):
    item_key = call.data.split("_")[1]
    item = CASH_ITEMS.get(item_key)
    
    if not item:
        await call.answer("Товар не найден")
        return
    
    order_id = db.insert('cash_orders', {
        'user_id': call.from_user.id,
        'item_key': item_key,
        'amount': item['price'],
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    })
    
    for admin_id in ADMIN_IDS:
        try:
            await call.bot.send_message(
                admin_id,
                f"🔔 <b>Новый заказ CASH.DL!</b>\n"
                f"👤 User: {call.from_user.id}\n"
                f"🛒 {item['name']}\n"
                f"💰 {item['price']}₽\n"
                f"🆔 #{order_id}",
                parse_mode="HTML"
            )
        except:
            pass
    
    await call.message.edit_text(
        f"✅ <b>ЗАКАЗ #{order_id}</b>\n\n"
        f"🛒 {item['name']}\n"
        f"💰 Сумма: {item['price']} ₽\n\n"
        f"💳 <b>ОПЛАТА:</b>\n"
        f"<code>{CARD_NUMBER}</code>\n"
        f"🏦 {BANK_NAME}\n\n"
        f"После оплаты материал будет отправлен.",
        reply_markup=InlineKeyboardBuilder().button(
            text="📋 МОИ ПОКУПКИ", callback_data="cash_orders"
        ).as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "cash_orders")
async def show_cash_orders(call: CallbackQuery):
    orders = db.fetchall(
        "SELECT * FROM cash_orders WHERE user_id = ? ORDER BY created_at DESC",
        (call.from_user.id,)
    )
    
    if not orders:
        text = "💰 У вас пока нет покупок."
    else:
        text = "💰 <b>ВАШИ ПОКУПКИ:</b>\n\n"
        for o in orders:
            item = CASH_ITEMS.get(o['item_key'], {})
            status = "✅" if o['status'] == 'completed' else "⏳"
            text += f"{status} #{o['order_id']}: {item.get('name','?')} — {o['amount']}₽\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 КАТАЛОГ", callback_data="mode_cash")
    builder.button(text="◀️ НАЗАД", callback_data="main_menu")
    builder.adjust(1)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()
