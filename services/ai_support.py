import aiohttp
import json


class AISupport:
    """Автоответчик на базе DeepSeek API + FAQ"""
    
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    API_KEY = "sk-370b8b5bb0044c25b7e87a4b38f0c3a8"
    
    FAQ_ANSWERS = {
        "price": "💰 Стоимость:\n• AI Access — 49 ₽\n• SIM.DL — 299 ₽\nНажмите «Получить доступ» для оплаты.",
        "trial": "🆓 Триал на 3 дня бесллатно!\nКнопка «Триал» в меню или /trial",
        "key": "🔑 После оплаты: кнопка «Мой ключ» или /key",
        "pay": "💳 Оплата: карта СБП, CryptoBot, Telegram Stars\nНажмите «Получить доступ»",
        "sim": "📱 SIM.DL — активация сим-карт через доверенное лицо.\n1. Оплатите доступ (299₽)\n2. Выберите оператора/регион/тариф\n3. Получите номер",
        "block": "🚫 Бан? Создайте тикет /support",
        "hello": "👋 Привет! Выберите режим:\n• 🤖 AI Access — нейросети\n• 📱 SIM.DL — активация сим",
        "help": "📚 Команды: /start /profile /key /trial /referral /support",
        "ref": "👥 Рефералы: приглашайте друзей — получайте бонусы!\n/referral",
    }
    
    @classmethod
    def get_faq_answer(cls, question: str) -> str:
        """Поиск по ключевым словам"""
        question = question.lower()
        
        keywords_map = {
            "price": ["цена", "стоит", "сколько", "сумма", "оплат", "стоимость", "рубл"],
            "trial": ["триал", "пробный", "беслатно", "тест", "проб"],
            "key": ["ключ", "api", "токен", "получить доступ"],
            "pay": ["оплат", "плат", "карт", "crypto", "звёзд", "star", "перевод"],
            "sim": ["сим", "активац", "номер", "билайн", "мтс", "мегафон", "tele2", "симк"],
            "block": ["бан", "блок", "забан", "разбан", "заблок"],
            "hello": ["привет", "здрав", "добр", "hello", "hi", "ку"],
            "help": ["помощ", "команд", "что дела", "как"],
            "ref": ["реферал", "друг", "приглас", "бонус"],
        }
        
        for key, words in keywords_map.items():
            for word in words:
                if word in question:
                    return cls.FAQ_ANSWERS[key]
        
        return None
    
    @classmethod
    async def get_deepseek_response(cls, question: str) -> str:
        """Получить ответ от DeepSeek API"""
        try:
            headers = {
                "Authorization": f"Bearer {cls.API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ты агент поддержки бота AI Access + SIM.DL. "
                            "Бот продаёт доступ к ChatGPT/Claude/Midjourney за 49₽ и "
                            "активацию сим-карт через доверенное лицо за 299₽. "
                            "Отвечай кратко (1-3 предложения), на русском языке, дружелюбно. "
                            "Если вопрос сложный или требует действий администратора — "
                            "предложи создать тикет командой /support"
                        )
                    },
                    {"role": "user", "content": question}
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(cls.API_URL, headers=headers, json=data) as response:
                    result = await response.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    else:
                        print(f"DeepSeek API error: {result}")
            
        except Exception as e:
            print(f"DeepSeek exception: {e}")
        
        return None
    
    @classmethod
    async def get_smart_response(cls, question: str) -> str:
        """Умный ответ"""
        # 1. Проверяем FAQ
        faq = cls.get_faq_answer(question)
        if faq:
            return "🤖 <b>Автоответчик:</b>\n\n" + faq
        
        # 2. Пробуем DeepSeek
        ai_answer = await cls.get_deepseek_response(question)
        if ai_answer:
            return "🤖 <b>AI ответ:</b>\n\n" + ai_answer
        
        # 3. Запасной ответ
        q = question.lower()
        
        if any(w in q for w in ["как", "где", "куда", "что"]):
            if "доступ" in q or "подписк" in q:
                return "🤖 <b>Автоответчик:</b>\n\n🔐 Для доступа:\n1. Нажмите «Получить доступ»\n2. Оплатите\n3. Получите ключ /key"
            if "заказ" in q or "order" in q:
                return "🤖 <b>Автоответчик:</b>\n\n📱 Для заказа SIM:\n1. Оплатите SIM.DL\n2. Нажмите «Заказать SIM»\n3. Выберите параметры"
        
        if "долго" in q or "ждать" in q:
            return "🤖 <b>Автоответчик:</b>\n\n⏳ Обработка до 15 минут. Если дольше — /support"
        
        if "не работает" in q or "ошибка" in q:
            return "🤖 <b>Автоответчик:</b>\n\n❌ Опишите проблему подробнее в тикете: /support"
        
        # 4. Предлагаем тикет
        return (
            "🤖 <b>Автоответчик:</b>\n\n"
            "🤔 Я не смог найти автоматический ответ на ваш вопрос.\n\n"
            "📝 <b>Создайте тикет</b> — оператор ответит лично.\n"
            "Используйте команду /support"
        )
    
    @classmethod
    async def get_answer(cls, question: str) -> str:
        """Основной метод"""
        return await cls.get_smart_response(question)