import sqlite3

def initiate_db():
    with sqlite3.connect('products.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                price INTEGER NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                age INTEGER NOT NULL,
                balance INTEGER NOT NULL DEFAULT 1000
            )
        ''')
        conn.commit()

def get_all_products():
    with sqlite3.connect('products.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT title, description, price FROM Products')
        return cursor.fetchall()

def add_user(username, email, age):
    with sqlite3.connect('products.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Users (username, email, age, balance) VALUES (?, ?, ?, ?)',
                       (username, email, age, 1000))
        conn.commit()

def is_included(username):
    with sqlite3.connect('products.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM Users WHERE username = ?', (username,))
        return cursor.fetchone()[0] > 0


import telebot
from telebot import types
from telebot.handler_backends import State, StatesGroup
from telebot import storage
from crud_functions import initiate_db, get_all_products, add_user, is_included

TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
bot = telebot.TeleBot(TOKEN)

# Инициализация базы данных
initiate_db()


# Создание класса для состояний регистрации
class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()


# Создание главной клавиатуры
main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
buy_button = types.KeyboardButton("Купить")
register_button = types.KeyboardButton("Регистрация")
main_keyboard.add(buy_button, register_button)


# Функция для отправки списка продуктов
def get_buying_list(message):
    products = get_all_products()

    for product in products:
        title, description, price = product
        bot.send_message(message.chat.id,
                         f'Название: {title} | Описание: {description} | Цена: {price}')
        # Здесь замените 'image_url' на фактический URL изображения продукта
        # bot.send_photo(message.chat.id, 'image_url')

    # Создание Inline клавиатуры
    inline_keyboard = types.InlineKeyboardMarkup()
    for product in products:
        title, _, _ = product
        button = types.InlineKeyboardButton(title, callback_data="product_buying")
        inline_keyboard.add(button)

    bot.send_message(message.chat.id, "Выберите продукт для покупки:", reply_markup=inline_keyboard)


# Хэндлер для кнопки "Купить"
@bot.message_handler(func=lambda message: message.text == "Купить")
def handle_buy(message):
    get_buying_list(message)


# Хэндлер для кнопки "Регистрация"
@bot.message_handler(func=lambda message: message.text == "Регистрация")
def sing_up(message):
    bot.send_message(message.chat.id, "Введите имя пользователя (только латинский алфавит):")
    bot.set_state(message.from_user.id, RegistrationState.username)


# Хэндлер для состояния username
@bot.message_handler(state=RegistrationState.username)
def set_username(message):
    if not message.text.isalpha():
        bot.send_message(message.chat.id, "Имя пользователя должно содержать только латинские буквы. Попробуйте снова.")
        return

    if is_included(message.text):
        bot.send_message(message.chat.id, "Пользователь существует, введите другое имя.")
    else:
        bot.set_state(message.from_user.id, RegistrationState.email)
        bot.send_message(message.chat.id, "Введите свой email:")


# Хэндлер для состояния email
@bot.message_handler(state=RegistrationState.email)
def set_email(message):
    bot.set_state(message.from_user.id, RegistrationState.age)
    bot.send_message(message.chat.id, "Введите свой возраст:")


# Хэндлер для состояния age
@bot.message_handler(state=RegistrationState.age)
def set_age(message):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Возраст должен быть целым числом. Введите свой возраст снова:")
        return

    username = bot.get_state(message.from_user.id, RegistrationState.username)
    email = bot.get_state(message.from_user.id, RegistrationState.email)

    add_user(username, email, message.text)
    bot.send_message(message.chat.id, "Вы успешно зарегистрированы!")
    bot.finish_state(message.from_user.id)  # Завершает состояние


# Хэндлер для callback_data
@bot.callback_query_handler(func=lambda call: call.data == "product_buying")
def send_confirm_message(call):
    bot.answer_callback_query(call.id)  # Убирает вращающийся значок на кнопке
    bot.send_message(call.message.chat.id, "Вы успешно приобрели продукт!")


bot.polling()
