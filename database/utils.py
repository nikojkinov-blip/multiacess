import os
import json
import shutil
import sqlite3
from datetime import datetime
from config import DB_PATH

def backup_database() -> str:
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'{backup_dir}/bot_backup_{timestamp}.db'
    
    shutil.copy2(DB_PATH, backup_path)
    return backup_path

def restore_database(backup_path: str) -> bool:
    if not os.path.exists(backup_path):
        return False
    
    shutil.copy2(backup_path, DB_PATH)
    return True

def export_users_to_csv() -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    
    export_dir = 'exports'
    os.makedirs(export_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_path = f'{export_dir}/users_{timestamp}.csv'
    
    with open(export_path, 'w', encoding='utf-8') as f:
        f.write(','.join(columns) + '\n')
        for row in rows:
            f.write(','.join(str(cell) for cell in row) + '\n')
    
    conn.close()
    return export_path

def export_payments_to_csv() -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM payments')
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    
    export_dir = 'exports'
    os.makedirs(export_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_path = f'{export_dir}/payments_{timestamp}.csv'
    
    with open(export_path, 'w', encoding='utf-8') as f:
        f.write(','.join(columns) + '\n')
        for row in rows:
            f.write(','.join(str(cell) for cell in row) + '\n')
    
    conn.close()
    return export_path

def get_stats() -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute('SELECT COUNT(*) FROM users')
    stats['total_users'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE paid = 1')
    stats['paid_users'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM tickets WHERE status = "open"')
    stats['open_tickets'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(amount) FROM payments WHERE status = "confirmed"')
    revenue = cursor.fetchone()[0]
    stats['total_revenue'] = revenue if revenue else 0
    
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE joined_date >= datetime('now', '-1 day')
    ''')
    stats['new_users_24h'] = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM payments 
        WHERE status = "confirmed" 
        AND created_at >= datetime('now', '-1 day')
    ''')
    stats['payments_24h'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def get_daily_stats(days: int = 7) -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = []
    for i in range(days):
        cursor.execute(f'''
            SELECT 
                (SELECT COUNT(*) FROM users WHERE date(joined_date) = date('now', '-{i} day')) as users,
                (SELECT COUNT(*) FROM payments WHERE status = "confirmed" AND date(created_at) = date('now', '-{i} day')) as payments,
                (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = "confirmed" AND date(created_at) = date('now', '-{i} day')) as revenue
        ''')
        row = cursor.fetchone()
        stats.append({
            'date': f"now-{i}",
            'users': row[0],
            'payments': row[1],
            'revenue': row[2]
        })
    
    conn.close()
    return stats

def clean_old_logs(days: int = 30) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(f'''
        DELETE FROM admin_logs 
        WHERE timestamp < datetime('now', '-{days} day')
    ''')
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def reset_daily_requests() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET requests_today = 0')
    conn.commit()
    conn.close()