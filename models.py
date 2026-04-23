import sqlite3
import json
import uuid
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from config import DB_PATH

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cls._instance.conn.row_factory = sqlite3.Row
            cls._instance.cursor = cls._instance.conn.cursor()
        return cls._instance
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor
        except Exception as e:
            self.conn.rollback()
            raise
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict]:
        self.cursor.execute(query, params)
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def fetchall(self, query: str, params: tuple = ()) -> List[Dict]:
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def insert(self, table: str, data: Dict) -> int:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.execute(query, tuple(data.values()))
        return self.cursor.lastrowid
    
    def update(self, table: str, data: Dict, where: str, params: tuple) -> int:
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        self.execute(query, tuple(data.values()) + params)
        return self.cursor.rowcount
    
    def delete(self, table: str, where: str, params: tuple) -> int:
        query = f"DELETE FROM {table} WHERE {where}"
        self.execute(query, params)
        return self.cursor.rowcount

db = Database()

def init_database():
    tables = [
        '''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language TEXT DEFAULT 'ru',
            paid INTEGER DEFAULT 0,
            trial_until TEXT,
            subscription_until TEXT,
            api_keys TEXT DEFAULT '[]',
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            referral_bonus INTEGER DEFAULT 0,
            joined_date TEXT,
            last_activity TEXT,
            requests_today INTEGER DEFAULT 0,
            total_requests INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            ban_reason TEXT,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            achievements TEXT DEFAULT '[]',
            sim_paid INTEGER DEFAULT 0,
            sim_subscription_until TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            currency TEXT DEFAULT 'RUB',
            payment_method TEXT,
            payment_type TEXT DEFAULT 'ai_access',
            transaction_hash TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            confirmed_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            status TEXT DEFAULT 'open',
            created_at TEXT,
            closed_at TEXT,
            assigned_to INTEGER
        )''',
        
        '''CREATE TABLE IF NOT EXISTS ticket_messages (
            msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            sender_type TEXT,
            sender_id INTEGER,
            message TEXT,
            attachments TEXT DEFAULT '[]',
            timestamp TEXT,
            is_read INTEGER DEFAULT 0
        )''',
        
        '''CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            banned_by INTEGER,
            banned_at TEXT,
            unbanned_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            status TEXT DEFAULT 'pending',
            bonus_paid INTEGER DEFAULT 0,
            created_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS sim_orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            operator TEXT,
            region TEXT,
            tariff TEXT,
            status TEXT DEFAULT 'pending',
            sim_number TEXT,
            created_at TEXT,
            completed_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS sim_numbers (
            number_id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            operator TEXT,
            region TEXT,
            tariff TEXT,
            icc TEXT,
            status TEXT DEFAULT 'available',
            added_at TEXT,
            sold_to INTEGER
        )''',
        
        '''CREATE TABLE IF NOT EXISTS scheduler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            message TEXT,
            target TEXT,
            send_at TEXT,
            status TEXT DEFAULT 'pending',
            sent_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            created_at TEXT,
            completed_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS promo_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            promo_code TEXT,
            discount INTEGER,
            used_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS broadcasts (
            broadcast_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            message TEXT,
            target TEXT,
            sent_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            created_at TEXT,
            completed_at TEXT
        )'''
    ]
    
    for table in tables:
        db.execute(table)
    
    # Добавляем недостающие колонки в старых БД
    try:
        db.execute('ALTER TABLE users ADD COLUMN sim_paid INTEGER DEFAULT 0')
    except:
        pass
    
    try:
        db.execute('ALTER TABLE users ADD COLUMN sim_subscription_until TEXT')
    except:
        pass
    
    try:
        db.execute('ALTER TABLE payments ADD COLUMN payment_type TEXT DEFAULT "ai_access"')
    except:
        pass
    
    # Индексы
    try:
        db.execute('CREATE INDEX IF NOT EXISTS idx_users_referral ON users(referral_code)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_sim_orders_user ON sim_orders(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_sim_numbers_status ON sim_numbers(status)')
    except:
        pass

def get_db():
    return db


# ============== USER MODEL ==============
class UserModel:
    @staticmethod
    def create(user_id: int, username: str, first_name: str, last_name: str) -> Dict:
        referral_code = f"ref_{user_id}_{uuid.uuid4().hex[:8]}"
        data = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'joined_date': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'referral_code': referral_code,
            'api_keys': '[]',
            'achievements': '[]'
        }
        db.insert('users', data)
        return data
    
    @staticmethod
    def get(user_id: int) -> Optional[Dict]:
        return db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
    
    @staticmethod
    def get_by_referral(code: str) -> Optional[Dict]:
        return db.fetchone("SELECT * FROM users WHERE referral_code = ?", (code,))
    
    @staticmethod
    def update(user_id: int, data: Dict) -> bool:
        db.update('users', data, 'user_id = ?', (user_id,))
        return True
    
    @staticmethod
    def set_ai_paid(user_id: int, days: int = 30) -> bool:
        subscription_until = (datetime.now() + timedelta(days=days)).isoformat()
        api_keys = json.dumps([f"sk-pro-{uuid.uuid4().hex[:24]}"])
        data = {
            'paid': 1,
            'subscription_until': subscription_until,
            'api_keys': api_keys
        }
        db.update('users', data, 'user_id = ?', (user_id,))
        
        user = UserModel.get(user_id)
        if user and user.get('referred_by'):
            ReferralModel.mark_paid(user['referred_by'], user_id)
        
        UserModel.add_achievement(user_id, 'first_payment')
        return True
    
    @staticmethod
    def set_sim_paid(user_id: int, days: int = 30) -> bool:
        subscription_until = (datetime.now() + timedelta(days=days)).isoformat()
        data = {
            'sim_paid': 1,
            'sim_subscription_until': subscription_until
        }
        db.update('users', data, 'user_id = ?', (user_id,))
        return True
    
    @staticmethod
    def activate_trial(user_id: int) -> bool:
        trial_until = (datetime.now() + timedelta(days=3)).isoformat()
        data = {'trial_until': trial_until}
        db.update('users', data, 'user_id = ?', (user_id,))
        return True
    
    @staticmethod
    def is_ai_premium(user_id: int) -> bool:
        user = UserModel.get(user_id)
        if not user:
            return False
        
        if user['paid'] == 1:
            if user['subscription_until']:
                sub_date = datetime.fromisoformat(user['subscription_until'])
                if sub_date > datetime.now():
                    return True
        
        if user['trial_until']:
            trial_date = datetime.fromisoformat(user['trial_until'])
            if trial_date > datetime.now():
                return True
        
        return False
    
    @staticmethod
    def is_sim_premium(user_id: int) -> bool:
        user = UserModel.get(user_id)
        if not user:
            return False
        
        if user['sim_paid'] == 1:
            if user['sim_subscription_until']:
                sub_date = datetime.fromisoformat(user['sim_subscription_until'])
                if sub_date > datetime.now():
                    return True
        
        return False
    
    @staticmethod
    def increment_requests(user_id: int) -> None:
        db.execute('''
            UPDATE users 
            SET requests_today = requests_today + 1,
                total_requests = total_requests + 1,
                last_activity = ?
            WHERE user_id = ?
        ''', (datetime.now().isoformat(), user_id))
        
        user = UserModel.get(user_id)
        if user and user['total_requests'] >= 100:
            UserModel.add_achievement(user_id, 'hundred_requests')
    
    @staticmethod
    def add_achievement(user_id: int, achievement_key: str) -> bool:
        user = UserModel.get(user_id)
        if not user:
            return False
        
        achievements = json.loads(user.get('achievements', '[]'))
        if achievement_key not in achievements:
            achievements.append(achievement_key)
            db.update('users', {'achievements': json.dumps(achievements)}, 'user_id = ?', (user_id,))
            return True
        return False
    
    @staticmethod
    def get_all(limit: int = 100, offset: int = 0) -> List[Dict]:
        return db.fetchall(
            "SELECT * FROM users ORDER BY joined_date DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
    
    @staticmethod
    def search(query: str) -> List[Dict]:
        q = f"%{query}%"
        return db.fetchall(
            "SELECT * FROM users WHERE username LIKE ? OR first_name LIKE ? OR user_id LIKE ?",
            (q, q, q)
        )
    
    @staticmethod
    def count_all() -> int:
        result = db.fetchone("SELECT COUNT(*) as count FROM users")
        return result['count'] if result else 0
    
    @staticmethod
    def count_paid() -> int:
        result = db.fetchone("SELECT COUNT(*) as count FROM users WHERE paid = 1")
        return result['count'] if result else 0
    
    @staticmethod
    def get_top_users(limit: int = 10) -> List[Dict]:
        return db.fetchall('''
            SELECT user_id, username, first_name, total_requests, referral_bonus,
                   (total_requests + referral_bonus * 10) as score
            FROM users
            WHERE is_banned = 0
            ORDER BY score DESC
            LIMIT ?
        ''', (limit,))
    
    @staticmethod
    def check_subscription_ending() -> List[Dict]:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        return db.fetchall('''
            SELECT * FROM users 
            WHERE paid = 1 
            AND subscription_until LIKE ?
        ''', (f"{tomorrow}%",))


# ============== PAYMENT MODEL ==============
class PaymentModel:
    @staticmethod
    def create(user_id: int, amount: int, method: str, payment_type: str = 'ai_access', currency: str = 'RUB') -> int:
        data = {
            'user_id': user_id,
            'amount': amount,
            'currency': currency,
            'payment_method': method,
            'payment_type': payment_type,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        return db.insert('payments', data)
    
    @staticmethod
    def confirm(payment_id: int, tx_hash: str = '') -> bool:
        data = {
            'status': 'confirmed',
            'transaction_hash': tx_hash,
            'confirmed_at': datetime.now().isoformat()
        }
        db.update('payments', data, 'payment_id = ?', (payment_id,))
        
        payment = PaymentModel.get(payment_id)
        if payment:
            if payment['payment_type'] == 'sim_dl':
                UserModel.set_sim_paid(payment['user_id'])
            else:
                UserModel.set_ai_paid(payment['user_id'])
        
        return True
    
    @staticmethod
    def get(payment_id: int) -> Optional[Dict]:
        return db.fetchone("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
    
    @staticmethod
    def get_by_user(user_id: int) -> List[Dict]:
        return db.fetchall(
            "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
    
    @staticmethod
    def get_all(limit: int = 50) -> List[Dict]:
        return db.fetchall(
            "SELECT * FROM payments ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
    
    @staticmethod
    def get_total_revenue() -> int:
        result = db.fetchone(
            "SELECT SUM(amount) as total FROM payments WHERE status = 'confirmed'"
        )
        return result['total'] or 0 if result else 0


# ============== TICKET MODEL ==============
class TicketModel:
    @staticmethod
    def create(user_id: int) -> int:
        data = {
            'user_id': user_id,
            'status': 'open',
            'created_at': datetime.now().isoformat()
        }
        return db.insert('tickets', data)
    
    @staticmethod
    def get(ticket_id: int) -> Optional[Dict]:
        return db.fetchone("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    
    @staticmethod
    def get_open_by_user(user_id: int) -> Optional[Dict]:
        return db.fetchone(
            "SELECT * FROM tickets WHERE user_id = ? AND status = 'open'",
            (user_id,)
        )
    
    @staticmethod
    def get_all_open() -> List[Dict]:
        return db.fetchall("SELECT * FROM tickets WHERE status = 'open' ORDER BY created_at")
    
    @staticmethod
    def close(ticket_id: int) -> bool:
        data = {'status': 'closed', 'closed_at': datetime.now().isoformat()}
        db.update('tickets', data, 'ticket_id = ?', (ticket_id,))
        return True


class TicketMessageModel:
    @staticmethod
    def add(ticket_id: int, sender_type: str, sender_id: int, message: str) -> int:
        data = {
            'ticket_id': ticket_id,
            'sender_type': sender_type,
            'sender_id': sender_id,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        return db.insert('ticket_messages', data)
    
    @staticmethod
    def get_by_ticket(ticket_id: int) -> List[Dict]:
        return db.fetchall(
            "SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY timestamp",
            (ticket_id,)
        )


# ============== BAN MODEL ==============
class BanModel:
    @staticmethod
    def add(user_id: int, reason: str, banned_by: int) -> bool:
        data = {
            'user_id': user_id,
            'reason': reason,
            'banned_by': banned_by,
            'banned_at': datetime.now().isoformat()
        }
        db.insert('banned_users', data)
        UserModel.update(user_id, {'is_banned': 1, 'ban_reason': reason})
        return True
    
    @staticmethod
    def remove(user_id: int) -> bool:
        db.delete('banned_users', 'user_id = ?', (user_id,))
        UserModel.update(user_id, {'is_banned': 0, 'ban_reason': None})
        return True
    
    @staticmethod
    def is_banned(user_id: int) -> bool:
        result = db.fetchone("SELECT * FROM banned_users WHERE user_id = ?", (user_id,))
        return result is not None


# ============== REFERRAL MODEL ==============
class ReferralModel:
    @staticmethod
    def add(referrer_id: int, referred_id: int) -> bool:
        existing = db.fetchone("SELECT * FROM referrals WHERE referred_id = ?", (referred_id,))
        if existing:
            return False
        
        data = {
            'referrer_id': referrer_id,
            'referred_id': referred_id,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        db.insert('referrals', data)
        return True
    
    @staticmethod
    def mark_paid(referrer_id: int, referred_id: int) -> bool:
        db.execute('''
            UPDATE referrals 
            SET status = 'paid', bonus_paid = 1
            WHERE referrer_id = ? AND referred_id = ?
        ''', (referrer_id, referred_id))
        
        db.execute('UPDATE users SET referral_bonus = referral_bonus + 1 WHERE user_id = ?', (referrer_id,))
        
        user = UserModel.get(referrer_id)
        if user:
            if user['referral_bonus'] >= 10:
                UserModel.add_achievement(referrer_id, 'ten_friends')
            elif user['referral_bonus'] >= 5:
                UserModel.add_achievement(referrer_id, 'five_friends')
        
        return True
    
    @staticmethod
    def get_stats(user_id: int) -> Dict:
        total = db.fetchone("SELECT COUNT(*) as count FROM referrals WHERE referrer_id = ?", (user_id,))
        paid = db.fetchone("SELECT COUNT(*) as count FROM referrals WHERE referrer_id = ? AND status = 'paid'", (user_id,))
        return {
            'total': total['count'] if total else 0,
            'paid': paid['count'] if paid else 0
        }


# ============== PROMO MODEL ==============
class PromoModel:
    @staticmethod
    def check(code: str) -> Optional[Dict]:
        from config import PROMO_CODES
        promo = PROMO_CODES.get(code.upper())
        if promo:
            if promo["uses"] > 0:
                return promo
            elif promo["uses"] == 0:
                return promo
        return None
    
    @staticmethod
    def use(user_id: int, code: str, discount: int) -> bool:
        db.insert('promo_usage', {
            'user_id': user_id,
            'promo_code': code.upper(),
            'discount': discount,
            'used_at': datetime.now().isoformat()
        })
        return True
    
    @staticmethod
    def is_used(user_id: int, code: str) -> bool:
        result = db.fetchone(
            "SELECT * FROM promo_usage WHERE user_id = ? AND promo_code = ?",
            (user_id, code.upper())
        )
        return result is not None


# ============== SIM MODEL ==============
class SimModel:
    @staticmethod
    def get_available(operator: str = None, region: str = None) -> List[Dict]:
        query = "SELECT * FROM sim_numbers WHERE status = 'available'"
        params = []
        if operator:
            query += " AND operator = ?"
            params.append(operator)
        if region:
            query += " AND region = ?"
            params.append(region)
        query += " LIMIT 20"
        return db.fetchall(query, tuple(params))
    
    @staticmethod
    def create_order(user_id: int, operator: str, region: str, tariff: str) -> int:
        data = {
            'user_id': user_id,
            'operator': operator,
            'region': region,
            'tariff': tariff,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        return db.insert('sim_orders', data)
    
    @staticmethod
    def get_order(order_id: int) -> Optional[Dict]:
        return db.fetchone("SELECT * FROM sim_orders WHERE order_id = ?", (order_id,))
    
    @staticmethod
    def get_user_orders(user_id: int) -> List[Dict]:
        return db.fetchall(
            "SELECT * FROM sim_orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
    
    @staticmethod
    def complete_order(order_id: int, sim_number: str) -> bool:
        data = {
            'status': 'completed',
            'sim_number': sim_number,
            'completed_at': datetime.now().isoformat()
        }
        db.update('sim_orders', data, 'order_id = ?', (order_id,))
        
        # Отмечаем номер как проданный
        order = SimModel.get_order(order_id)
        if order:
            db.update('sim_numbers', 
                     {'status': 'sold', 'sold_to': order['user_id']},
                     'phone = ?', (sim_number,))
        
        return True
    
    @staticmethod
    def get_orders(status: str = 'pending') -> List[Dict]:
        return db.fetchall(
            "SELECT * FROM sim_orders WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
    
    @staticmethod
    def add_number(phone: str, operator: str, region: str, tariff: str, icc: str = "") -> int:
        data = {
            'phone': phone,
            'operator': operator,
            'region': region,
            'tariff': tariff,
            'icc': icc,
            'status': 'available',
            'added_at': datetime.now().isoformat()
        }
        return db.insert('sim_numbers', data)


# ============== SETTINGS MODEL ==============
class SettingsModel:
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        result = db.fetchone("SELECT value FROM settings WHERE key = ?", (key,))
        return result['value'] if result else default
    
    @staticmethod
    def set(key: str, value: Any) -> bool:
        data = {'value': str(value), 'updated_at': datetime.now().isoformat()}
        existing = db.fetchone("SELECT * FROM settings WHERE key = ?", (key,))
        if existing:
            db.update('settings', data, 'key = ?', (key,))
        else:
            data['key'] = key
            db.insert('settings', data)
        return True