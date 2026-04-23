from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database.models import UserModel, PaymentModel, SimModel
from services.level_system import LevelSystem
from services.achievements import AchievementSystem
import json

app = FastAPI(title="AI Access Bot WebApp")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/webapp", response_class=HTMLResponse)
async def webapp():
    """Главная страница WebApp"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scale=no">
        <title>AI Access Bot</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', sans-serif;
                background: #1a1a2e;
                color: white;
                min-height: 100vh;
                padding: 15px;
            }
            .header {
                text-align: center;
                padding: 20px 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                margin-bottom: 20px;
            }
            .header h1 { font-size: 24px; }
            .header p { opacity: 0.7; font-size: 14px; margin-top: 5px; }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin-bottom: 20px;
            }
            .stat-box {
                background: rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 15px;
                text-align: center;
            }
            .stat-box .value { font-size: 28px; font-weight: bold; }
            .stat-box .label { font-size: 11px; opacity: 0.7; margin-top: 5px; }
            
            .card {
                background: rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 15px;
                margin-bottom: 12px;
            }
            .card h3 { margin-bottom: 10px; font-size: 16px; }
            
            .xp-bar {
                background: rgba(255,255,255,0.2);
                border-radius: 10px;
                height: 10px;
                margin-top: 10px;
                overflow: hidden;
            }
            .xp-fill {
                background: linear-gradient(90deg, #667eea, #764ba2);
                height: 100%;
                border-radius: 10px;
                transition: width 0.5s;
            }
            
            .btn {
                display: block;
                width: 100%;
                padding: 14px;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                cursor: pointer;
                margin-bottom: 8px;
                font-weight: 600;
                transition: all 0.2s;
            }
            .btn:active { transform: scale(0.98); }
            .btn-primary { background: #667eea; color: white; }
            .btn-success { background: #1cc88a; color: white; }
            .btn-warning { background: #f6c23e; color: #1a1a2e; }
            
            .key-box {
                background: rgba(0,0,0,0.3);
                padding: 12px;
                border-radius: 8px;
                font-family: monospace;
                word-break: break-all;
                font-size: 13px;
                margin-top: 5px;
            }
            
            .achievement {
                display: inline-block;
                background: rgba(255,255,255,0.15);
                padding: 8px 12px;
                border-radius: 20px;
                margin: 4px;
                font-size: 13px;
            }
            
            .nav-tabs {
                display: flex;
                gap: 5px;
                margin-bottom: 15px;
            }
            .nav-tab {
                flex: 1;
                padding: 10px;
                border: none;
                border-radius: 8px;
                background: rgba(255,255,255,0.1);
                color: white;
                cursor: pointer;
                font-size: 13px;
                text-align: center;
            }
            .nav-tab.active { background: #667eea; }
            
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            
            .loader {
                text-align: center;
                padding: 40px;
                opacity: 0.7;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 AI Access Bot</h1>
            <p id="user-name">Загрузка...</p>
        </div>
        
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('profile')">👤 Профиль</button>
            <button class="nav-tab" onclick="showTab('keys')">🔑 Ключи</button>
            <button class="nav-tab" onclick="showTab('sim')">📱 SIM</button>
        </div>
        
        <div id="tab-profile" class="tab-content active">
            <div class="stats-grid" id="stats-grid">
                <div class="stat-box">
                    <div class="value" id="stat-requests">—</div>
                    <div class="label">Запросов</div>
                </div>
                <div class="stat-box">
                    <div class="value" id="stat-level">—</div>
                    <div class="label">Уровень</div>
                </div>
                <div class="stat-box">
                    <div class="value" id="stat-xp">—</div>
                    <div class="label">XP</div>
                </div>
            </div>
            
            <div class="card">
                <h3>Прогресс уровня</h3>
                <div id="level-info">Загрузка...</div>
                <div class="xp-bar">
                    <div class="xp-fill" id="xp-bar-fill" style="width: 0%;"></div>
                </div>
            </div>
            
            <div class="card">
                <h3>🏆 Достижения</h3>
                <div id="achievements-list">Загрузка...</div>
            </div>
            
            <div class="card">
                <h3>Подписки</h3>
                <div id="subscriptions">Загрузка...</div>
            </div>
        </div>
        
        <div id="tab-keys" class="tab-content">
            <div class="card">
                <h3>🔑 AI API Ключи</h3>
                <div id="keys-list">Загрузка...</div>
            </div>
            <button class="btn btn-primary" onclick="getNewKey()">🔄 Сгенерировать новый ключ</button>
        </div>
        
        <div id="tab-sim" class="tab-content">
            <div class="card">
                <h3>📱 SIM Заказы</h3>
                <div id="sim-orders">Загрузка...</div>
            </div>
        </div>
        
        <script>
            const tg = window.Telegram.WebApp;
            const API_URL = window.location.origin;
            let userId = null;
            
            // Инициализация
            tg.ready();
            tg.expand();
            
            // Получаем данные пользователя из Telegram
            if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
                userId = tg.initDataUnsafe.user.id;
                document.getElementById('user-name').textContent = 
                    '👋 ' + tg.initDataUnsafe.user.first_name + 
                    (tg.initDataUnsafe.user.username ? ' (@' + tg.initDataUnsafe.user.username + ')' : '');
                
                loadProfile();
                loadKeys();
                loadSimOrders();
            } else {
                document.getElementById('user-name').textContent = '👋 Гость';
                // Для теста можно ввести ID вручную
                userId = prompt('Введите Telegram ID:');
                if (userId) {
                    loadProfile();
                    loadKeys();
                    loadSimOrders();
                }
            }
            
            function showTab(name) {
                document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
                document.getElementById('tab-' + name).classList.add('active');
                event.target.classList.add('active');
            }
            
            async function loadProfile() {
                try {
                    const response = await fetch(API_URL + '/api/webapp/profile?user_id=' + userId);
                    const data = await response.json();
                    
                    document.getElementById('stat-requests').textContent = data.total_requests || 0;
                    document.getElementById('stat-level').textContent = data.level || 1;
                    document.getElementById('stat-xp').textContent = data.experience || 0;
                    
                    document.getElementById('level-info').innerHTML = 
                        'Уровень ' + (data.level || 1) + ': <b>' + (data.level_name || 'Новичок') + '</b>';
                    
                    document.getElementById('xp-bar-fill').style.width = (data.xp_percent || 0) + '%';
                    
                    // Достижения
                    let achHtml = '';
                    if (data.achievements && data.achievements.length > 0) {
                        data.achievements.forEach(a => {
                            achHtml += '<span class="achievement">' + (a.emoji || '⭐') + ' ' + a.name + '</span>';
                        });
                    } else {
                        achHtml = 'Пока нет достижений';
                    }
                    document.getElementById('achievements-list').innerHTML = achHtml;
                    
                    // Подписки
                    document.getElementById('subscriptions').innerHTML = 
                        '🤖 AI: <b>' + (data.ai_premium ? '✅ Premium' : '❌ Нет') + '</b><br>' +
                        '📱 SIM: <b>' + (data.sim_premium ? '✅ Premium' : '❌ Нет') + '</b>';
                    
                } catch(e) {
                    console.error('Error loading profile:', e);
                }
            }
            
            async function loadKeys() {
                try {
                    const response = await fetch(API_URL + '/api/webapp/keys?user_id=' + userId);
                    const data = await response.json();
                    
                    if (data.keys && data.keys.length > 0) {
                        let html = '';
                        data.keys.forEach(key => {
                            html += '<div class="key-box">' + key + '</div>';
                        });
                        document.getElementById('keys-list').innerHTML = html;
                    } else {
                        document.getElementById('keys-list').innerHTML = 'Нет ключей. Получите AI доступ.';
                    }
                } catch(e) {
                    document.getElementById('keys-list').innerHTML = 'Ошибка загрузки';
                }
            }
            
            async function loadSimOrders() {
                try {
                    const response = await fetch(API_URL + '/api/webapp/sim-orders?user_id=' + userId);
                    const data = await response.json();
                    
                    if (data.orders && data.orders.length > 0) {
                        let html = '';
                        data.orders.forEach(order => {
                            const status = order.status === 'completed' ? '✅' : '⏳';
                            html += '<div style="margin-bottom:8px;">' +
                                status + ' #' + order.order_id + ': ' + order.operator + 
                                ' | ' + order.region + 
                                (order.sim_number ? ' | ' + order.sim_number : '') +
                                '</div>';
                        });
                        document.getElementById('sim-orders').innerHTML = html;
                    } else {
                        document.getElementById('sim-orders').innerHTML = 'Нет заказов';
                    }
                } catch(e) {
                    document.getElementById('sim-orders').innerHTML = 'Ошибка загрузки';
                }
            }
            
            async function getNewKey() {
                try {
                    const response = await fetch(API_URL + '/api/webapp/new-key?user_id=' + userId);
                    const data = await response.json();
                    if (data.key) {
                        loadKeys();
                        tg.showPopup({title: 'Новый ключ', message: data.key});
                    } else {
                        tg.showPopup({title: 'Ошибка', message: 'Не удалось создать ключ'});
                    }
                } catch(e) {
                    tg.showPopup({title: 'Ошибка', message: 'Сервер недоступен'});
                }
            }
            
            // Отправка данных в бота
            function sendToBot(action) {
                tg.sendData(JSON.stringify({action: action}));
                tg.close();
            }
        </script>
    </body>
    </html>
    """


@app.get("/api/webapp/profile")
async def webapp_profile(user_id: int):
    """API для профиля"""
    user = UserModel.get(user_id)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    from config import ACHIEVEMENTS, LEVELS
    import json
    
    progress = LevelSystem.get_progress(user_id)
    achievements = json.loads(user.get('achievements', '[]'))
    achievement_list = []
    for ach_key in achievements:
        ach = ACHIEVEMENTS.get(ach_key, {})
        if ach:
            achievement_list.append({"key": ach_key, "name": ach["name"], "emoji": ach["emoji"]})
    
    level_data = LEVELS.get(user.get('level', 1), LEVELS[1])
    
    return {
        "user_id": user_id,
        "total_requests": user.get('total_requests', 0),
        "level": user.get('level', 1),
        "level_name": level_data["name"],
        "experience": user.get('experience', 0),
        "xp_percent": progress.get('percent', 0),
        "ai_premium": UserModel.is_ai_premium(user_id),
        "sim_premium": UserModel.is_sim_premium(user_id),
        "achievements": achievement_list,
        "referral_bonus": user.get('referral_bonus', 0)
    }


@app.get("/api/webapp/keys")
async def webapp_keys(user_id: int):
    """API для ключей"""
    user = UserModel.get(user_id)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    import json
    keys = json.loads(user.get('api_keys', '[]'))
    return {"keys": keys}


@app.get("/api/webapp/new-key")
async def webapp_new_key(user_id: int):
    """Создать новый ключ"""
    import uuid
    user = UserModel.get(user_id)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    if not UserModel.is_ai_premium(user_id):
        return JSONResponse({"error": "No premium"}, status_code=403)
    
    import json
    keys = json.loads(user.get('api_keys', '[]'))
    new_key = f"sk-pro-{uuid.uuid4().hex[:24]}"
    keys.append(new_key)
    UserModel.update(user_id, {'api_keys': json.dumps(keys)})
    
    return {"key": new_key}


@app.get("/api/webapp/sim-orders")
async def webapp_sim_orders(user_id: int):
    """API для SIM заказов"""
    orders = SimModel.get_user_orders(user_id)
    return {"orders": orders}