import asyncio
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import UserModel, PaymentModel, db
from config import (
    ADMIN_IDS, CARD_NUMBER, BANK_NAME, 
    AI_PAYMENT_AMOUNT, SIM_PAYMENT_AMOUNT
)
from keyboards.inline import get_main_keyboard, get_sim_keyboard
from services.payment_systems import CryptoBotPayment

router = Router()

# Временное хранилище для отслеживания крипто-платежей
pending_payments = {}


# ============== ВЫБОР РЕЖИМА ОПЛАТЫ ==============
@router.callback_query(F.data == "get_access")
async def show_payment_info(call: CallbackQuery):
    """Оплата AI Access"""
    user = UserModel.get(call.from_user.id)
    
    if UserModel.is_ai_premium(call.from_user.id):
        await call.message.edit_text(
            "✅ У вас уже есть активный AI доступ! Используйте /key для просмотра ключа.",
            reply_markup=get_main_keyboard()
        )
        await call.answer()
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Перевод на карту (СБП)", callback_data="pay_card_ai")
    builder.button(text="₿ CryptoBot (TON, USDT, BTC)", callback_data="pay_crypto_menu_ai")
    builder.button(text="⭐ Telegram Stars", callback_data="pay_stars_ai")
    builder.button(text="🎫 Промокод", callback_data="promo_code")
    builder.button(text="◀️ Назад", callback_data="mode_ai")
    builder.adjust(1)
    
    text = f"""
🤖 <b>AI Access — Верификация</b>

💰 Сумма: <b>{AI_PAYMENT_AMOUNT} ₽</b>

Выберите способ оплаты:
"""
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "pay_sim")
async def show_sim_payment(call: CallbackQuery):
    """Оплата SIM.DL"""
    if UserModel.is_sim_premium(call.from_user.id):
        await call.answer("✅ У вас уже есть доступ к SIM.DL!", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Перевод на карту (СБП)", callback_data="pay_card_sim")
    builder.button(text="₿ CryptoBot (TON, USDT, BTC)", callback_data="pay_crypto_menu_sim")
    builder.button(text="◀️ Назад", callback_data="mode_sim")
    builder.adjust(1)
    
    text = f"""
📱 <b>SIM.DL — Доступ к базе</b>

💰 Сумма: <b>{SIM_PAYMENT_AMOUNT} ₽</b>

Что вы получаете:
• Доступ к номерам для активации
• Оформление доверенного лица
• Все операторы связи

Выберите способ оплаты:
"""
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


# ============== ОПЛАТА КАРТОЙ ==============
@router.callback_query(F.data == "pay_card_ai")
async def show_card_info_ai(call: CallbackQuery):
    text = f"""
💳 <b>Оплата AI Access — Перевод на карту</b>

💰 Сумма: <b>{AI_PAYMENT_AMOUNT} ₽</b>
💳 Карта: <code>{CARD_NUMBER}</code>
🏦 Банк: {BANK_NAME}

📌 <b>Инструкция:</b>
1. Переведите {AI_PAYMENT_AMOUNT} ₽ по номеру карты
2. Нажмите <b>«✅ Я оплатил»</b>
3. Ожидайте подтверждения (до 15 минут)

⚠️ В комментарии к платежу: <code>AI{call.from_user.id}</code>
"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Я оплатил", callback_data="i_paid_card_ai")
    builder.button(text="◀️ Назад", callback_data="get_access")
    builder.adjust(1)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "pay_card_sim")
async def show_card_info_sim(call: CallbackQuery):
    text = f"""
💳 <b>Оплата SIM.DL — Перевод на карту</b>

💰 Сумма: <b>{SIM_PAYMENT_AMOUNT} ₽</b>
💳 Карта: <code>{CARD_NUMBER}</code>
🏦 Банк: {BANK_NAME}

📌 <b>Инструкция:</b>
1. Переведите {SIM_PAYMENT_AMOUNT} ₽ по номеру карты
2. Нажмите <b>«✅ Я оплатил»</b>
3. Ожидайте подтверждения (до 15 минут)

⚠️ В комментарии к платежу: <code>SIM{call.from_user.id}</code>
"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Я оплатил", callback_data="i_paid_card_sim")
    builder.button(text="◀️ Назад", callback_data="pay_sim")
    builder.adjust(1)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


# ============== ОТМЕТКА ОБ ОПЛАТЕ КАРТОЙ ==============
@router.callback_query(F.data == "i_paid_card_ai")
async def mark_card_paid_ai(call: CallbackQuery):
    payment_id = PaymentModel.create(
        user_id=call.from_user.id,
        amount=AI_PAYMENT_AMOUNT,
        method='card',
        payment_type='ai_access'
    )
    
    for admin_id in ADMIN_IDS:
        try:
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Подтвердить", callback_data=f"confirm_payment_{payment_id}")
            builder.button(text="❌ Отклонить", callback_data=f"reject_payment_{payment_id}")
            
            await call.bot.send_message(
                admin_id,
                f"🔔 <b>Новая заявка AI Access!</b>\n\n"
                f"👤 Пользователь: @{call.from_user.username} (ID: <code>{call.from_user.id}</code>)\n"
                f"🤖 Тип: AI Access\n"
                f"💰 Сумма: {AI_PAYMENT_AMOUNT} ₽\n"
                f"💳 Способ: Карта\n"
                f"🆔 Платёж: #{payment_id}\n\n"
                f"Проверьте поступление и подтвердите.",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Notify admin error: {e}")
    
    await call.message.edit_text(
        "✅ <b>Заявка на оплату отправлена!</b>\n\n"
        "Ожидайте подтверждения администратором (обычно до 15 минут).\n"
        "После подтверждения вы получите уведомление.",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "i_paid_card_sim")
async def mark_card_paid_sim(call: CallbackQuery):
    payment_id = PaymentModel.create(
        user_id=call.from_user.id,
        amount=SIM_PAYMENT_AMOUNT,
        method='card',
        payment_type='sim_dl'
    )
    
    for admin_id in ADMIN_IDS:
        try:
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Подтвердить", callback_data=f"confirm_payment_{payment_id}")
            builder.button(text="❌ Отклонить", callback_data=f"reject_payment_{payment_id}")
            
            await call.bot.send_message(
                admin_id,
                f"🔔 <b>Новая заявка SIM.DL!</b>\n\n"
                f"👤 Пользователь: @{call.from_user.username} (ID: <code>{call.from_user.id}</code>)\n"
                f"📱 Тип: SIM.DL\n"
                f"💰 Сумма: {SIM_PAYMENT_AMOUNT} ₽\n"
                f"💳 Способ: Карта\n"
                f"🆔 Платёж: #{payment_id}\n\n"
                f"Проверьте поступление и подтвердите.",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Notify admin error: {e}")
    
    await call.message.edit_text(
        "✅ <b>Заявка на оплату отправлена!</b>\n\n"
        "Ожидайте подтверждения администратором (обычно до 15 минут).\n"
        "После подтверждения вы получите уведомление и доступ к SIM.DL.",
        reply_markup=get_sim_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


# ============== КРИПТОВАЛЮТА (CryptoBot) ==============
@router.callback_query(F.data == "pay_crypto_menu_ai")
async def show_crypto_menu_ai(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="💎 TON", callback_data="pay_crypto_ai_TON")
    builder.button(text="💵 USDT", callback_data="pay_crypto_ai_USDT")
    builder.button(text="₿ BTC", callback_data="pay_crypto_ai_BTC")
    builder.button(text="◀️ Назад", callback_data="get_access")
    builder.adjust(3, 1)
    
    text = f"""
₿ <b>AI Access — Оплата криптовалютой</b>

💰 Сумма: <b>{AI_PAYMENT_AMOUNT} ₽</b>

Выберите валюту:
"""
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "pay_crypto_menu_sim")
async def show_crypto_menu_sim(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="💎 TON", callback_data="pay_crypto_sim_TON")
    builder.button(text="💵 USDT", callback_data="pay_crypto_sim_USDT")
    builder.button(text="₿ BTC", callback_data="pay_crypto_sim_BTC")
    builder.button(text="◀️ Назад", callback_data="pay_sim")
    builder.adjust(3, 1)
    
    text = f"""
₿ <b>SIM.DL — Оплата криптовалютой</b>

💰 Сумма: <b>{SIM_PAYMENT_AMOUNT} ₽</b>

Выберите валюту:
"""
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("pay_crypto_ai_"))
async def create_crypto_payment_ai(call: CallbackQuery):
    currency = call.data.split("_")[2]
    payment_type = 'ai_access'
    amount = AI_PAYMENT_AMOUNT
    
    await process_crypto_payment(call, currency, payment_type, amount)


@router.callback_query(F.data.startswith("pay_crypto_sim_"))
async def create_crypto_payment_sim(call: CallbackQuery):
    currency = call.data.split("_")[2]
    payment_type = 'sim_dl'
    amount = SIM_PAYMENT_AMOUNT
    
    await process_crypto_payment(call, currency, payment_type, amount)


async def process_crypto_payment(call: CallbackQuery, currency: str, payment_type: str, amount: int):
    """Общая функция для создания крипто-платежа"""
    payment_id = PaymentModel.create(
        user_id=call.from_user.id,
        amount=amount,
        method=f'crypto_{currency}',
        payment_type=payment_type,
        currency=currency
    )
    
    invoice = await CryptoBotPayment.create_invoice(amount, currency)
    
    if invoice:
        pending_payments[invoice["invoice_id"]] = {
            "payment_id": payment_id,
            "user_id": call.from_user.id,
            "payment_type": payment_type
        }
        
        builder = InlineKeyboardBuilder()
        builder.button(text="💸 Перейти к оплате", url=invoice["pay_url"])
        builder.button(text="🔄 Проверить оплату", callback_data=f"check_crypto_{invoice['invoice_id']}")
        builder.button(text="◀️ Назад", callback_data="mode_ai" if payment_type == 'ai_access' else "mode_sim")
        builder.adjust(1)
        
        type_name = "AI Access" if payment_type == 'ai_access' else "SIM.DL"
        
        text = f"""
₿ <b>Счёт создан! ({type_name})</b>

💎 Валюта: {invoice['asset']}
💰 Сумма: {invoice['amount']} {invoice['asset']} (~{amount} ₽)
🆔 ID платежа: {payment_id}

Нажмите <b>«Перейти к оплате»</b> и оплатите счёт.
После оплаты нажмите <b>«Проверить оплату»</b>.
"""
        await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await call.message.edit_text(
            "❌ Ошибка создания счёта. Попробуйте позже или другой способ.",
            reply_markup=get_main_keyboard()
        )
    
    await call.answer()


@router.callback_query(F.data.startswith("check_crypto_"))
async def check_crypto_payment(call: CallbackQuery):
    invoice_id = int(call.data.split("_")[2])
    
    status = await CryptoBotPayment.check_invoice(invoice_id)
    
    if status == "paid":
        payment_info = pending_payments.get(invoice_id)
        if payment_info:
            PaymentModel.confirm(payment_info["payment_id"], str(invoice_id))
            
            type_name = "AI Access" if payment_info["payment_type"] == 'ai_access' else "SIM.DL"
            
            for admin_id in ADMIN_IDS:
                try:
                    await call.bot.send_message(
                        admin_id,
                        f"💰 <b>Новая оплата через CryptoBot!</b>\n"
                        f"📱 Тип: {type_name}\n"
                        f"👤 Пользователь: {payment_info['user_id']}\n"
                        f"🆔 Платёж: #{payment_info['payment_id']}",
                        parse_mode="HTML"
                    )
                except:
                    pass
            
            keyboard = get_main_keyboard() if payment_info["payment_type"] == 'ai_access' else get_sim_keyboard()
            
            await call.message.edit_text(
                f"✅ <b>Оплата подтверждена!</b>\n\n"
                f"{'Используйте /key для получения API-ключа.' if payment_info['payment_type'] == 'ai_access' else 'Доступ к SIM.DL открыт! Создайте заказ.'}",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await call.answer("✅ Оплата подтверждена!")
            
            try:
                await call.bot.send_message(
                    payment_info["user_id"],
                    f"✅ Ваш платёж подтверждён! {'AI доступ активирован. /key' if payment_info['payment_type'] == 'ai_access' else 'SIM.DL доступ открыт!'}"
                )
            except:
                pass
            
            del pending_payments[invoice_id]
        else:
            await call.answer("❌ Платёж не найден", show_alert=True)
    
    elif status == "active":
        await call.answer("⏳ Счёт создан, но ещё не оплачен", show_alert=True)
    
    else:
        await call.answer("❌ Счёт не оплачен или истёк", show_alert=True)


# ============== TELEGRAM STARS ==============
@router.callback_query(F.data == "pay_stars_ai")
async def pay_with_stars_ai(call: CallbackQuery):
    await call.message.answer_invoice(
        title="AI Access Bot - Premium",
        description="Доступ к ChatGPT, Claude, Midjourney на 30 дней",
        payload=f"ai_premium_{call.from_user.id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Premium доступ", amount=AI_PAYMENT_AMOUNT)],
        start_parameter="ai_premium",
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False
    )
    await call.answer("📝 Счёт выставлен!")


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    user_id = message.from_user.id
    payment_info = message.successful_payment
    
    payment_type = 'ai_access'
    if 'sim' in payment_info.invoice_payload:
        payment_type = 'sim_dl'
    
    PaymentModel.create(
        user_id=user_id,
        amount=payment_info.total_amount,
        method='stars',
        payment_type=payment_type
    )
    
    if payment_type == 'sim_dl':
        UserModel.set_sim_paid(user_id)
    else:
        UserModel.set_ai_paid(user_id)
    
    await message.answer(
        f"✅ Оплата получена! {'AI доступ активирован. /key' if payment_type == 'ai_access' else 'SIM.DL доступ открыт!'}",
        reply_markup=get_main_keyboard() if payment_type == 'ai_access' else get_sim_keyboard()
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"💰 Новая оплата Stars!\n"
                f"Пользователь: {user_id}\n"
                f"Тип: {'AI Access' if payment_type == 'ai_access' else 'SIM.DL'}\n"
                f"Сумма: {payment_info.total_amount} {payment_info.currency}"
            )
        except:
            pass


# ============== ПОДТВЕРЖДЕНИЕ/ОТКЛОНЕНИЕ АДМИНОМ ==============
@router.callback_query(F.data.startswith("confirm_payment_"))
async def confirm_payment_admin(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    payment_id = int(call.data.split("_")[2])
    payment = PaymentModel.get(payment_id)
    
    if payment:
        PaymentModel.confirm(payment_id)
        
        type_name = "AI Access" if payment['payment_type'] == 'ai_access' else "SIM.DL"
        msg = f"✅ Ваш платёж подтверждён! {'AI доступ активирован. /key' if payment['payment_type'] == 'ai_access' else 'SIM.DL доступ открыт!'}"
        
        try:
            await call.bot.send_message(payment['user_id'], msg)
        except:
            pass
        
        await call.message.edit_text(
            call.message.text + f"\n\n✅ <b>Подтверждено админом @{call.from_user.username}</b>",
            parse_mode="HTML"
        )
        await call.answer("✅ Подтверждено")
    else:
        await call.answer("❌ Платёж не найден", show_alert=True)


@router.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment_admin(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    payment_id = int(call.data.split("_")[2])
    payment = PaymentModel.get(payment_id)
    
    if payment:
        db.update('payments', {'status': 'rejected'}, 'payment_id = ?', (payment_id,))
        
        try:
            await call.bot.send_message(
                payment['user_id'],
                "❌ Ваш платёж отклонён. Свяжитесь с поддержкой /support"
            )
        except:
            pass
        
        await call.message.edit_text(
            call.message.text + f"\n\n❌ <b>Отклонено админом @{call.from_user.username}</b>",
            parse_mode="HTML"
        )
        await call.answer("❌ Отклонено")