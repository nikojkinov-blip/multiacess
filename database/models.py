import sqlite3
import json
import uuid
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
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            last_name TEXT, language TEXT DEFAULT 'ru', paid INTEGER DEFAULT 0,
            trial_until TEXT, subscription_until TEXT, api_keys TEXT DEFAULT '[]',
            referral_code TEXT UNIQUE, referred_by INTEGER, referral_bonus INTEGER DEFAULT 0,
            joined_date TEXT, last_activity TEXT, requests_today INTEGER DEFAULT 0,
            total_requests INTEGER DEFAULT 0, is_banned INTEGER DEFAULT 0,
            ban_reason TEXT, level INTEGER DEFAULT 1, experience INTEGER DEFAULT 0,
            achievements TEXT DEFAULT '[]', sim_paid INTEGER DEFAULT 0,
            sim_subscription_until TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            amount INTEGER, currency TEXT DEFAULT 'RUB', payment_method TEXT,
            payment_type TEXT DEFAULT 'ai_access', transaction_hash TEXT,
            status TEXT DEFAULT 'pending', created_at TEXT, confirmed_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            status TEXT DEFAULT 'open', created_at TEXT, closed_at TEXT,
            assigned_to INTEGER
        )''',
        
        '''CREATE TABLE IF NOT EXISTS ticket_messages (
            msg_id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id INTEGER,
            sender_type TEXT, sender_id INTEGER, message TEXT,
            attachments TEXT DEFAULT '[]', timestamp TEXT, is_read INTEGER DEFAULT 0
        )''',
        
        '''CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY, reason TEXT, banned_by INTEGER,
            banned_at TEXT, unbanned_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER,
            referred_id INTEGER, status TEXT DEFAULT 'pending',
            bonus_paid INTEGER DEFAULT 0, created_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS sim_orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            operator TEXT, region TEXT, tariff TEXT, status TEXT DEFAULT 'pending',
            sim_number TEXT, created_at TEXT, completed_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS sim_numbers (
            number_id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT,
            operator TEXT, region TEXT, tariff TEXT, icc TEXT,
            status TEXT DEFAULT 'available', added_at TEXT, sold_to INTEGER
        )''',
        
        '''CREATE TABLE IF NOT EXISTS cash_orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            item_key TEXT, amount INTEGER, status TEXT DEFAULT 'pending',
            created_at TEXT, completed_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS fragment_orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, item_key TEXT, amount INTEGER,
            phone TEXT, status TEXT DEFAULT 'pending',
            created_at TEXT, completed_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS promo_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            promo_code TEXT, discount INTEGER, used_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT, updated_at TEXT
        )'''
    ]
    
    for table in tables:
        db.execute(table)
    
    try:
        db.execute('CREATE INDEX IF NOT EXISTS idx_users_referral ON users(referral_code)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_cash_orders_user ON cash_orders(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_fragment_orders_user ON fragment_orders(user_id)')
    except:
        pass

def get_db():
    return db


# ==================== USER MODEL ====================
class UserModel:
    @staticmethod
    def create(user_id: int, username: str, first_name: str, last_name: str) -> Dict:
        referral_code = f"ref_{user_id}_{uuid.uuid4().hex[:8]}"
        data = {
            'user_id': user_id, 'username': username, 'first_name': first_name,
            'last_name': last_name, 'joined_date': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(), 'referral_code': referral_code,
            'api_keys': '[]', 'achievements': '[]'
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
        data = {'paid': 1, 'subscription_until': subscription_until, 'api_keys': api_keys}
        db.update('users', data, 'user_id = ?', (user_id,))
        user = UserModel.get(user_id)
        if user and user.get('referred_by'):
            ReferralModel.mark_paid(user['referred_by'], user_id)
        UserModel.add_achievement(user_id, 'first_payment')
        return True
    
    @staticmethod
    def set_sim_paid(user_id: int, days: int = 30) -> bool:
        subscription_until = (datetime.now() + timedelta(days=days)).isoformat()
        data = {'sim_paid': 1, 'sim_subscription_until': subscription_until}
        db.update('users', data, 'user_id = ?', (user_id,))
        return True
    
    @staticmethod
    def activate_trial(user_id: int) -> bool:
        trial_until = (datetime.now() + timedelta(days=3)).isoformat()
        db.update('users', {'trial_until': trial_until}, 'user_id = ?', (user_id,))
        return True
    
    @staticmethod
    def is_ai_premium(user_id: int) -> bool:
        user = UserModel.get(user_id)
        if not user: return False
        if user['paid'] == 1 and user['subscription_until']:
            if datetime.fromisoformat(user['subscription_until']) > datetime.now(): return True
        if user['trial_until']:
            if datetime.fromisoformat(user['trial_until']) > datetime.now(): return True
        return False
    
    @staticmethod
    def is_sim_premium(user_id: int) -> bool:
        user = UserModel.get(user_id)
        if not user: return False
        if user['sim_paid'] == 1 and user['sim_subscription_until']:
            if datetime.fromisoformat(user['sim_subscription_until']) > datetime.now(): return True
        return False
    
    @staticmethod
    def increment_requests(user_id: int) -> None:
        db.execute('UPDATE users SET requests_today=requests_today+1, total_requests=total_requests+1, last_activity=? WHERE user_id=?',
                   (datetime.now().isoformat(), user_id))
        user = UserModel.get(user_id)
        if user and user['total_requests'] >= 100: UserModel.add_achievement(user_id, 'hundred_requests')
    
    @staticmethod
    def add_achievement(user_id: int, key: str) -> bool:
        user = UserModel.get(user_id)
        if not user: return False
        achievements = json.loads(user.get('achievements', '[]'))
        if key not in achievements:
            achievements.append(key)
            db.update('users', {'achievements': json.dumps(achievements)}, 'user_id = ?', (user_id,))
            return True
        return False
    
    @staticmethod
    def get_all(limit: int = 100, offset: int = 0) -> List[Dict]:
        return db.fetchall("SELECT * FROM users ORDER BY joined_date DESC LIMIT ? OFFSET ?", (limit, offset))
    
    @staticmethod
    def search(query: str) -> List[Dict]:
        q = f"%{query}%"
        return db.fetchall("SELECT * FROM users WHERE username LIKE ? OR first_name LIKE ? OR user_id LIKE ?", (q, q, q))
    
    @staticmethod
    def count_all() -> int:
        r = db.fetchone("SELECT COUNT(*) as count FROM users")
        return r['count'] if r else 0
    
    @staticmethod
    def get_top_users(limit: int = 10) -> List[Dict]:
        return db.fetchall('''SELECT user_id, username, first_name, total_requests, referral_bonus,
                            (total_requests + referral_bonus*10) as score FROM users
                            WHERE is_banned=0 ORDER BY score DESC LIMIT ?''', (limit,))


# ==================== PAYMENT MODEL ====================
class PaymentModel:
    @staticmethod
    def create(user_id: int, amount: int, method: str, payment_type: str = 'ai_access', currency: str = 'RUB') -> int:
        return db.insert('payments', {'user_id': user_id, 'amount': amount, 'currency': currency,
                                       'payment_method': method, 'payment_type': payment_type,
                                       'status': 'pending', 'created_at': datetime.now().isoformat()})
    
    @staticmethod
    def confirm(payment_id: int, tx_hash: str = '') -> bool:
        db.update('payments', {'status': 'confirmed', 'transaction_hash': tx_hash,
                                'confirmed_at': datetime.now().isoformat()}, 'payment_id = ?', (payment_id,))
        payment = PaymentModel.get(payment_id)
        if payment:
            if payment['payment_type'] == 'sim_dl': UserModel.set_sim_paid(payment['user_id'])
            else: UserModel.set_ai_paid(payment['user_id'])
        return True
    
    @staticmethod
    def get(payment_id: int) -> Optional[Dict]:
        return db.fetchone("SELECT * FROM payments WHERE payment_id=?", (payment_id,))
    
    @staticmethod
    def get_by_user(user_id: int) -> List[Dict]:
        return db.fetchall("SELECT * FROM payments WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    
    @staticmethod
    def get_all(limit: int = 50) -> List[Dict]:
        return db.fetchall("SELECT * FROM payments ORDER BY created_at DESC LIMIT ?", (limit,))
    
    @staticmethod
    def get_total_revenue() -> int:
        r = db.fetchone("SELECT SUM(amount) as total FROM payments WHERE status='confirmed'")
        return r['total'] or 0 if r else 0


# ==================== TICKET MODEL ====================
class TicketModel:
    @staticmethod
    def create(user_id: int) -> int:
        return db.insert('tickets', {'user_id': user_id, 'status': 'open', 'created_at': datetime.now().isoformat()})
    
    @staticmethod
    def get(ticket_id: int) -> Optional[Dict]:
        return db.fetchone("SELECT * FROM tickets WHERE ticket_id=?", (ticket_id,))
    
    @staticmethod
    def get_open_by_user(user_id: int) -> Optional[Dict]:
        return db.fetchone("SELECT * FROM tickets WHERE user_id=? AND status='open'", (user_id,))
    
    @staticmethod
    def get_all_open() -> List[Dict]:
        return db.fetchall("SELECT * FROM tickets WHERE status='open' ORDER BY created_at")
    
    @staticmethod
    def close(ticket_id: int) -> bool:
        db.update('tickets', {'status': 'closed', 'closed_at': datetime.now().isoformat()}, 'ticket_id = ?', (ticket_id,))
        return True


class TicketMessageModel:
    @staticmethod
    def add(ticket_id: int, sender_type: str, sender_id: int, message: str) -> int:
        return db.insert('ticket_messages', {'ticket_id': ticket_id, 'sender_type': sender_type,
                                              'sender_id': sender_id, 'message': message,
                                              'timestamp': datetime.now().isoformat()})
    
    @staticmethod
    def get_by_ticket(ticket_id: int) -> List[Dict]:
        return db.fetchall("SELECT * FROM ticket_messages WHERE ticket_id=? ORDER BY timestamp", (ticket_id,))


# ==================== BAN MODEL ====================
class BanModel:
    @staticmethod
    def add(user_id: int, reason: str, banned_by: int) -> bool:
        db.insert('banned_users', {'user_id': user_id, 'reason': reason, 'banned_by': banned_by,
                                    'banned_at': datetime.now().isoformat()})
        UserModel.update(user_id, {'is_banned': 1, 'ban_reason': reason})
        return True
    
    @staticmethod
    def remove(user_id: int) -> bool:
        db.delete('banned_users', 'user_id=?', (user_id,))
        UserModel.update(user_id, {'is_banned': 0, 'ban_reason': None})
        return True
    
    @staticmethod
    def is_banned(user_id: int) -> bool:
        return db.fetchone("SELECT * FROM banned_users WHERE user_id=?", (user_id,)) is not None


# ==================== REFERRAL MODEL ====================
class ReferralModel:
    @staticmethod
    def add(referrer_id: int, referred_id: int) -> bool:
        if db.fetchone("SELECT * FROM referrals WHERE referred_id=?", (referred_id,)): return False
        db.insert('referrals', {'referrer_id': referrer_id, 'referred_id': referred_id,
                                 'status': 'pending', 'created_at': datetime.now().isoformat()})
        return True
    
    @staticmethod
    def mark_paid(referrer_id: int, referred_id: int) -> bool:
        db.execute("UPDATE referrals SET status='paid', bonus_paid=1 WHERE referrer_id=? AND referred_id=?", 
                   (referrer_id, referred_id))
        db.execute("UPDATE users SET referral_bonus=referral_bonus+1 WHERE user_id=?", (referrer_id,))
        return True
    
    @staticmethod
    def get_stats(user_id: int) -> Dict:
        total = db.fetchone("SELECT COUNT(*) as count FROM referrals WHERE referrer_id=?", (user_id,))
        paid = db.fetchone("SELECT COUNT(*) as count FROM referrals WHERE referrer_id=? AND status='paid'", (user_id,))
        return {'total': total['count'] if total else 0, 'paid': paid['count'] if paid else 0}


# ==================== SIM MODEL ====================
class SimModel:
    @staticmethod
    def create_order(user_id: int, operator: str, region: str, tariff: str) -> int:
        return db.insert('sim_orders', {'user_id': user_id, 'operator': operator, 'region': region,
                                         'tariff': tariff, 'status': 'pending', 'created_at': datetime.now().isoformat()})
    
    @staticmethod
    def get_user_orders(user_id: int) -> List[Dict]:
        return db.fetchall("SELECT * FROM sim_orders WHERE user_id=? ORDER BY created_at DESC", (user_id,))


# ==================== PROMO MODEL ====================
class PromoModel:
    @staticmethod
    def check(code: str) -> Optional[Dict]:
        from config import PROMO_CODES
        return PROMO_CODES.get(code.upper())
    
    @staticmethod
    def use(user_id: int, code: str, discount: int) -> bool:
        db.insert('promo_usage', {'user_id': user_id, 'promo_code': code.upper(),
                                   'discount': discount, 'used_at': datetime.now().isoformat()})
        return True
    
    @staticmethod
    def is_used(user_id: int, code: str) -> bool:
        return db.fetchone("SELECT * FROM promo_usage WHERE user_id=? AND promo_code=?", 
                          (user_id, code.upper())) is not None


# ==================== SETTINGS MODEL ====================
class SettingsModel:
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        r = db.fetchone("SELECT value FROM settings WHERE key=?", (key,))
        return r['value'] if r else default
    
    @staticmethod
    def set(key: str, value: Any) -> bool:
        data = {'value': str(value), 'updated_at': datetime.now().isoformat()}
        if db.fetchone("SELECT * FROM settings WHERE key=?", (key,)):
            db.update('settings', data, 'key=?', (key,))
        else:
            data['key'] = key
            db.insert('settings', data)
        return True
