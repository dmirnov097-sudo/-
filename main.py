import telebot
import json
import datetime
import random
from threading import Thread
from telebot import types
import time

# ============ КОНФИГУРАЦИЯ ============
KEY_BOT_TOKEN = "8230694505:AAGWElZG_1SG2ITduvbmW2yNxNCJSqabr7A"
KEY_BOT_USERNAME = "@Fnsndkskfkkddkbot"

GAME_BOT_TOKEN = "8352745659:AAGcMu4ukwTxKMHb465_FtfZQorSLnMiMzw"
GAME_BOT_USERNAME = "@Teleamtaninbot"

ADMIN_ID = 8562793772

# Увеличенные суммы
INITIAL_COINS = 100000  # 100,000 вместо 100
VIP_BONUS_COINS = 500000  # 500,000 вместо 500

# Тарифы покупки (увеличенные)
STARS_TO_COINS = {
    15: 100000,      # 15 звёзд = 100,000 койнов
    30: 250000,      # 30 звёзд = 250,000 койнов
    60: 600000,      # 60 звёзд = 600,000 койнов
    150: 1500000,    # 150 звёзд = 1,500,000 койнов
    300: 3500000     # 300 звёзд = 3,500,000 койнов
}

# Цены игр (соразмерно увеличенному балансу)
GAME_PRICES = {
    "football": 1000,
    "basketball": 1000,
    "dice": 500,
    "bowling": 500,
    "darts": 500,
    "casino": 2000,
    "slot": 1500
}

# Файлы для хранения данных
KEYS_FILE = "keys.json"
USERS_FILE = "users.json"
PURCHASES_FILE = "purchases.json"

# Создаем ботов
key_bot = telebot.TeleBot(KEY_BOT_TOKEN)
game_bot = telebot.TeleBot(GAME_BOT_TOKEN)

# ============ ХРАНЕНИЕ ДАННЫХ ============
def load_data(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        if filename == KEYS_FILE:
            return {"keys": [], "used_keys": []}
        elif filename == PURCHASES_FILE:
            return {"purchases": []}
        else:
            return {"users": []}

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Загружаем данные
keys_data = load_data(KEYS_FILE)
users_data = load_data(USERS_FILE)
purchases_data = load_data(PURCHASES_FILE)

# ============ ФУНКЦИИ ДЛЯ КЛЮЧЕЙ И КОИНОВ ============
def generate_key(key_type="regular"):
    import random
    import string
    
    if key_type == "vip":
        prefix = "VIP"
        length = 16
    else:
        prefix = "REG"
        length = 12
    
    chars = string.ascii_uppercase + string.digits
    key = prefix + "-" + ''.join(random.choice(chars) for _ in range(length))
    
    keys_data["keys"].append({
        "key": key,
        "type": key_type,
        "generated": datetime.datetime.now().isoformat(),
        "used": False,
        "used_by": None,
        "used_at": None
    })
    save_data(KEYS_FILE, keys_data)
    
    return key

def validate_key(key):
    for k in keys_data["keys"]:
        if k["key"] == key and not k["used"]:
            return k["type"]
    return None

def use_key(key, user_id):
    for k in keys_data["keys"]:
        if k["key"] == key:
            k["used"] = True
            k["used_by"] = user_id
            k["used_at"] = datetime.datetime.now().isoformat()
            save_data(KEYS_FILE, keys_data)
            
            initial_balance = INITIAL_COINS
            if k["type"] == "vip":
                initial_balance += VIP_BONUS_COINS
            
            users_data["users"].append({
                "user_id": user_id,
                "username": "",
                "key_type": k["type"],
                "coins": initial_balance,
                "total_coins_earned": initial_balance,
                "activated_at": datetime.datetime.now().isoformat(),
                "total_wins": 0,
                "total_games": 0,
                "last_daily": None,
                "total_purchased": 0
            })
            save_data(USERS_FILE, users_data)
            return True, initial_balance
    return False, 0

def get_user_type(user_id):
    for user in users_data["users"]:
        if user["user_id"] == user_id:
            return user["key_type"]
    return None

def get_user_data(user_id):
    for user in users_data["users"]:
        if user["user_id"] == user_id:
            return user
    return None

def update_user_coins(user_id, amount, source="game"):
    for user in users_data["users"]:
        if user["user_id"] == user_id:
            old_balance = user["coins"]
            new_balance = max(0, user["coins"] + amount)
            user["coins"] = new_balance
            
            if amount > 0 and source == "purchase":
                user["total_purchased"] = user.get("total_purchased", 0) + amount
                user["total_coins_earned"] = user.get("total_coins_earned", 0) + amount
            
            save_data(USERS_FILE, users_data)
            return old_balance, new_balance
    return None, None

def add_game_played(user_id):
    for user in users_data["users"]:
        if user["user_id"] == user_id:
            user["total_games"] = user.get("total_games", 0) + 1
            save_data(USERS_FILE, users_data)
            return user["total_games"]
    return None

def add_win(user_id):
    for user in users_data["users"]:
        if user["user_id"] == user_id:
            user["total_wins"] = user.get("total_wins", 0) + 1
            save_data(USERS_FILE, users_data)
            return user["total_wins"]
    return None

def give_daily_coins(user_id):
    user = get_user_data(user_id)
    if not user:
        return 0
    
    today = datetime.datetime.now().date().isoformat()
    
    if user.get("last_daily") == today:
        return 0
    
    daily_coins = 5000  # 5,000 вместо 50
    if user["key_type"] == "vip":
        daily_coins = 10000  # 10,000 вместо 100
    
    update_user_coins(user_id, daily_coins, "daily")
    user["last_daily"] = today
    save_data(USERS_FILE, users_data)
    
    return daily_coins

def record_purchase(user_id, stars_amount, coins_amount):
    purchase = {
        "user_id": user_id,
        "stars": stars_amount,
        "coins": coins_amount,
        "date": datetime.datetime.now().isoformat(),
        "status": "completed"
    }
    
    purchases_data["purchases"].append(purchase)
    save_data(PURCHASES_FILE, purchases_data)
    return purchase

# ============ КЛАВИАТУРЫ ============
def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if user_id == ADMIN_ID:
        markup.add(
            types.KeyboardButton("🔑 Получить ключ"),
            types.KeyboardButton("⭐ VIP ключ")
        )
        markup.add(
            types.KeyboardButton("💰 Купить койны"),
            types.KeyboardButton("📊 Статистика")
        )
        markup.add(
            types.KeyboardButton("👥 Все пользователи"),
            types.KeyboardButton("🎮 Игровой бот")
        )
        markup.add(
            types.KeyboardButton("⚙️ Админ панель"),
            types.KeyboardButton("❓ Помощь")
        )
    else:
        markup.add(
            types.KeyboardButton("🔑 Получить ключ"),
            types.KeyboardButton("📊 Статистика")
        )
        markup.add(
            types.KeyboardButton("💰 Купить койны"),
            types.KeyboardButton("🎁 Ежедневный бонус")
        )
        markup.add(
            types.KeyboardButton("🎮 Игровой бот"),
            types.KeyboardButton("💳 Мой баланс")
        )
        markup.add(
            types.KeyboardButton("❓ Помощь")
        )
    
    return markup

def get_games_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add(
        types.KeyboardButton("⚽ Футбол"),
        types.KeyboardButton("🏀 Баскетбол"),
        types.KeyboardButton("🎲 Кости")
    )
    markup.add(
        types.KeyboardButton("🎳 Боулинг"),
        types.KeyboardButton("🎯 Дартс"),
        types.KeyboardButton("🎰 Казино")
    )
    markup.add(
        types.KeyboardButton("🎰 Слоты"),
        types.KeyboardButton("💰 Баланс"),
        types.KeyboardButton("📊 Статистика")
    )
    markup.add(
        types.KeyboardButton("⭐ Купить койны"),
        types.KeyboardButton("🎁 Ежедневный бонус"),
        types.KeyboardButton("❓ Помощь")
    )
    markup.add(
        types.KeyboardButton("🔙 В главное меню")
    )
    return markup

def get_bet_keyboard(game_name):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    price = GAME_PRICES.get(game_name, 1000)
    
    markup.add(
        types.KeyboardButton(f"🎯 Ставка {price:,} койнов"),
        types.KeyboardButton(f"💰 Ставка {price*2:,} койнов"),
        types.KeyboardButton(f"💎 Ставка {price*5:,} койнов")
    )
    markup.add(
        types.KeyboardButton("🔙 Назад к играм"),
        types.KeyboardButton("❌ Отмена")
    )
    return markup

def get_purchase_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("⭐ 15 звёзд → 100,000 койнов"),
        types.KeyboardButton("⭐ 30 звёзд → 250,000 койнов")
    )
    markup.add(
        types.KeyboardButton("⭐ 60 звёзд → 600,000 койнов"),
        types.KeyboardButton("⭐ 150 звёзд → 1,500,000 койнов")
    )
    markup.add(
        types.KeyboardButton("⭐ 300 звёзд → 3,500,000 койнов"),
        types.KeyboardButton("🔙 Назад")
    )
    return markup

def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("✅ Полный сброс"),
        types.KeyboardButton("👤 Сброс по ID")
    )
    markup.add(
        types.KeyboardButton("💰 Пополнить баланс"),
        types.KeyboardButton("📊 Статистика")
    )
    markup.add(
        types.KeyboardButton("⬅️ Назад в меню"),
        types.KeyboardButton("❌ Отмена")
    )
    return markup

def get_confirmation_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("✅ Да, купить"),
        types.KeyboardButton("❌ Нет, отмена")
    )
    return markup

def get_back_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("⬅️ Назад"))
    return markup

# ============ ФУНКЦИИ ДЛЯ ИГР ============
def get_football_result(dice_value):
    results = {
        1: "❌ Мяч улетел на трибуны! Промах...",
        2: "❌ Удар в штангу! Почти, но не попал.",
        3: "❌ Вратарь поймал мяч! Отличный сейв.",
        4: "❌ Мяч пролетел мимо ворот...",
        5: "❌ Блок защитника! Мяч отбит.",
        6: "✅ ГООООЛ! Идеальный удар в девятку! ⚽"
    }
    return results.get(dice_value, "Неизвестный результат")

def get_basketball_result(dice_value):
    results = {
        1: "❌ Мяч не долетел до кольца...",
        2: "❌ Удар об дужку кольца!",
        3: "❌ Мяч отскочил от щита...",
        4: "❌ Кружётся на ободе и вылетает!",
        5: "✅ Отличный бросок! 2 очка! 🏀",
        6: "✅ Трехочковый! Идеальный бросок! 🏀⭐"
    }
    return results.get(dice_value, "Неизвестный результат")

# ============ БОТ ДЛЯ ПОЛУЧЕНИЯ КЛЮЧЕЙ ============
@key_bot.message_handler(commands=['start'])
def key_start(message):
    user = message.from_user
    welcome_text = f"""
🔑 *Бот для получения ключей* 🔑

Привет, {user.first_name}! 

💰 *Система койнов:*
• Получайте койны за активацию
• Покупайте койны за звёзды Telegram
• Играйте на койны в играх
• Выигрывайте и увеличивайте баланс

📌 *Используйте кнопки ниже:*
• 🔑 Получить ключ (100,000 койнов)
• ⭐ VIP ключ (600,000 койнов)
• 💰 Купить койны за звёзды
• 📊 Статистика
"""
    key_bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(user.id)
    )

@key_bot.message_handler(func=lambda message: message.text == "🔑 Получить ключ")
def handle_get_key(message):
    user_id = message.from_user.id
    
    key = generate_key("regular")
    
    response = f"""
✅ *Обычный ключ успешно создан!*

🔑 *Ваш ключ:* `{key}`
💰 *Бонус:* *{INITIAL_COINS:,} койнов*

⚠️ *Важная информация:*
• Ключ действует для одного аккаунта
• Активируйте его в игровом боте
• Начальный баланс: {INITIAL_COINS:,} койнов

📋 *Инструкция по активации:*
1. Нажмите кнопку "🎮 Игровой бот"
2. Или перейдите: {GAME_BOT_USERNAME}
3. Введите ключ: `{key}`
4. Начинайте играть!
"""
    key_bot.send_message(message.chat.id, response, parse_mode='Markdown')

@key_bot.message_handler(func=lambda message: message.text == "⭐ VIP ключ")
def handle_vip_key(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        key_bot.send_message(message.chat.id, "❌ *Доступ запрещен!*\nТолько администратор может генерировать VIP ключи.", parse_mode='Markdown')
        return
    
    key = generate_key("vip")
    total_coins = INITIAL_COINS + VIP_BONUS_COINS
    
    response = f"""
⭐ *VIP ключ успешно создан!*

🔑 *VIP ключ:* `{key}`
💰 *Бонус:* *{total_coins:,} койнов* (VIP)

🎁 *VIP преимущества:*
• {VIP_BONUS_COINS:,} дополнительных койнов
• Двойные выигрыши в играх
• Приоритетная поддержка
• Ежедневный бонус 10,000 койнов
"""
    key_bot.send_message(message.chat.id, response, parse_mode='Markdown')

@key_bot.message_handler(func=lambda message: message.text == "💰 Купить койны")
def handle_buy_coins_menu(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        key_bot.send_message(message.chat.id, "❌ *Сначала активируйте ключ в игровом боте!*", parse_mode='Markdown')
        return
    
    purchase_text = """
⭐ *Покупка койнов за звёзды Telegram*

*Тарифы:*
• 15 звёзд → 100,000 койнов
• 30 звёзд → 250,000 койнов
• 60 звёзд → 600,000 койнов
• 150 звёзд → 1,500,000 койнов
• 300 звёзд → 3,500,000 койнов

💡 *Как купить:*
1. Выберите тариф
2. Оплатите через Telegram Stars
3. Койны начислятся автоматически

⚠️ *Оплата проходит через защищенную систему Telegram*
"""
    key_bot.send_message(
        message.chat.id,
        purchase_text,
        parse_mode='Markdown',
        reply_markup=get_purchase_keyboard()
    )

# Обработка нажатия на кнопки покупки
@key_bot.message_handler(func=lambda message: message.text.startswith("⭐ ") and "→" in message.text)
def handle_purchase_selection(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        key_bot.send_message(message.chat.id, "❌ *Сначала активируйте ключ!*", parse_mode='Markdown')
        return
    
    # Извлекаем данные из текста кнопки
    parts = message.text.replace("⭐ ", "").split(" → ")
    stars_part = parts[0].replace(" звёзд", "")
    coins_part = parts[1].replace(" койнов", "").replace(",", "")
    
    try:
        stars = int(stars_part)
        coins = int(coins_part)
    except ValueError:
        key_bot.send_message(message.chat.id, "❌ *Ошибка формата тарифа*", parse_mode='Markdown')
        return
    
    # Сохраняем выбор покупки
    purchase_data = {
        "user_id": user_id,
        "stars": stars,
        "coins": coins
    }
    
    # Показываем кнопку для оплаты через Telegram Stars
    markup = types.InlineKeyboardMarkup()
    pay_button = types.InlineKeyboardButton(
        text=f"💳 Оплатить {stars} звёзд",
        pay=True
    )
    demo_button = types.InlineKeyboardButton(
        text="🔄 Демо-оплата (тест)",
        callback_data=f"demo_pay_{stars}_{coins}_{user_id}"
    )
    cancel_button = types.InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel_purchase"
    )
    markup.add(pay_button)
    markup.add(demo_button, cancel_button)
    
    confirmation_text = f"""
💳 *Оплата койнов*

*Вы выбрали:*
• Тариф: {stars} звёзд
• Получите: {coins:,} койнов

💰 *Текущий баланс:* {user_data['coins']:,} койнов
💰 *После покупки:* {user_data['coins'] + coins:,} койнов

*Для оплаты нажмите кнопку ниже ⬇️*
"""
    
    key_bot.send_message(
        message.chat.id,
        confirmation_text,
        parse_mode='Markdown',
        reply_markup=markup
    )

# Обработка callback-запросов для демо-оплаты
@key_bot.callback_query_handler(func=lambda call: call.data.startswith('demo_pay_'))
def handle_demo_payment(call):
    try:
        data_parts = call.data.split('_')
        stars = int(data_parts[2])
        coins = int(data_parts[3])
        user_id = int(data_parts[4])
        
        # Проверяем, что это тот же пользователь
        if call.from_user.id != user_id:
            key_bot.answer_callback_query(call.id, "❌ Недостаточно прав!", show_alert=True)
            return
        
        # Начисляем койны
        old_balance, new_balance = update_user_coins(user_id, coins, "purchase")
        record_purchase(user_id, stars, coins)
        
        # Уведомляем администратора
        admin_message = f"""
🔄 *Демо-покупка койнов*

👤 Пользователь: @{call.from_user.username or call.from_user.first_name}
🆔 ID: {user_id}

⭐ Звёзд: {stars}
💰 Койнов: {coins:,}
💳 Баланс: {new_balance:,} койнов

⚠️ *Это демо-транзакция*
"""
        key_bot.send_message(ADMIN_ID, admin_message, parse_mode='Markdown')
        
        # Уведомляем пользователя
        success_text = f"""
✅ *Покупка успешно завершена!*

⭐ Оплачено: {stars} звёзд (демо)
💰 Получено: {coins:,} койнов

💳 *Ваш баланс:*
• Было: {old_balance:,} койнов
• Стало: {new_balance:,} койнов

🎮 Теперь вы можете играть и выигрывать!
"""
        key_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=success_text,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        key_bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)}", show_alert=True)

@key_bot.callback_query_handler(func=lambda call: call.data == "cancel_purchase")
def handle_cancel_purchase(call):
    key_bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="❌ *Покупка отменена*",
        parse_mode='Markdown'
    )

# Обработка pre_checkout_query для реальной оплаты
@key_bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    key_bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Обработка успешной оплаты
@key_bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    user_id = message.from_user.id
    payment_info = message.successful_payment
    
    # Ищем соответствующий тариф
    for stars, coins in STARS_TO_COINS.items():
        # Здесь должна быть логика сопоставления суммы оплаты с тарифом
        # В демо-версии используем первый подходящий тариф
        if payment_info.total_amount // 100 == stars:  # stars в копейках/центах
            old_balance, new_balance = update_user_coins(user_id, coins, "purchase")
            record_purchase(user_id, stars, coins)
            
            success_text = f"""
✅ *Оплата успешно принята!*

⭐ Оплачено: {stars} звёзд
💰 Получено: {coins:,} койнов

💳 *Ваш баланс:*
• Было: {old_balance:,} койнов
• Стало: {new_balance:,} койнов

🎮 Приятной игры!
"""
            key_bot.send_message(
                message.chat.id,
                success_text,
                parse_mode='Markdown',
                reply_markup=get_main_keyboard(user_id)
            )
            break

@key_bot.message_handler(func=lambda message: message.text == "💳 Мой баланс")
def handle_my_balance(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data:
        balance = user_data.get("coins", 0)
        purchased = user_data.get("total_purchased", 0)
        earned = user_data.get("total_coins_earned", 0)
        
        response = f"""
💰 *Ваш баланс:*

🪙 *Койны:* {balance:,}

📊 *Статистика:*
• Всего получено: {earned:,} койнов
• Куплено за звёзды: {purchased:,} койнов
• Игр сыграно: {user_data.get('total_games', 0)}
• Побед: {user_data.get('total_wins', 0)}
"""
    else:
        response = "❌ *Вы еще не активировали ключ!*\nПолучите ключ и активируйте его в игровом боте."
    
    key_bot.send_message(message.chat.id, response, parse_mode='Markdown')

@key_bot.message_handler(func=lambda message: message.text == "🎁 Ежедневный бонус")
def handle_daily_bonus(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        key_bot.send_message(message.chat.id, "❌ *Сначала активируйте ключ в игровом боте!*", parse_mode='Markdown')
        return
    
    bonus = give_daily_coins(user_id)
    
    if bonus > 0:
        new_balance = get_user_data(user_id).get("coins", 0)
        response = f"""
🎁 *Ежедневный бонус получен!*

💰 +{bonus:,} койнов
💳 Новый баланс: {new_balance:,} койнов

🔄 Следующий бонус через 24 часа!
"""
    else:
        response = """
⏰ *Вы уже получали бонус сегодня!*

Приходите за новым бонусом завтра.
"""
    
    key_bot.send_message(message.chat.id, response, parse_mode='Markdown')

@key_bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def handle_stats(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    user_keys = [k for k in keys_data["keys"] if k["used_by"] == user_id]
    user_data = get_user_data(user_id)
    
    if user_data:
        stats_text = f"""
📊 *Ваша статистика* 📊

👤 *Пользователь:* {username}
🆔 *ID:* `{user_id}`

💰 *Финансы:*
• Баланс: {user_data.get('coins', 0):,} койнов
• Всего получено: {user_data.get('total_coins_earned', 0):,} койнов
• Куплено: {user_data.get('total_purchased', 0):,} койнов

🎮 *Игры:*
• Сыграно игр: {user_data.get('total_games', 0)}
• Побед: {user_data.get('total_wins', 0)}
"""
    else:
        stats_text = f"""
📊 *Статистика* 📊

👤 *Пользователь:* {username}
🆔 *ID:* `{user_id}`

❌ *Ключ не активирован!*
Для получения статистики активируйте ключ в игровом боте.
"""
    
    key_bot.send_message(message.chat.id, stats_text, parse_mode='Markdown')

@key_bot.message_handler(func=lambda message: message.text == "🎮 Игровой бот")
def handle_game_bot_link(message):
    response = f"""
🎮 *Переход в игровой бот*

Чтобы активировать ключ и начать играть:

1. Нажмите на ссылку ниже
2. Введите полученный ключ
3. Выбирайте игры и играйте на койны!

👉 *Перейти:* {GAME_BOT_USERNAME}

💰 *Система койнов:*
• Ставьте койны в играх
• Выигрывайте и увеличивайте баланс
• Покупайте койны за звёзды
"""
    key_bot.send_message(message.chat.id, response, parse_mode='Markdown')

# ============ ИГРОВОЙ БОТ ============
@game_bot.message_handler(commands=['start'])
def game_start(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data:
        welcome_text = f"""
🎮 *Добро пожаловать в игровой бот!* 🎮

👋 Привет, {message.from_user.first_name}!
💰 Баланс: *{user_data['coins']:,} койнов*
✅ Статус: *{'VIP 🎁' if user_data['key_type'] == 'vip' else 'Обычный ✨'}*

🎯 *Выбирайте игру и делайте ставки!*
⚽ Футбол, 🏀 Баскетбол и другие игры
"""
        game_bot.send_message(
            message.chat.id, 
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=get_games_keyboard()
        )
    else:
        welcome_text = f"""
🎮 *Игровой бот* 🎮

Привет, {message.from_user.first_name}! 

🔒 *Требуется активация!*
Для доступа к играм необходим ключ.

🔑 *Как получить ключ:*
1. Перейдите в бот: {KEY_BOT_USERNAME}
2. Получите ключ с койнами
3. Вернитесь сюда и введите ключ

💰 *Вы получите начальные койны!*
⚽ Играйте и выигрывайте больше!

📝 *Просто введите ваш ключ в этот чат*
Пример: `REG-ABC123DEF456`
"""
        game_bot.send_message(
            message.chat.id, 
            welcome_text, 
            parse_mode='Markdown'
        )

@game_bot.message_handler(func=lambda message: len(message.text) > 10 and '-' in message.text)
def activate_key(message):
    user_id = message.from_user.id
    key = message.text.strip()
    
    key_type = validate_key(key)
    
    if key_type:
        success, initial_coins = use_key(key, user_id)
        if success:
            user_data = get_user_data(user_id)
            
            success_text = f"""
🎉 *Поздравляем!* 🎉

✅ *Ключ успешно активирован!*
🔑 Тип: *{'VIP 🎁' if key_type == 'vip' else 'Обычный ✨'}*
💰 Начальный баланс: *{initial_coins:,} койнов*

🎮 *Теперь вам доступны все игры!*
Делайте ставки и выигрывайте койны!
"""
            game_bot.send_message(
                message.chat.id, 
                success_text, 
                parse_mode='Markdown',
                reply_markup=get_games_keyboard()
            )
        else:
            game_bot.send_message(message.chat.id, "❌ *Ошибка активации!*\nКлюч уже использован.", parse_mode='Markdown')
    else:
        game_bot.send_message(message.chat.id, "❌ *Неверный ключ!*\nПроверьте правильность ввода или получите новый ключ.", parse_mode='Markdown')

# Обработчики игр
@game_bot.message_handler(func=lambda message: message.text == "🏀 Баскетбол")
def basketball_game(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        game_bot.send_message(message.chat.id, "🔒 *Требуется активация!*\nВведите ключ для доступа к играм.", parse_mode='Markdown')
        return
    
    game_info = """
🏀 *БАСКЕТБОЛ - Броски*

*Правила:*
• Выбираете размер ставки
• Бросаете мяч в кольцо
• За 2 очка получаете ×1.5 ставки
• За 3 очка получаете ×3 ставки
• За промах теряете ставку

---

*Шанс попасть:* 1 из 3  
*Стоимость игры:* 1,000 койнов
"""
    game_bot.send_message(
        message.chat.id,
        game_info,
        parse_mode='Markdown',
        reply_markup=get_bet_keyboard("basketball")
    )

@game_bot.message_handler(func=lambda message: message.text == "⚽ Футбол")
def football_game(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        game_bot.send_message(message.chat.id, "🔒 *Требуется активация!*\nВведите ключ для доступа к играм.", parse_mode='Markdown')
        return
    
    game_info = """
⚽ *ФУТБОЛ - Пенальти*

*Правила:*
• Выбираете размер ставки
• Бьете пенальти
• За гол получаете ×2 ставки
• За промах теряете ставку

---

*Шанс попасть:* 1 из 6  
*Стоимость игры:* 1,000 койнов
"""
    game_bot.send_message(
        message.chat.id,
        game_info,
        parse_mode='Markdown',
        reply_markup=get_bet_keyboard("football")
    )

@game_bot.message_handler(func=lambda message: message.text == "🎰 Слоты")
def slots_game(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        game_bot.send_message(message.chat.id, "🔒 *Требуется активация!*\nВведите ключ для доступа к играм.", parse_mode='Markdown')
        return
    
    game_info = """
🎰 *ИГРОВЫЕ АВТОМАТЫ*

*Правила:*
• Выбираете размер ставки
• Вращайте барабаны
• Сочетания символов дают выигрыши
• Максимальный выигрыш ×10

---

*Стоимость игры:* 1,500 койнов
"""
    game_bot.send_message(
        message.chat.id,
        game_info,
        parse_mode='Markdown',
        reply_markup=get_bet_keyboard("slot")
    )

# Обработка ставок
@game_bot.message_handler(func=lambda message: any(x in message.text for x in ["Ставка", "койнов"]) and "→" not in message.text)
def handle_bet_selection(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        return
    
    # Извлекаем сумму ставки
    import re
    match = re.search(r'(\d[\d,]*)', message.text.replace(",", ""))
    if not match:
        return
    
    bet_amount = int(match.group(1))
    
    # Проверяем баланс
    if user_data["coins"] < bet_amount:
        game_bot.send_message(
            message.chat.id,
            f"❌ *Недостаточно койнов!*\n💰 Ваш баланс: {user_data['coins']:,} койнов\n💸 Нужно: {bet_amount:,} койнов",
            parse_mode='Markdown',
            reply_markup=get_games_keyboard()
        )
        return
    
    # Определяем игру по контексту
    if "🏀" in message.text or "Баскетбол" in message.text:
        game_type = "basketball"
    elif "⚽" in message.text or "Футбол" in message.text:
        game_type = "football"
    elif "🎰" in message.text or "Слоты" in message.text:
        game_type = "slot"
    else:
        game_type = "dice"
    
    # Играем
    play_game_with_bet(message, game_type, bet_amount)

def play_game_with_bet(message, game_type, bet_amount):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data or user_data["coins"] < bet_amount:
        return False
    
    # Списание ставки
    old_balance, new_balance = update_user_coins(user_id, -bet_amount, "game")
    add_game_played(user_id)
    
    if game_type == "basketball":
        game_bot.send_message(message.chat.id, "🏀 *Бросаю мяч...*", parse_mode='Markdown')
        msg = game_bot.send_dice(message.chat.id, emoji='🏀')
        time.sleep(3)
        
        dice_value = msg.dice.value
        result_text = get_basketball_result(dice_value)
        
        win_amount = 0
        multiplier = 1
        
        if dice_value == 5:
            win_amount = int(bet_amount * 1.5)
            multiplier = 1.5
        elif dice_value == 6:
            win_amount = bet_amount * 3
            multiplier = 3
        
    elif game_type == "football":
        game_bot.send_message(message.chat.id, "⚽ *Бью пенальти...*", parse_mode='Markdown')
        msg = game_bot.send_dice(message.chat.id, emoji='⚽')
        time.sleep(3)
        
        dice_value = msg.dice.value
        result_text = get_football_result(dice_value)
        
        win_amount = 0
        multiplier = 1
        
        if dice_value == 6:
            win_amount = bet_amount * 2
            multiplier = 2
    
    else:
        # Для других игр - простой результат
        win_amount = bet_amount * random.choice([0, 0, 0, 0.5, 1, 2, 3, 5, 10])
        multiplier = win_amount / bet_amount if bet_amount > 0 else 0
        result_text = f"🎰 *Игра завершена!*\nМножитель: ×{multiplier:.1f}"
    
    # VIP бонус
    if win_amount > 0 and user_data["key_type"] == "vip":
        win_amount = int(win_amount * 1.5)
        multiplier *= 1.5
        result_text += "\n⭐ *VIP бонус: ×1.5 к выигрышу!*"
        add_win(user_id)
    elif win_amount > 0:
        add_win(user_id)
    
    # Начисляем выигрыш
    if win_amount > 0:
        final_old, final_new = update_user_coins(user_id, win_amount, "game")
        
        result_message = f"""
{result_text}

💰 *Ставка:* {bet_amount:,} койнов
🎯 *Множитель:* ×{multiplier:.1f}
🎁 *Выигрыш:* {win_amount:,} койнов

💳 *Баланс:*
• Было: {new_balance:,} койнов
• Стало: {final_new:,} койнов
"""
    else:
        result_message = f"""
{result_text}

💰 *Ставка:* {bet_amount:,} койнов
❌ *Вы проиграли ставку*

💳 *Текущий баланс:* {new_balance:,} койнов
"""
    
    game_bot.send_message(
        message.chat.id,
        result_message,
        parse_mode='Markdown',
        reply_markup=get_games_keyboard()
    )
    
    return True

# Остальные обработчики
@game_bot.message_handler(func=lambda message: message.text == "⭐ Купить койны")
def game_buy_coins(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        game_bot.send_message(message.chat.id, "❌ *Сначала активируйте ключ!*", parse_mode='Markdown')
        return
    
    purchase_text = """
⭐ *Покупка койнов за звёзды Telegram*

*Тарифы:*
• 15 звёзд → 100,000 койнов
• 30 звёзд → 250,000 койнов
• 60 звёзд → 600,000 койнов
• 150 звёзд → 1,500,000 койнов
• 300 звёзд → 3,500,000 койнов

💡 *Как купить:*
1. Выберите тариф
2. Оплатите через Telegram Stars
3. Койны начислятся автоматически
"""
    game_bot.send_message(
        message.chat.id,
        purchase_text,
        parse_mode='Markdown',
        reply_markup=get_purchase_keyboard()
    )

@game_bot.message_handler(func=lambda message: message.text == "💰 Баланс")
def game_balance(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data:
        response = f"""
💰 *Ваш игровой баланс:*

🪙 *Койны:* {user_data['coins']:,}

📊 *Статистика игр:*
• Сыграно: {user_data.get('total_games', 0)}
• Побед: {user_data.get('total_wins', 0)}
• Тип: {'VIP ⭐' if user_data['key_type'] == 'vip' else 'Обычный'}
"""
    else:
        response = "❌ *Сначала активируйте ключ!*"
    
    game_bot.send_message(message.chat.id, response, parse_mode='Markdown')

@game_bot.message_handler(func=lambda message: message.text in ["🔙 В главное меню", "🔙 Назад к играм", "🔙 Назад"])
def back_buttons(message):
    game_start(message)

# ============ ЗАПУСК БОТОВ ============
def run_key_bot():
    print(f"🔑 Бот для ключей запущен: @{key_bot.get_me().username}")
    key_bot.infinity_polling()

def run_game_bot():
    print(f"🎮 Игровой бот запущен: @{game_bot.get_me().username}")
    game_bot.infinity_polling()

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ЗАПУСК СИСТЕМЫ БОТОВ С РЕАЛЬНОЙ ОПЛАТОЙ")
    print("=" * 60)
    print(f"🔑 Бот для ключей: {KEY_BOT_USERNAME}")
    print(f"🎮 Игровой бот: {GAME_BOT_USERNAME}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("=" * 60)
    print("💰 УВЕЛИЧЕННЫЕ СУММЫ:")
    print(f"• Начальный баланс: {INITIAL_COINS:,} койнов")
    print(f"• VIP бонус: +{VIP_BONUS_COINS:,} койнов")
    print("• Ежедневный бонус: 5,000-10,000 койнов")
    print("=" * 60)
    print("⭐ СИСТЕМА ПОКУПКИ ЗА ЗВЁЗДЫ:")
    print("• 15 звёзд → 100,000 койнов")
    print("• 30 звёзд → 250,000 койнов")
    print("• 60 звёзд → 600,000 койнов")
    print("• 150 звёзд → 1,500,000 койнов")
    print("• 300 звёзд → 3,500,000 койнов")
    print("=" * 60)
    print("🎮 ИГРЫ:")
    print("• Ставки: 1,000 - 5,000 койнов")
    print("• Выигрыши: до ×10 ставки")
    print("• VIP бонус: ×1.5 к выигрышам")
    print("=" * 60)
    
    thread1 = Thread(target=run_key_bot)
    thread2 = Thread(target=run_game_bot)
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()