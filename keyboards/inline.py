from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, WebAppInfo


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню AI Access"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔐 Получить доступ AI", callback_data="get_access")
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.button(text="🔑 Мой ключ", callback_data="my_key")
    builder.button(text="🆓 Триал AI", callback_data="trial")
    builder.button(text="👥 Рефералы", callback_data="referral_menu")
    builder.button(text="🏆 Рейтинг", callback_data="rating")
    builder.button(text="🎫 Промокод", callback_data="promo_code")
    builder.button(text="📱 Открыть WebApp", web_app=WebAppInfo(url="https://nikojkinov-blip.github.io/multiacess/"))
    builder.button(text="◀️ Сменить режим", callback_data="main_menu")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def get_sim_keyboard() -> InlineKeyboardMarkup:
    """Меню SIM.DL"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Заказать SIM", callback_data="sim_order")
    builder.button(text="📋 Мои заказы", callback_data="sim_orders")
    builder.button(text="💰 Оплатить доступ SIM", callback_data="pay_sim")
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.button(text="📞 Поддержка", callback_data="support")
    builder.button(text="📱 Открыть WebApp", web_app=WebAppInfo(url="https://nikojkinov-blip.github.io/multiacess/"))
    builder.button(text="◀️ Сменить режим", callback_data="main_menu")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def get_profile_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура профиля"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 AI ключ", callback_data="my_key")
    builder.button(text="📱 SIM заказы", callback_data="sim_orders")
    builder.button(text="👥 Рефералы", callback_data="referral_menu")
    builder.button(text="🏆 Рейтинг", callback_data="rating")
    builder.button(text="🎫 Промокод", callback_data="promo_code")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админ-панель"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Пользователи", callback_data="admin_users")
    builder.button(text="💰 Платежи", callback_data="admin_payments")
    builder.button(text="📱 SIM заказы", callback_data="admin_sim_orders")
    builder.button(text="📋 Тикеты", callback_data="admin_tickets")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.button(text="⚙️ Настройки", callback_data="admin_settings")
    builder.button(text="◀️ Закрыть", callback_data="close_admin")
    builder.adjust(2, 2, 2, 1, 1)
    return builder.as_markup()


def get_payment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура способов оплаты AI"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Перевод на карту", callback_data="pay_card_ai")
    builder.button(text="₿ CryptoBot", callback_data="pay_crypto_menu_ai")
    builder.button(text="⭐ Telegram Stars", callback_data="pay_stars_ai")
    builder.button(text="🎫 Промокод", callback_data="promo_code")
    builder.button(text="◀️ Назад", callback_data="mode_ai")
    builder.adjust(1)
    return builder.as_markup()


def get_sim_payment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура способов оплаты SIM"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Перевод на карту", callback_data="pay_card_sim")
    builder.button(text="₿ CryptoBot", callback_data="pay_crypto_menu_sim")
    builder.button(text="◀️ Назад", callback_data="mode_sim")
    builder.adjust(1)
    return builder.as_markup()


def get_crypto_menu_keyboard(payment_type: str = 'ai') -> InlineKeyboardMarkup:
    """Меню выбора криптовалюты"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💎 TON", callback_data=f"pay_crypto_{payment_type}_TON")
    builder.button(text="💵 USDT", callback_data=f"pay_crypto_{payment_type}_USDT")
    builder.button(text="₿ BTC", callback_data=f"pay_crypto_{payment_type}_BTC")
    builder.button(text="◀️ Назад", callback_data="get_access" if payment_type == 'ai' else "pay_sim")
    builder.adjust(3, 1)
    return builder.as_markup()


def get_support_keyboard(ticket_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура поддержки"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Создать тикет", callback_data="create_ticket")
    builder.button(text="💬 Задать вопрос боту", callback_data="ask_question")
    builder.button(text="📱 Открыть WebApp", web_app=WebAppInfo(url="https://nikojkinov-blip.github.io/multiacess/"))
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_referral_keyboard(ref_link: str) -> InlineKeyboardMarkup:
    """Клавиатура реферальной программы"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Поделиться ссылкой", switch_inline_query=ref_link)
    builder.button(text="📊 Моя статистика", callback_data="referral_menu")
    builder.button(text="◀️ Назад", callback_data="profile")
    builder.adjust(1)
    return builder.as_markup()


def get_ticket_view_keyboard(ticket_id: int, status: str = 'open') -> InlineKeyboardMarkup:
    """Клавиатура просмотра тикета"""
    builder = InlineKeyboardBuilder()
    if status == 'open':
        builder.button(text="📝 Добавить сообщение", callback_data=f"add_message_{ticket_id}")
        builder.button(text="❌ Закрыть тикет", callback_data=f"close_ticket_{ticket_id}")
    builder.button(text="📝 Создать новый", callback_data="create_ticket")
    builder.button(text="◀️ Назад", callback_data="support")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_question_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после вопроса боту"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Создать тикет", callback_data="create_ticket")
    builder.button(text="💬 Ещё вопрос", callback_data="ask_question")
    builder.button(text="📱 Открыть WebApp", web_app=WebAppInfo(url="https://nikojkinov-blip.github.io/multiacess/"))
    builder.button(text="◀️ В меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены"""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_support")
    return builder.as_markup()


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В главное меню", callback_data="main_menu")
    return builder.as_markup()


def get_broadcast_target_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора аудитории для рассылки"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Всем", callback_data="bc_all")
    builder.button(text="🤖 AI Premium", callback_data="bc_ai_paid")
    builder.button(text="📱 SIM Premium", callback_data="bc_sim_paid")
    builder.button(text="🆓 Без подписки", callback_data="bc_unpaid")
    builder.button(text="❌ Отмена", callback_data="bc_cancel")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_export_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура экспорта данных"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Пользователи CSV", callback_data="export_users")
    builder.button(text="💰 Платежи CSV", callback_data="export_payments")
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    builder.adjust(1)
    return builder.as_markup()


def get_stats_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура статистики"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="admin_stats")
    builder.button(text="📥 Экспорт", callback_data="export_menu")
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    builder.adjust(2, 1)
    return builder.as_markup()