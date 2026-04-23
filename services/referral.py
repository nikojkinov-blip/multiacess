import random
import string
from database.models import UserModel, ReferralModel

def generate_referral_code(user_id: int) -> str:
    chars = string.ascii_letters + string.digits
    random_part = ''.join(random.choices(chars, k=8))
    return f"ref_{user_id}_{random_part}"

def process_referral_bonus(referrer_id: int, referred_id: int) -> None:
    ReferralModel.mark_paid(referrer_id, referred_id)
    
    user = UserModel.get(referrer_id)
    if user:
        current_bonus = user.get('referral_bonus', 0)
        
        if current_bonus >= 10:
            pass
        elif current_bonus >= 5:
            pass