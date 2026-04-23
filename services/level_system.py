from config import LEVELS
from database.models import UserModel


class LevelSystem:
    @staticmethod
    def add_xp(user_id: int, xp: int):
        """Добавить опыт пользователю"""
        user = UserModel.get(user_id)
        if not user:
            return
        
        current_xp = user.get('experience', 0) + xp
        current_level = user.get('level', 1)
        
        # Проверяем повышение уровня
        new_level = current_level
        for level, data in LEVELS.items():
            if current_xp >= data['xp']:
                new_level = level
        
        UserModel.update(user_id, {
            'experience': current_xp,
            'level': new_level
        })
        
        if new_level > current_level:
            return new_level
        return None
    
    @staticmethod
    def get_level_info(level: int) -> dict:
        """Информация об уровне"""
        return LEVELS.get(level, LEVELS[1])
    
    @staticmethod
    def get_progress(user_id: int) -> dict:
        """Прогресс до следующего уровня"""
        user = UserModel.get(user_id)
        if not user:
            return {"current": 0, "next": 100, "percent": 0}
        
        current_level = user.get('level', 1)
        current_xp = user.get('experience', 0)
        
        next_level = current_level + 1
        if next_level in LEVELS:
            next_xp = LEVELS[next_level]['xp']
            current_level_xp = LEVELS[current_level]['xp']
            progress = current_xp - current_level_xp
            total = next_xp - current_level_xp
            percent = min(100, int(progress / total * 100)) if total > 0 else 100
        else:
            percent = 100
            next_xp = current_xp
        
        return {
            "level": current_level,
            "xp": current_xp,
            "next_xp": next_xp,
            "percent": percent
        }