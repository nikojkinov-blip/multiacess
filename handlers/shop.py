from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import ShopModel
from config import (
    SHOP_BRAND, SHOP_SLOGAN, SHOP_CITIES, SHOP_DISTRICTS,
    SHOP_ITEMS, SHOP_CATEGORIES, ADMIN_IDS, CARD_NUMBER, BANK_NAME
)

router = Router()

WELCOME = f"""
{SHOP_BRAND}
<i>{SHOP_SLOGAN}</i>

🔬 Лабораторные исследования с 2024
🧪 Чистота продуктов — наш приоритет
📊 Все партии проходят тестирование

🏙 <b>Кластеры:</b> {', '.join(SHOP_CITIES)}

⚠️ Только предоплата
🔐 Полная анонимность
"""


@router.callback_query(F.data == "mode_shop")
async def show_shop_menu(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🧪 КАТАЛОГ", callback_data="shop_catalog")
    builder.button(text="🔥 ХИТЫ", callback_data="shop_hits")
    builder.button(text="📋 МОИ ЗАКАЗЫ", callback_data="shop_orders")
    builder.button(text="📞 ТЕХПОДДЕРЖКА", callback_data="support")
    builder.button(text="◀️ СМЕНИТЬ РЕЖИМ", callback_data="main_menu")
    builder.adjust(1)
    
    await call.message.edit_text(
        WELCOME,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "shop_catalog")
async def show_cities(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for city in SHOP_CITIES:
        builder.button(text=f"🏙 {city}", callback_data=f"shopcity_{city}")
    builder.button(text="◀️ НАЗАД", callback_data="mode_shop")
    builder.adjust(2, 1)
    
    await call.message.edit_text(
        f"{SHOP_BRAND}\n\n📍 <b>ВЫБЕРИ КЛАСТЕР:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "shop_hits")
async def show_hits(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for key, item in SHOP_ITEMS.items():
        if item['category'] == 'hit':
            builder.button(
                text=f"{item['emoji']} {item['name']} — {item['price']}₽",
                callback_data=f"shopbuy_{key}"
            )
    builder.button(text="◀️ НАЗАД", callback_data="mode_shop")
    builder.adjust(1)
    
    await call.message.edit_text(
        f"{SHOP_BRAND}\n\n🔥 <b>ХИТЫ ПРОДАЖ:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("shopcity_"))
async def show_categories(call: CallbackQuery):
    city = call.data.split("_")[1]
    
    builder = InlineKeyboardBuilder()
    for cat_key, cat_name in SHOP_CATEGORIES.items():
        if cat_key != 'hit':
            builder.button(text=cat_name, callback_data=f"shopcat_{city}_{cat_key}")
    builder.button(text="◀️ НАЗАД", callback_data="shop_catalog")
    builder.adjust(1)
    
    await call.message.edit_text(
        f"{SHOP_BRAND}\n🏙 {city}\n\n🧪 <b>ВЫБЕРИ ФОРМУЛУ:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("shopcat_"))
async def show_items(call: CallbackQuery):
    parts = call.data.split("_")
    city = parts[1]
    category = parts[2]
    
    cat_name = SHOP_CATEGORIES.get(category, category)
    
    builder = InlineKeyboardBuilder()
    has_items = False
    for key, item in SHOP_ITEMS.items():
        if item['city'] == city and item['category'] == category:
            has_items = True
            builder.button(
                text=f"{item['emoji']} {item['name']} — {item['price']}₽",
                callback_data=f"shopbuy_{key}"
            )
    
    if not has_items:
        await call.answer("Нет товаров в этом кластере", show_alert=True)
        return
    
    builder.button(text="◀️ НАЗАД", callback_data=f"shopcity_{city}")
    builder.adjust(1)
    
    await call.message.edit_text(
        f"{SHOP_BRAND}\n🏙 {city}\n🧪 {cat_name}\n\n📊 <b>ДОСТУПНЫЕ ПРОДУКТЫ:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("shopbuy_"))
async def select_district(call: CallbackQuery):
    item_key = call.data.split("_")[1]
    item = SHOP_ITEMS.get(item_key)
    
    if not item:
        await call.answer("Продукт не найден")
        return
    
    districts = SHOP_DISTRICTS.get(item['city'], ["Центр"])
    
    builder = InlineKeyboardBuilder()
    for district in districts:
        builder.button(text=district, callback_data=f"shopaddr_{item_key}_{district}")
    builder.button(text="◀️ НАЗАД", callback_data=f"shopcity_{item['city']}")
    builder.adjust(1)
    
    await call.message.edit_text(
        f"{SHOP_BRAND}\n\n"
        f"{item['emoji']} <b>{item['name']}</b>\n"
        f"💰 {item['price']}₽\n"
        f"📝 {item['desc']}\n\n"
        f"📍 <b>ВЫБЕРИ КЛАСТЕР ДОСТАВКИ:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("shopaddr_"))
async def confirm_order(call: CallbackQuery):
    parts = call.data.split("_")
    item_key = parts[1]
    district = parts[2]
    item = SHOP_ITEMS.get(item_key)
    
    if not item:
        await call.answer("Ошибка")
        return
    
    order_id = ShopModel.create_order(
        call.from_user.id, item_key, item['price'],
        item['city'], district
    )
    
    for admin_id in ADMIN_IDS:
        try:
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ ВЫПОЛНИТЬ", callback_data=f"shopdone_{order_id}")
            
            await call.bot.send_message(
                admin_id,
                f"🧪 <b>НОВЫЙ ЗАКАЗ #{order_id}</b>\n\n"
                f"🛒 {item['name']}\n"
                f"💰 {item['price']}₽\n"
                f"📍 {district}\n"
                f"👤 User: <code>{call.from_user.id}</code>",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        except:
            pass
    
    await call.message.edit_text(
        f"✅ <b>ЗАКАЗ #{order_id} СОЗДАН!</b>\n\n"
        f"🧪 {item['name']}\n"
        f"💰 Сумма: {item['price']} ₽\n"
        f"📍 Кластер: {district}\n\n"
        f"💳 <b>ОПЛАТА:</b>\n"
        f"<code>{CARD_NUMBER}</code>\n"
        f"🏦 {BANK_NAME}\n\n"
        f"⚠️ После оплаты лаборант отправит координаты.\n"
        f"📋 Статус заказа: кнопка «МОИ ЗАКАЗЫ»",
        reply_markup=InlineKeyboardBuilder().button(
            text="📋 МОИ ЗАКАЗЫ", callback_data="shop_orders"
        ).as_markup(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "shop_orders")
async def show_orders(call: CallbackQuery):
    orders = ShopModel.get_user_orders(call.from_user.id)
    
    if not orders:
        text = "🧪 У вас пока нет заказов.\n\nЗакажите в КАТАЛОГЕ!"
    else:
        text = f"🧪 <b>ВАШИ ЗАКАЗЫ:</b>\n\n"
        for o in orders:
            item = SHOP_ITEMS.get(o['item_key'], {})
            status = "✅ ВЫПОЛНЕН" if o['status'] == 'completed' else "⏳ ОЖИДАЕТ"
            addr = f"\n📍 {o.get('address', '')}" if o.get('address') else ""
            text += f"{'✅' if o['status']=='completed' else '⏳'} <b>#{o['order_id']}</b>\n"
            text += f"🧪 {item.get('name','?')}\n"
            text += f"💰 {o['amount']}₽ | {status}{addr}\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🧪 КАТАЛОГ", callback_data="shop_catalog")
    builder.button(text="◀️ НАЗАД", callback_data="mode_shop")
    builder.adjust(1)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()
