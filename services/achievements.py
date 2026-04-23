import json
from datetime import datetime, timedelta
from config import ACHIEVEMENTS
from database.models import UserModel, db


class AchievementSystem:
    @staticmethod
    def check_and_award(user_id: int) -> list:
        """Проверить и выдать достижения"""
        user = UserModel.get(user_id)
        if not user:
            return []
        
        current = json.loads(user.get('achievements', '[]'))
        new_achievements = []
        
        # Проверка условий
        checks = {
            "first_payment": user.get('paid', 0) == 1,
            "hundred_requests": user.get('total_requests', 0) >= 100,
            "week_active": AchievementSystem._is_week_active(user),
            "five_friends": user.get('referral_bonus', 0) >= 5,
            "ten_friends": user.get('referral_bonus', 0) >= 10,
        }
        
        for key, condition in checks.items():
            if condition and key not in current:
                current.append(key)
                new_achievements.append(key)
        
        if new_achievements:
            UserModel.update(user_id, {'achievements': json.dumps(current)})
        
        return new_achievements
    
    @staticmethod
    def _is_week_active(user: dict) -> bool:
        """Проверка активности за неделю"""
        last_activity = user.get('last_activity')
        if not last_activity:
            return False
        
        try:
            last_date = datetime.fromisoformat(last_activity)
            week_ago = datetime.now() - timedelta(days=7)
            return last_date > week_ago
        except:
            return False
    
    @staticmethod
    def get_achievement_info(key: str) -> dict:
        """Информация о достижении"""
        return ACHIEVEMENTS.get(key, {"name": key, "emoji": "⭐"})