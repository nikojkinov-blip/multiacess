import aiohttp
from typing import Optional, Dict
from config import CRYPTO_BOT_TOKEN


class CryptoBotPayment:
    API_URL = "https://pay.crypt.bot/api"
    
    @classmethod
    async def create_invoice(cls, amount_rub: float, currency: str = "USDT") -> Optional[Dict]:
        """Создать счёт в CryptoBot"""
        headers = {
            "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
            "Content-Type": "application/json"
        }
        
        rates = {
            "TON": 150,
            "USDT": 90,
            "BTC": 6000000
        }
        
        crypto_amount = amount_rub / rates.get(currency, 90)
        if currency == "USDT":
            crypto_amount = round(crypto_amount, 2)
        elif currency == "TON":
            crypto_amount = round(crypto_amount, 4)
        else:
            crypto_amount = round(crypto_amount, 8)
        
        data = {
            "asset": currency,
            "amount": str(crypto_amount),
            "description": "AI Access Bot - Premium доступ",
            "payload": "premium_access",
            "allow_comments": False,
            "allow_anonymous": False,
            "expires_in": 3600
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{cls.API_URL}/createInvoice",
                    headers=headers,
                    json=data
                ) as response:
                    result = await response.json()
                    
                    if result.get("ok"):
                        invoice = result["result"]
                        return {
                            "invoice_id": invoice["invoice_id"],
                            "pay_url": invoice["pay_url"],
                            "amount": invoice["amount"],
                            "asset": invoice["asset"],
                            "status": invoice["status"],
                            "rub_amount": amount_rub
                        }
                    else:
                        print(f"CryptoBot error: {result}")
                        return None
        except Exception as e:
            print(f"CryptoBot exception: {e}")
            return None
    
    @classmethod
    async def check_invoice(cls, invoice_id: int) -> Optional[str]:
        """Проверить статус счёта"""
        headers = {
            "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
            "Content-Type": "application/json"
        }
        
        data = {"invoice_ids": [invoice_id]}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{cls.API_URL}/getInvoices",
                    headers=headers,
                    json=data
                ) as response:
                    result = await response.json()
                    
                    if result.get("ok") and result["result"]["items"]:
                        invoice = result["result"]["items"][0]
                        return invoice["status"]
        except Exception as e:
            print(f"Check invoice error: {e}")
        
        return None
    
    @classmethod
    async def get_balance(cls) -> Optional[Dict]:
        """Получить баланс кошелька"""
        headers = {
            "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{cls.API_URL}/getBalance",
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if result.get("ok"):
                        return result["result"]
        except Exception as e:
            print(f"Get balance error: {e}")
        
        return None
    
    @classmethod
    async def get_exchange_rates(cls) -> Optional[Dict]:
        """Получить курсы валют"""
        headers = {
            "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{cls.API_URL}/getExchangeRates",
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if result.get("ok"):
                        return result["result"]
        except Exception as e:
            print(f"Get rates error: {e}")
        
        return None