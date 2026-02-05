import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import Counter
import os

# Токен вашего Telegram-бота
TOKEN = '7612218514:AAG78sS26TW2ISSNlR5Sgf9qezRl-LTFapU'

# Настройка бота
bot = telebot.TeleBot(TOKEN)

# Рабочая папка с изображениями
IMAGES_FOLDER = './images/'

# Словарь для временных данных пользователей
USER_DATA = {}

# Обработчик команды "/start"
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Введите ключевую фразу для поиска:")

# Основная логика поиска
@bot.message_handler(func=lambda message: True)
def find_by_keywords(message):
    user_id = message.chat.id
    input_phrase = message.text.lower()

    # Парсим введённую фразу на отдельные слова
    input_words = set(input_phrase.split())

    # Подключаемся к базе данных
    conn = sqlite3.connect('instance\database.db')
    cursor = conn.cursor()

    # Извлекаем все записи из таблицы
    cursor.execute("SELECT * FROM equipment_record")
    all_rows = cursor.fetchall()

    # Оценка совпадений
    matching_results = []
    for row in all_rows:
        # Проверяем, что у нас есть достаточное количество элементов в записи
        if len(row) >= 6:
            place, equipment, part, key, description = row[1:]  # Первый элемент — это ID, который мы отбрасываем
            words_in_key = set(key.lower().split())

            # Определяем процент совпадения
            common_words = input_words.intersection(words_in_key)
            match_percentage = len(common_words) / len(input_words) * 100

            if match_percentage >= 50:  # Произвольный порог совпадения
                matching_results.append((row, match_percentage))

    if matching_results:
        # Сортируем по количеству совпадений
        sorted_results = sorted(matching_results, key=lambda x: x[1], reverse=True)

        # Сохраняем результаты для текущего пользователя
        USER_DATA[user_id] = {'matching_results': sorted_results}

        # Если найдено несколько вариантов, даём выбор кнопками
        if len(sorted_results) > 1:
            markup = InlineKeyboardMarkup()
            buttons = []
            for idx, (_, _) in enumerate(sorted_results):
                details = sorted_results[idx][0][4]  # Столбец "Детали"
                button = InlineKeyboardButton(details, callback_data=f"select_{idx}")
                buttons.append(button)
            markup.add(*buttons)

            bot.send_message(user_id, "Несколько вариантов найдено. Выберите интересующий:",
                             reply_markup=markup)
        else:
            show_result(user_id, sorted_results[0][0])
    else:
        bot.send_message(user_id, "Ничего подходящего не найдено. Попробуйте другую фразу.")
    conn.close()

# Обработчик выбора кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_selection(call):
    user_id = call.message.chat.id
    choice_idx = int(call.data.split("_")[1])

    # Восстанавливаем промежуточные данные
    if user_id in USER_DATA and 'matching_results' in USER_DATA[user_id]:
        matching_results = USER_DATA[user_id]['matching_results']
        result_row = matching_results[choice_idx][0]  # Извлекаем саму строку, а не весь кортеж
        show_result(user_id, result_row)
    else:
        bot.send_message(user_id, "Что-то пошло не так. Попробуйте начать сначала.")

# Функция отображения результатов
def show_result(user_id, row):
    # Проверяем, что у нас есть необходимое количество элементов
    if len(row) >= 6:
        place, equipment, part, key, description = row[1:]

        # Проверяем наличие изображения
        filename = extract_filename_from_description(description)
        if filename:
            full_path = IMAGES_FOLDER + filename
            if os.path.isfile(full_path):
                with open(full_path, 'rb') as img_file:
                    bot.send_photo(user_id, img_file)

        # Отображаем основную информацию
        output = f"""
        📍 Место: {place}
        ⚙️ Оборудование: {equipment}
        🛠️ Детали: {part}
        🔑 Ключ: {key}
        ✏️ Описание: {description}
        """
        bot.send_message(user_id, output)
    else:
        bot.send_message(user_id, "Данные повреждены или отсутствуют. Обратитесь к администратору.")

# Извлечение имени файла из описания
def extract_filename_from_description(desc):
    parts = desc.split()
    for word in parts:
        if '.' in word and any(ext in word for ext in ['.jpg', '.png', '.gif']):
            return word.strip()
    return None

# Запуск бота
print("Бот запущен...")
bot.polling(non_stop=True)