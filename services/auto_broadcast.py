from datetime import datetime
from database.models import db, UserModel


class AutoBroadcast:
    @staticmethod
    def add_scheduled(admin_id: int, message: str, target: str, send_at: str):
        """Добавить отложенную рассылку"""
        return db.insert('scheduler', {
            'admin_id': admin_id,
            'message': message,
            'target': target,
            'send_at': send_at,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        })
    
    @staticmethod
    def get_pending():
        """Получить ожидающие рассылки"""
        return db.fetchall(
            "SELECT * FROM scheduler WHERE status = 'pending' AND send_at <= ?",
            (datetime.now().isoformat(),)
        )
    
    @staticmethod
    def mark_completed(broadcast_id: int, sent: int, failed: int):
        """Отметить рассылку выполненной"""
        db.update('scheduler', {
            'status': 'completed',
            'sent_count': sent,
            'failed_count': failed,
            'completed_at': datetime.now().isoformat()
        }, 'id = ?', (broadcast_id,))
    
    @staticmethod
    async def send_broadcast(bot, broadcast: dict):
        """Отправить рассылку"""
        if broadcast['target'] == 'ai_paid':
            users = db.fetchall("SELECT user_id FROM users WHERE paid = 1")
        elif broadcast['target'] == 'sim_paid':
            users = db.fetchall("SELECT user_id FROM users WHERE sim_paid = 1")
        elif broadcast['target'] == 'unpaid':
            users = db.fetchall("SELECT user_id FROM users WHERE paid = 0 AND sim_paid = 0")
        else:
            users = db.fetchall("SELECT user_id FROM users")
        
        sent, failed = 0, 0
        for user in users:
            try:
                await bot.send_message(user['user_id'], f"📢 {broadcast['message']}", parse_mode="HTML")
                sent += 1
            except:
                failed += 1
        
        AutoBroadcast.mark_completed(broadcast['id'], sent, failed)
        return sent, failed