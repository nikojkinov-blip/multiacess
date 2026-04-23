from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from datetime import datetime, timedelta
import sqlite3
import os
import asyncio
import aiohttp
from config import BOT_TOKEN

app = FastAPI(title="AI Access Bot + SIM.DL Admin", version="4.0")


# ============== ОТПРАВКА УВЕДОМЛЕНИЙ ==============
async def send_telegram_notification(user_id: int, text: str):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": user_id, "text": text, "parse_mode": "HTML"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                result = await response.json()
                return result.get('ok', False)
    except:
        return False


# ============== БАЗА ДАННЫХ ==============
def get_db():
    conn = sqlite3.connect('database/bot.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    stats = {}
    
    cursor.execute('SELECT COUNT(*) FROM users')
    stats['total_users'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE paid = 1')
    stats['ai_paid'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE sim_paid = 1')
    stats['sim_paid'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM tickets WHERE status = "open"')
    stats['open_tickets'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = "confirmed"')
    stats['total_revenue'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = "confirmed" AND payment_type = "ai_access"')
    stats['ai_revenue'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = "confirmed" AND payment_type = "sim_dl"')
    stats['sim_revenue'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sim_orders WHERE status = "pending"')
    stats['pending_sim_orders'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE joined_date >= datetime("now", "-1 day")')
    stats['new_users_24h'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "confirmed" AND created_at >= datetime("now", "-1 day")')
    stats['payments_24h'] = cursor.fetchone()[0]
    
    conn.close()
    return stats


def get_users(limit=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users ORDER BY joined_date DESC LIMIT ?', (limit,))
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users


def get_payments(limit=50, payment_type=None):
    conn = get_db()
    cursor = conn.cursor()
    if payment_type:
        cursor.execute('SELECT * FROM payments WHERE payment_type = ? ORDER BY created_at DESC LIMIT ?', (payment_type, limit))
    else:
        cursor.execute('SELECT * FROM payments ORDER BY created_at DESC LIMIT ?', (limit,))
    payments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return payments


def get_tickets(status='open'):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC', (status,))
    tickets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tickets


def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_sim_orders(status='all'):
    conn = get_db()
    cursor = conn.cursor()
    if status == 'all':
        cursor.execute('SELECT * FROM sim_orders ORDER BY created_at DESC')
    else:
        cursor.execute('SELECT * FROM sim_orders WHERE status = ? ORDER BY created_at DESC', (status,))
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders


def add_ticket_message(ticket_id, sender_type, sender_id, message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ticket_messages (ticket_id, sender_type, sender_id, message, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (ticket_id, sender_type, sender_id, message, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def close_ticket_db(ticket_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE tickets SET status = "closed", closed_at = ? WHERE ticket_id = ?', 
                   (datetime.now().isoformat(), ticket_id))
    conn.commit()
    conn.close()


def confirm_payment_db(payment_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE payments SET status = "confirmed", confirmed_at = ? WHERE payment_id = ?',
                   (datetime.now().isoformat(), payment_id))
    cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
    row = cursor.fetchone()
    if row:
        payment = dict(row)
        if payment['payment_type'] == 'sim_dl':
            cursor.execute('UPDATE users SET sim_paid = 1 WHERE user_id = ?', (payment['user_id'],))
        else:
            cursor.execute('UPDATE users SET paid = 1 WHERE user_id = ?', (payment['user_id'],))
    conn.commit()
    conn.close()


def complete_sim_order(order_id, sim_number):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sim_orders SET status = "completed", sim_number = ?, completed_at = ? WHERE order_id = ?
    ''', (sim_number, datetime.now().isoformat(), order_id))
    conn.commit()
    conn.close()


def ban_user_db(user_id, reason, admin_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO banned_users (user_id, reason, banned_by, banned_at) VALUES (?, ?, ?, ?)',
                   (user_id, reason, admin_id, datetime.now().isoformat()))
    cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def unban_user_db(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
    cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def add_sim_number(phone, operator, region, tariff):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sim_numbers (phone, operator, region, tariff, status, added_at)
        VALUES (?, ?, ?, ?, 'available', ?)
    ''', (phone, operator, region, tariff, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def init_tables():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, status TEXT DEFAULT 'open',
            created_at TEXT, closed_at TEXT, assigned_to INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticket_messages (
            msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER, sender_type TEXT, sender_id INTEGER,
            message TEXT, timestamp TEXT, is_read INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sim_orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, operator TEXT, region TEXT, tariff TEXT,
            status TEXT DEFAULT 'pending', sim_number TEXT,
            created_at TEXT, completed_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sim_numbers (
            number_id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT, operator TEXT, region TEXT, tariff TEXT,
            icc TEXT, status TEXT DEFAULT 'available',
            added_at TEXT, sold_to INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()


init_tables()


# ============== СТИЛИ ==============
STYLE = """
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', sans-serif; background: #f8f9fc; display: flex; }
    .sidebar {
        width: 260px; min-height: 100vh;
        background: linear-gradient(180deg, #4e73df 0%, #224abe 100%);
        padding: 20px 0; position: fixed; top: 0; bottom: 0;
    }
    .sidebar .nav-link {
        color: rgba(255,255,255,0.8); padding: 14px 20px;
        margin: 4px 12px; border-radius: 8px; display: block;
        text-decoration: none; transition: all 0.3s;
    }
    .sidebar .nav-link:hover { color: white; background: rgba(255,255,255,0.1); }
    .sidebar .nav-link.active { color: white; background: rgba(255,255,255,0.2); }
    .main-content { margin-left: 260px; padding: 30px; flex: 1; }
    .card {
        background: white; border-radius: 12px;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58,59,69,0.1);
        margin-bottom: 20px;
    }
    .card-header {
        padding: 15px 20px; border-bottom: 1px solid #e3e6f0;
        font-weight: 600; color: #4e73df;
    }
    .card-body { padding: 20px; }
    .stat-card {
        background: white; border-radius: 12px; padding: 25px;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58,59,69,0.15);
    }
    .stat-card h3 { font-size: 28px; margin-bottom: 5px; }
    .stat-card p { color: #888; margin: 0; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }
    th { font-weight: 600; color: #5a5c69; font-size: 13px; text-transform: uppercase; }
    tr:hover { background: #f8f9fc; }
    .btn {
        display: inline-block; padding: 10px 20px; border-radius: 8px;
        text-decoration: none; font-weight: 500; border: none; cursor: pointer;
        font-size: 14px; transition: all 0.2s;
    }
    .btn-primary { background: #4e73df; color: white; }
    .btn-success { background: #1cc88a; color: white; }
    .btn-warning { background: #f6c23e; color: white; }
    .btn-danger { background: #e74a3b; color: white; }
    .btn-info { background: #36b9cc; color: white; }
    .btn:hover { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
    .badge {
        padding: 5px 12px; border-radius: 20px; font-size: 12px;
        font-weight: 500;
    }
    .badge-success { background: #1cc88a; color: white; }
    .badge-warning { background: #f6c23e; color: white; }
    .badge-danger { background: #e74a3b; color: white; }
    .badge-info { background: #36b9cc; color: white; }
    .row { display: flex; gap: 20px; flex-wrap: wrap; }
    .col-md-3 { flex: 0 0 calc(25% - 15px); }
    .col-md-4 { flex: 0 0 calc(33.333% - 14px); }
    .col-md-6 { flex: 0 0 calc(50% - 10px); }
    .col-md-8 { flex: 0 0 calc(66.666% - 7px); }
    .form-control {
        width: 100%; padding: 12px; border: 1px solid #ddd;
        border-radius: 8px; font-size: 14px; margin-bottom: 10px;
    }
    .form-select {
        width: 100%; padding: 12px; border: 1px solid #ddd;
        border-radius: 8px; font-size: 14px; margin-bottom: 10px;
    }
    textarea.form-control { resize: vertical; min-height: 100px; }
    .alert {
        padding: 15px 20px; border-radius: 8px; margin-bottom: 20px;
    }
    .alert-info { background: #e8f4fd; color: #0c5460; border: 1px solid #bee5eb; }
    .modal {
        display: none; position: fixed; z-index: 1000;
        left: 0; top: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.5); align-items: center; justify-content: center;
    }
    .modal-content {
        background: white; border-radius: 12px; padding: 30px;
        max-width: 500px; width: 90%;
    }
    .user-profile { position: absolute; bottom: 20px; width: 100%; padding: 15px; color: white; border-top: 1px solid rgba(255,255,255,0.1); }
    
    body.dark { background: #1a1a2e !important; }
    body.dark .card { background: #16213e; color: #e0e0e0; }
    body.dark .card-header { background: #0f3460; border-color: #1a1a5e; color: #fff; }
    body.dark .stat-card { background: #16213e; color: #e0e0e0; }
    body.dark .stat-card p { color: #aaa; }
    body.dark table { color: #e0e0e0; }
    body.dark th { color: #aaa; }
    body.dark tr:hover { background: #1a1a5e; }
    body.dark td { border-color: #1a1a5e; }
    body.dark .form-control, body.dark .form-select { background: #16213e; color: #fff; border-color: #1a1a5e; }
    
    @media (max-width: 768px) {
        .sidebar { width: 100%; min-height: auto; position: relative; }
        .main-content { margin-left: 0; }
        .col-md-3, .col-md-4, .col-md-6, .col-md-8 { flex: 0 0 100%; }
        .row { flex-direction: column; }
    }
</style>
"""


# ============== СТРАНИЦА ВХОДА ==============
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Access + SIM.DL - Вход</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
        <style>
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; display: flex; align-items: center; justify-content: center;
                font-family: 'Segoe UI', sans-serif;
            }}
            .login-card {{
                background: white; border-radius: 24px; padding: 50px 40px;
                max-width: 420px; width: 100%; text-align: center;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
            }}
            .logos {{ font-size: 48px; margin-bottom: 20px; }}
            .logos i {{ margin: 0 10px; }}
            h2 {{ font-weight: 700; color: #1a1a2e; margin-bottom: 5px; }}
            .subtitle {{ color: #666; margin-bottom: 10px; }}
            .badges {{ display: flex; gap: 10px; justify-content: center; margin-bottom: 25px; }}
            .badge-item {{
                background: #f0f0ff; padding: 8px 16px; border-radius: 20px;
                font-size: 13px; color: #667eea;
            }}
            .btn-login {{ width: 100%; padding: 14px; font-size: 16px; background: #667eea; color: white; border: none; border-radius: 12px; cursor: pointer; }}
            .btn-login:hover {{ background: #5a6fd6; }}
            .hint {{ margin-top: 20px; color: #999; font-size: 13px; }}
            input {{ width: 100%; padding: 14px; border: 2px solid #e0e0e0; border-radius: 12px; font-size: 16px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="logos">
                <i class="bi bi-robot" style="color:#667eea;"></i>
                <i class="bi bi-sim" style="color:#764ba2;"></i>
            </div>
            <h2>AI Access + SIM.DL</h2>
            <p class="subtitle">Административная панель</p>
            <div class="badges">
                <span class="badge-item">🤖 AI</span>
                <span class="badge-item">📱 SIM</span>
                <span class="badge-item">💰 Платежи</span>
            </div>
            
            <form method="POST" action="/login">
                <input type="number" name="user_id" placeholder="Введите Telegram ID" required autofocus>
                <br><br>
                <button type="submit" class="btn-login">
                    <i class="bi bi-box-arrow-in-right"></i> Войти
                </button>
            </form>
            
            <div class="hint">
                <i class="bi bi-info-circle"></i> 
                ID можно узнать у @userinfobot
            </div>
        </div>
    </body>
    </html>
    """


@app.post("/login")
async def login(user_id: int = Form(...)):
    from config import ADMIN_IDS
    
    if user_id not in ADMIN_IDS:
        return HTMLResponse("<h2>Доступ запрещён</h2><a href='/'>Назад</a>", status_code=403)
    
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie("user_id", str(user_id))
    return response


# ============== ДАШБОРД ==============
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/")
    
    stats = get_stats()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Дашборд</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
        {STYLE}
    </head>
    <body>
        <div class="sidebar">
            <div class="text-center py-3">
                <i class="bi bi-robot fs-1 text-white"></i>
                <i class="bi bi-sim fs-1 text-white"></i>
                <h5 class="text-white mt-2">AI + SIM Admin</h5>
            </div>
            <hr class="text-white-50 mx-3">
            <a class="nav-link active" href="/dashboard"><i class="bi bi-speedometer2 me-2"></i>Дашборд</a>
            <a class="nav-link" href="/users"><i class="bi bi-people me-2"></i>Пользователи</a>
            <a class="nav-link" href="/payments"><i class="bi bi-credit-card me-2"></i>Платежи</a>
            <a class="nav-link" href="/sim-orders"><i class="bi bi-sim me-2"></i>SIM заказы <span class="badge badge-warning">{stats['pending_sim_orders']}</span></a>
            <a class="nav-link" href="/tickets"><i class="bi bi-chat-dots me-2"></i>Тикеты <span class="badge badge-danger">{stats['open_tickets']}</span></a>
            <a class="nav-link" href="/broadcast"><i class="bi bi-megaphone me-2"></i>Рассылка</a>
            <a class="nav-link" href="/sim-numbers"><i class="bi bi-database me-2"></i>База номеров</a>
            <a class="nav-link" href="#" onclick="toggleTheme()"><i class="bi bi-moon me-2"></i>Тема</a>
            
            <div class="user-profile">
                <small>Admin ID: {user_id}</small><br>
                <a href="/logout" class="text-white-50 small">🚪 Выйти</a>
            </div>
        </div>
        
        <div class="main-content">
            <h2 class="mb-4">👋 Дашборд</h2>
            
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="stat-card">
                        <h3 style="color:#4e73df;">{stats['total_users']}</h3>
                        <p><i class="bi bi-people"></i> Пользователей</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <h3 style="color:#1cc88a;">{stats['ai_paid']}</h3>
                        <p>🤖 AI Premium</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <h3 style="color:#f6c23e;">{stats['sim_paid']}</h3>
                        <p>📱 SIM Premium</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <h3 style="color:#e74a3b;">{stats['total_revenue']} ₽</h3>
                        <p><i class="bi bi-cash-stack"></i> Доход</p>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header"><i class="bi bi-bar-chart"></i> Доход по направлениям</div>
                        <div class="card-body">
                            <p>🤖 AI Access: <strong>{stats['ai_revenue']} ₽</strong></p>
                            <p>📱 SIM.DL: <strong>{stats['sim_revenue']} ₽</strong></p>
                            <p>📋 Открытых тикетов: <strong>{stats['open_tickets']}</strong></p>
                            <p>📱 Заказов SIM (ожидают): <strong>{stats['pending_sim_orders']}</strong></p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header"><i class="bi bi-clock"></i> За 24 часа</div>
                        <div class="card-body">
                            <p>Новых пользователей: <strong>{stats['new_users_24h']}</strong></p>
                            <p>Новых оплат: <strong>{stats['payments_24h']}</strong></p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-4">
                    <a href="/users" class="btn btn-primary" style="display:block;text-align:center;">👥 Пользователи</a>
                </div>
                <div class="col-md-4">
                    <a href="/sim-orders" class="btn btn-warning" style="display:block;text-align:center;">📱 SIM заказы</a>
                </div>
                <div class="col-md-4">
                    <a href="/broadcast" class="btn btn-info" style="display:block;text-align:center;">📢 Рассылка</a>
                </div>
            </div>
        </div>
        
        <script>
            function toggleTheme() {{
                document.body.classList.toggle('dark');
                localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
            }}
            if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark');
        </script>
    </body>
    </html>
    """


# ============== ПОЛЬЗОВАТЕЛИ ==============
@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    if not request.cookies.get("user_id"):
        return RedirectResponse(url="/")
    
    users = get_users(200)
    rows = ""
    for u in users:
        ai = "💎" if u.get('paid') else "—"
        sim = "📱" if u.get('sim_paid') else "—"
        banned = "🚫" if u.get('is_banned') else ""
        rows += f"""
        <tr>
            <td><code>{u['user_id']}</code></td>
            <td>@{u.get('username', '—')}</td>
            <td>{ai} {sim} {banned}</td>
            <td><a href='/user/{u['user_id']}' class='btn btn-primary' style='padding:5px 10px;'>→</a></td>
        </tr>"""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Пользователи</title>{STYLE}</head>
    <body>
        <div class="sidebar">
            <div class="text-center py-3"><h5 class="text-white">AI+SIM Admin</h5></div>
            <hr class="text-white-50 mx-3">
            <a class="nav-link" href="/dashboard">Дашборд</a>
            <a class="nav-link active" href="/users">Пользователи</a>
            <a class="nav-link" href="/payments">Платежи</a>
            <a class="nav-link" href="/sim-orders">SIM заказы</a>
            <a class="nav-link" href="/tickets">Тикеты</a>
            <div class="user-profile"><a href="/logout" class="text-white-50">🚪 Выйти</a></div>
        </div>
        <div class="main-content">
            <h2>👥 Пользователи</h2>
            <div class="card">
                <div class="card-body">
                    <table>
                        <thead><tr><th>ID</th><th>Username</th><th>Статус</th><th></th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>"""


# ============== ДЕТАЛИ ПОЛЬЗОВАТЕЛЯ ==============
@app.get("/user/{user_id}", response_class=HTMLResponse)
async def user_detail(request: Request, user_id: int):
    if not request.cookies.get("user_id"):
        return RedirectResponse(url="/")
    
    user = get_user(user_id)
    if not user:
        return HTMLResponse("<h2>Не найден</h2>")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    payments = [dict(row) for row in cursor.fetchall()]
    cursor.execute('SELECT * FROM sim_orders WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    sim_orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    payments_html = ""
    for p in payments[:10]:
        s = "✅" if p['status'] == 'confirmed' else "⏳"
        t = "SIM" if p.get('payment_type') == 'sim_dl' else "AI"
        payments_html += f"<tr><td>#{p['payment_id']}</td><td>{t}</td><td>{p['amount']}₽</td><td>{s}</td></tr>"
    
    sim_html = ""
    for o in sim_orders[:10]:
        s = "✅" if o['status'] == 'completed' else "⏳"
        sim_html += f"<tr><td>#{o['order_id']}</td><td>{o['operator']}</td><td>{o['region']}</td><td>{s}</td></tr>"
    
    banned = user.get('is_banned', 0)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>User {user_id}</title>{STYLE}</head>
    <body>
        <div class="sidebar">
            <div class="text-center py-3"><h5 class="text-white">AI+SIM Admin</h5></div>
            <hr class="text-white-50 mx-3">
            <a class="nav-link" href="/dashboard">Дашборд</a>
            <a class="nav-link active" href="/users">Пользователи</a>
            <div class="user-profile"><a href="/logout" class="text-white-50">🚪 Выйти</a></div>
        </div>
        <div class="main-content">
            <h2>👤 @{user.get('username', 'ID:'+str(user_id))}</h2>
            <a href="/users" class="btn btn-primary mb-3">← Назад</a>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Информация</div>
                        <div class="card-body">
                            <p><strong>ID:</strong> <code>{user['user_id']}</code></p>
                            <p><strong>AI Premium:</strong> {'✅' if user.get('paid') else '❌'}</p>
                            <p><strong>SIM Premium:</strong> {'✅' if user.get('sim_paid') else '❌'}</p>
                            <p><strong>Бан:</strong> {'🚫' if banned else '✅'}</p>
                            <p><strong>Запросов:</strong> {user.get('total_requests', 0)}</p>
                        </div>
                    </div>
                    <div class="card mt-3">
                        <div class="card-header">Действия</div>
                        <div class="card-body">
                            <form method="POST" action="/api/user/{user_id}/ai-premium" style="display:inline;">
                                <button class="btn btn-success">🤖 AI Premium</button>
                            </form>
                            <form method="POST" action="/api/user/{user_id}/sim-premium" style="display:inline;">
                                <button class="btn btn-warning">📱 SIM Premium</button>
                            </form>
                            <form method="POST" action="/api/user/{user_id}/ban" style="display:inline;">
                                <button class="btn btn-danger" {'disabled' if banned else ''}>🚫 Бан</button>
                            </form>
                            <form method="POST" action="/api/user/{user_id}/unban" style="display:inline;">
                                <button class="btn btn-info" {'disabled' if not banned else ''}>✅ Разбан</button>
                            </form>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Платежи</div>
                        <div class="card-body">
                            <table><thead><tr><th>ID</th><th>Тип</th><th>Сумма</th><th>Статус</th></tr></thead>
                            <tbody>{payments_html or '<tr><td colspan="4">Нет</td></tr>'}</tbody></table>
                        </div>
                    </div>
                    <div class="card mt-3">
                        <div class="card-header">SIM Заказы</div>
                        <div class="card-body">
                            <table><thead><tr><th>ID</th><th>Оператор</th><th>Регион</th><th>Статус</th></tr></thead>
                            <tbody>{sim_html or '<tr><td colspan="4">Нет</td></tr>'}</tbody></table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>"""


# ============== ПЛАТЕЖИ ==============
@app.get("/payments", response_class=HTMLResponse)
async def payments_page(request: Request):
    if not request.cookies.get("user_id"):
        return RedirectResponse(url="/")
    
    payments = get_payments(200)
    
    rows = ""
    for p in payments:
        s = "✅" if p['status'] == 'confirmed' else "⏳"
        t = p.get('payment_type', 'ai_access')
        t_badge = "🤖 AI" if t == 'ai_access' else "📱 SIM"
        confirm = f"<a href='/api/payment/{p['payment_id']}/confirm' class='btn btn-success' style='padding:5px 10px;'>Подтв.</a>" if p['status'] != 'confirmed' else ""
        rows += f"<tr><td>#{p['payment_id']}</td><td><a href='/user/{p['user_id']}'>{p['user_id']}</a></td><td><span class='badge badge-{'info' if t=='ai_access' else 'warning'}'>{t_badge}</span></td><td>{p['amount']}₽</td><td>{s}</td><td>{confirm}</td></tr>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Платежи</title>{STYLE}</head>
    <body>
        <div class="sidebar">
            <div class="text-center py-3"><h5 class="text-white">AI+SIM Admin</h5></div>
            <hr class="text-white-50 mx-3">
            <a class="nav-link" href="/dashboard">Дашборд</a>
            <a class="nav-link active" href="/payments">Платежи</a>
            <a class="nav-link" href="/sim-orders">SIM заказы</a>
            <a class="nav-link" href="/tickets">Тикеты</a>
        </div>
        <div class="main-content">
            <h2>💰 Платежи</h2>
            <div class="card">
                <div class="card-body">
                    <table><thead><tr><th>ID</th><th>User</th><th>Тип</th><th>Сумма</th><th>Статус</th><th></th></tr></thead>
                    <tbody>{rows}</tbody></table>
                </div>
            </div>
        </div>
    </body>
    </html>"""


# ============== SIM ЗАКАЗЫ ==============
@app.get("/sim-orders", response_class=HTMLResponse)
async def sim_orders_page(request: Request):
    if not request.cookies.get("user_id"):
        return RedirectResponse(url="/")
    
    orders = get_sim_orders('all')
    
    rows = ""
    for o in orders:
        s = "✅" if o['status'] == 'completed' else "⏳"
        num = o.get('sim_number', '—')
        action = f"<button onclick='openCompleteModal({o['order_id']})' class='btn btn-success' style='padding:5px 10px;'>Выдать</button>" if o['status'] == 'pending' else ""
        rows += f"""
        <tr>
            <td>#{o['order_id']}</td>
            <td><a href='/user/{o['user_id']}'>{o['user_id']}</a></td>
            <td>{o['operator']}</td>
            <td>{o['region']}</td>
            <td>{o['tariff']}</td>
            <td>{num}</td>
            <td>{s}</td>
            <td>{action}</td>
        </tr>"""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>SIM Заказы</title>{STYLE}</head>
    <body>
        <div class="sidebar">
            <div class="text-center py-3"><h5 class="text-white">AI+SIM Admin</h5></div>
            <hr class="text-white-50 mx-3">
            <a class="nav-link" href="/dashboard">Дашборд</a>
            <a class="nav-link active" href="/sim-orders">SIM заказы</a>
            <a class="nav-link" href="/sim-numbers">База номеров</a>
            <a class="nav-link" href="/tickets">Тикеты</a>
        </div>
        <div class="main-content">
            <h2>📱 SIM Заказы</h2>
            <div class="card">
                <div class="card-body">
                    <table><thead><tr><th>ID</th><th>User</th><th>Оператор</th><th>Регион</th><th>Тариф</th><th>Номер</th><th>Статус</th><th></th></tr></thead>
                    <tbody>{rows}</tbody></table>
                </div>
            </div>
        </div>
        
        <div id="completeModal" class="modal">
            <div class="modal-content">
                <h3>Выдать номер для заказа <span id="modalOrderId"></span></h3>
                <form id="completeForm" method="POST">
                    <label>Номер телефона:</label>
                    <input type="text" name="sim_number" class="form-control" placeholder="+7XXXXXXXXXX" required>
                    <br>
                    <button type="submit" class="btn btn-success">Выдать</button>
                    <button type="button" class="btn btn-primary" onclick="closeModal()">Отмена</button>
                </form>
            </div>
        </div>
        
        <script>
            function openCompleteModal(orderId) {{
                document.getElementById('modalOrderId').textContent = '#' + orderId;
                document.getElementById('completeForm').action = '/api/sim-order/' + orderId + '/complete';
                document.getElementById('completeModal').style.display = 'flex';
            }}
            function closeModal() {{
                document.getElementById('completeModal').style.display = 'none';
            }}
            window.onclick = function(event) {{
                if (event.target == document.getElementById('completeModal')) closeModal();
            }}
        </script>
    </body>
    </html>"""


# ============== БАЗА SIM НОМЕРОВ ==============
@app.get("/sim-numbers", response_class=HTMLResponse)
async def sim_numbers_page(request: Request):
    if not request.cookies.get("user_id"):
        return RedirectResponse(url="/")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sim_numbers ORDER BY added_at DESC')
    numbers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    rows = ""
    for n in numbers:
        s = "🟢" if n['status'] == 'available' else "🔴"
        sold = f"User {n['sold_to']}" if n.get('sold_to') else "—"
        rows += f"<tr><td>{n['phone']}</td><td>{n['operator']}</td><td>{n['region']}</td><td>{n['tariff']}</td><td>{s}</td><td>{sold}</td></tr>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>База номеров</title>{STYLE}</head>
    <body>
        <div class="sidebar">
            <div class="text-center py-3"><h5 class="text-white">AI+SIM Admin</h5></div>
            <hr class="text-white-50 mx-3">
            <a class="nav-link" href="/dashboard">Дашборд</a>
            <a class="nav-link active" href="/sim-orders">SIM заказы</a>
            <a class="nav-link" href="/sim-numbers">База номеров</a>
        </div>
        <div class="main-content">
            <h2>📊 База SIM номеров</h2>
            
            <div class="card mb-4">
                <div class="card-header">Добавить номера</div>
                <div class="card-body">
                    <form method="POST" action="/api/sim-numbers/add">
                        <div class="row">
                            <div class="col-md-4">
                                <input type="text" name="phone" class="form-control" placeholder="+79261234567" required>
                            </div>
                            <div class="col-md-2">
                                <select name="operator" class="form-select">
                                    <option>Билайн</option><option>Мегафон</option><option>МТС</option><option>Tele2</option>
                                </select>
                            </div>
                            <div class="col-md-2">
                                <select name="region" class="form-select">
                                    <option>Москва</option><option>СПб</option><option>Казань</option>
                                </select>
                            </div>
                            <div class="col-md-2">
                                <select name="tariff" class="form-select">
                                    <option>Доверенное лицо</option><option>Корпоративный</option>
                                </select>
                            </div>
                            <div class="col-md-2">
                                <button type="submit" class="btn btn-success">+ Добавить</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <table><thead><tr><th>Номер</th><th>Оператор</th><th>Регион</th><th>Тариф</th><th>Статус</th><th>Продан</th></tr></thead>
                    <tbody>{rows or '<tr><td colspan="6">Нет номеров</td></tr>'}</tbody></table>
                </div>
            </div>
        </div>
    </body>
    </html>"""


# ============== ТИКЕТЫ ==============
@app.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request):
    if not request.cookies.get("user_id"):
        return RedirectResponse(url="/")
    
    tickets = get_tickets('open')
    rows = ""
    for t in tickets:
        user = get_user(t['user_id'])
        username = f"@{user['username']}" if user and user.get('username') else f"ID:{t['user_id']}"
        rows += f"<tr><td>#{t['ticket_id']}</td><td>{username}</td><td><a href='/ticket/{t['ticket_id']}' class='btn btn-primary' style='padding:5px 10px;'>→</a></td></tr>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Тикеты</title>{STYLE}</head>
    <body>
        <div class="sidebar">
            <div class="text-center py-3"><h5 class="text-white">AI+SIM Admin</h5></div>
            <a class="nav-link" href="/dashboard">Дашборд</a>
            <a class="nav-link active" href="/tickets">Тикеты</a>
        </div>
        <div class="main-content">
            <h2>📋 Тикеты</h2>
            <div class="card"><div class="card-body">
                <table><thead><tr><th>ID</th><th>User</th><th></th></tr></thead>
                <tbody>{rows or '<tr><td colspan="3">Нет</td></tr>'}</tbody></table>
            </div></div>
        </div>
    </body>
    </html>"""


@app.get("/ticket/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail(request: Request, ticket_id: int):
    if not request.cookies.get("user_id"):
        return RedirectResponse(url="/")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets WHERE ticket_id = ?', (ticket_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return HTMLResponse("<h2>Не найден</h2>")
    
    ticket = dict(row)
    cursor.execute('SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY timestamp', (ticket_id,))
    messages = [dict(m) for m in cursor.fetchall()]
    conn.close()
    
    user = get_user(ticket['user_id'])
    username = f"@{user['username']}" if user and user.get('username') else f"ID:{ticket['user_id']}"
    
    msgs = ""
    for m in messages:
        sender = "👤 Юзер" if m.get('sender_type') == 'user' else "👨‍💼 Саппорт"
        if m.get('sender_type') == 'system': sender = "🤖 Система"
        msgs += f"<div class='card mb-2'><div class='card-body'><strong>{sender}:</strong><p>{m.get('message','')}</p><small>{m.get('timestamp','')[:16]}</small></div></div>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Тикет #{ticket_id}</title>{STYLE}</head>
    <body>
        <div class="sidebar"><div class="text-center py-3"><h5 class="text-white">AI+SIM Admin</h5></div></div>
        <div class="main-content">
            <h2>📋 Тикет #{ticket_id}</h2>
            <div style="margin-bottom:20px;">
                <a href="/tickets" class="btn btn-primary">← Назад</a>
                <button onclick="openCloseModal()" class="btn btn-warning">Закрыть</button>
            </div>
            <div class="alert alert-info">
                <strong>Пользователь:</strong> {username} (ID: {ticket['user_id']})<br>
                <strong>Создан:</strong> {ticket.get('created_at','—')[:16]}
            </div>
            <div class="card mb-4"><div class="card-header">Переписка</div>
                <div class="card-body" style="max-height:400px;overflow-y:auto;">{msgs or 'Нет сообщений'}</div>
            </div>
            <div class="card"><div class="card-header">Ответить</div>
                <div class="card-body">
                    <form method="POST" action="/api/ticket/{ticket_id}/reply">
                        <textarea name="message" class="form-control" rows="4" required></textarea><br>
                        <button type="submit" class="btn btn-success">Отправить</button>
                    </form>
                </div>
            </div>
        </div>
        
        <div id="closeModal" class="modal">
            <div class="modal-content">
                <h3>Закрыть тикет #{ticket_id}</h3>
                <form method="POST" action="/api/ticket/{ticket_id}/close">
                    <select name="reason" class="form-select">
                        <option>Обращение рассмотрено</option>
                        <option>Проблема решена</option>
                        <option>Нет ответа</option>
                        <option>Спам</option>
                    </select><br>
                    <button type="submit" class="btn btn-warning">Закрыть</button>
                    <button type="button" class="btn btn-primary" onclick="closeCloseModal()">Отмена</button>
                </form>
            </div>
        </div>
        <script>
            function openCloseModal() {{ document.getElementById('closeModal').style.display='flex'; }}
            function closeCloseModal() {{ document.getElementById('closeModal').style.display='none'; }}
        </script>
    </body>
    </html>"""


# ============== РАССЫЛКА ==============
@app.get("/broadcast", response_class=HTMLResponse)
async def broadcast_page(request: Request):
    if not request.cookies.get("user_id"):
        return RedirectResponse(url="/")
    
    stats = get_stats()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Рассылка</title>{STYLE}</head>
    <body>
        <div class="sidebar"><div class="text-center py-3"><h5 class="text-white">AI+SIM Admin</h5></div></div>
        <div class="main-content">
            <h2>📢 Рассылка</h2>
            <div class="card"><div class="card-header">Новая рассылка</div>
                <div class="card-body">
                    <form method="POST" action="/api/broadcast">
                        <textarea name="message" class="form-control" rows="5" required></textarea><br>
                        <select name="target" class="form-select">
                            <option value="all">Все ({stats['total_users']})</option>
                            <option value="ai_paid">AI Premium ({stats['ai_paid']})</option>
                            <option value="sim_paid">SIM Premium ({stats['sim_paid']})</option>
                        </select><br>
                        <button type="submit" class="btn btn-success">Отправить</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>"""


# ============== API ==============
@app.post("/api/ticket/{ticket_id}/reply")
async def api_ticket_reply(ticket_id: int, message: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM tickets WHERE ticket_id = ?', (ticket_id,))
    row = cursor.fetchone()
    if row:
        add_ticket_message(ticket_id, 'admin', 0, message)
        await send_telegram_notification(
            row[0],
            f"📞 <b>Ответ поддержки в тикете #{ticket_id}</b>\n\n{message}"
        )
    conn.close()
    return RedirectResponse(url=f"/ticket/{ticket_id}", status_code=302)


@app.post("/api/ticket/{ticket_id}/close")
async def api_ticket_close(ticket_id: int, reason: str = Form("Обращение рассмотрено")):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM tickets WHERE ticket_id = ?', (ticket_id,))
    row = cursor.fetchone()
    if row:
        close_ticket_db(ticket_id)
        add_ticket_message(ticket_id, 'system', 0, f"Тикет закрыт\nПричина: {reason}")
        await send_telegram_notification(
            row[0],
            f"✅ <b>Тикет #{ticket_id} закрыт</b>\n\nПричина: {reason}\n\n/support для нового обращения"
        )
    conn.close()
    return RedirectResponse(url="/tickets", status_code=302)


@app.get("/api/payment/{payment_id}/confirm")
async def api_payment_confirm(payment_id: int):
    confirm_payment_db(payment_id)
    return RedirectResponse(url="/payments", status_code=302)


@app.post("/api/sim-order/{order_id}/complete")
async def api_complete_sim_order(order_id: int, sim_number: str = Form(...)):
    complete_sim_order(order_id, sim_number)
    order = get_sim_orders('all')
    order = [o for o in order if o['order_id'] == order_id]
    if order:
        await send_telegram_notification(
            order[0]['user_id'],
            f"📱 <b>Ваш SIM заказ #{order_id} выполнен!</b>\n\n"
            f"Номер: <code>{sim_number}</code>\n"
            f"Оператор: {order[0]['operator']}\n"
            f"Тариф: {order[0]['tariff']}"
        )
    return RedirectResponse(url="/sim-orders", status_code=302)


@app.post("/api/sim-numbers/add")
async def api_add_sim_number(
    phone: str = Form(...),
    operator: str = Form(...),
    region: str = Form(...),
    tariff: str = Form(...)
):
    add_sim_number(phone, operator, region, tariff)
    return RedirectResponse(url="/sim-numbers", status_code=302)


@app.post("/api/user/{user_id}/ai-premium")
async def api_user_ai_premium(user_id: int):
    from database.models import UserModel
    UserModel.set_ai_paid(user_id)
    await send_telegram_notification(user_id, "🤖 <b>Вам выдан AI Premium доступ!</b>\n\nИспользуйте /key")
    return RedirectResponse(url=f"/user/{user_id}", status_code=302)


@app.post("/api/user/{user_id}/sim-premium")
async def api_user_sim_premium(user_id: int):
    from database.models import UserModel
    UserModel.set_sim_paid(user_id)
    await send_telegram_notification(user_id, "📱 <b>Вам выдан SIM.DL доступ!</b>\n\nСоздайте заказ в боте.")
    return RedirectResponse(url=f"/user/{user_id}", status_code=302)


@app.post("/api/user/{user_id}/ban")
async def api_user_ban(user_id: int, reason: str = Form("Нарушение")):
    ban_user_db(user_id, reason, 0)
    await send_telegram_notification(user_id, f"🚫 <b>Вы заблокированы</b>\n\nПричина: {reason}")
    return RedirectResponse(url=f"/user/{user_id}", status_code=302)


@app.post("/api/user/{user_id}/unban")
async def api_user_unban(user_id: int):
    unban_user_db(user_id)
    await send_telegram_notification(user_id, "✅ <b>Вы разблокированы!</b>")
    return RedirectResponse(url=f"/user/{user_id}", status_code=302)


@app.post("/api/broadcast")
async def api_broadcast(message: str = Form(...), target: str = Form("all")):
    conn = get_db()
    cursor = conn.cursor()
    
    if target == 'ai_paid':
        cursor.execute('SELECT user_id FROM users WHERE paid = 1')
    elif target == 'sim_paid':
        cursor.execute('SELECT user_id FROM users WHERE sim_paid = 1')
    else:
        cursor.execute('SELECT user_id FROM users')
    
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    sent = 0
    for uid in users:
        if await send_telegram_notification(uid, f"📢 {message}"):
            sent += 1
    
    return HTMLResponse(f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8">{STYLE}</head>
    <body class="d-flex justify-content-center align-items-center vh-100">
        <div class="text-center card" style="padding:40px;">
            <h2>✅ Рассылка завершена!</h2>
            <p>Отправлено: {sent} / {len(users)}</p>
            <a href="/broadcast" class="btn btn-primary">Новая</a>
            <a href="/dashboard" class="btn btn-info">Дашборд</a>
        </div>
    </body></html>""")


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("user_id")
    return response


@app.get("/api/stats")
async def api_stats():
    return get_stats()