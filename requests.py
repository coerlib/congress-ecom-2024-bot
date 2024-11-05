import sqlite3 as sq
import random


async def db_start():
    global db, cur

    # Подключаемся к базе данных
    db = sq.connect('data.db')
    cur = db.cursor()

    # Создаем таблицу для пользователей
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        tg_username TEXT,
        tg_phone TEXT,
        tg_first_name TEXT,
        tg_last_name TEXT,
        last_name TEXT,
        first_name TEXT,
        phone TEXT,
        raffle_participant INTEGER DEFAULT 0,  -- 1 для участия, 0 для отсутствия
        file_path TEXT
    )''')

    # Создаем таблицу для вопросов соц опроса
    cur.execute('''CREATE TABLE IF NOT EXISTS survey_questions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL
    )''')

    # Создаем таблицу для ответов на вопросы соц опроса
    cur.execute('''CREATE TABLE IF NOT EXISTS survey_answers (
        answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        answer_text TEXT NOT NULL,
        question_id INTEGER,
        FOREIGN KEY (question_id) REFERENCES survey_questions(question_id)
    )''')

    # Создаем таблицу для ответов пользователей в соц опросе
    cur.execute('''CREATE TABLE IF NOT EXISTS user_survey_responses (
        response_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        answer_id INTEGER,
        FOREIGN KEY (question_id) REFERENCES survey_questions(question_id),
        FOREIGN KEY (answer_id) REFERENCES survey_answers(answer_id)
    )''')

    # Сохраняем изменения в базе данных
    db.commit()


# Сохраняет нового пользователя в таблицу users, если его ещё нет
async def save_user(chat_id, tg_username=None, tg_phone=None, tg_first_name=None, tg_last_name=None, last_name=None, first_name=None, phone=None):
    cur.execute('''INSERT OR IGNORE INTO users (chat_id, tg_username, tg_phone, tg_first_name, tg_last_name, last_name, first_name, phone)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (chat_id, tg_username, tg_phone, tg_first_name, tg_last_name, last_name, first_name, phone))
    db.commit()


async def check_user_exists(user_id):
    query = "SELECT 1 FROM users WHERE chat_id = ? LIMIT 1"
    cur.execute(query, (user_id,))
    return cur.fetchone() is not None


# Выбирает случайного пользователя из всех пользователей
async def select_random_user():
    cur.execute("SELECT * FROM users ORDER BY RANDOM() LIMIT 1")
    return cur.fetchone()


# Выбирает случайного пользователя, участвующего в платном розыгрыше
async def select_random_raffle_user():
    cur.execute(
        "SELECT * FROM users WHERE raffle_participant = 1 ORDER BY RANDOM() LIMIT 1")
    return cur.fetchone()


# Записывает вопросы и возможные ответы для соц опроса из массива данных
async def save_questions_and_answers(questions_with_answers):
    """
    Формат данных:
    [
        ("Вопрос 1", ["Ответ 1", "Ответ 2", "Ответ 3"]),
        ("Вопрос 2", ["Ответ 1", "Ответ 2", "Ответ 3"]),
        ("Вопрос 3", ["Ответ 1", "Ответ 2", "Ответ 3"]),
    ]
    """
    for question_text, answers in questions_with_answers:
        # Сохраняем вопрос
        cur.execute(
            "INSERT INTO survey_questions (question_text) VALUES (?)", (question_text,))
        question_id = cur.lastrowid

        # Сохраняем ответы
        for answer_text in answers:
            cur.execute(
                "INSERT INTO survey_answers (answer_text, question_id) VALUES (?, ?)", (answer_text, question_id))

    db.commit()


# Сохраняет ответ пользователя на конкретный вопрос
async def save_user_response(user_id, question_id, answer_id):
    cur.execute("INSERT INTO user_survey_responses (question_id, answer_id) VALUES (?, ?)",
                (question_id, answer_id))
    db.commit()


# Проверяет, начал ли пользователь проходить опрос (ответил хотя бы на один вопрос)
async def has_started_survey(user_id):
    cur.execute(
        "SELECT 1 FROM user_survey_responses WHERE response_id = ?", (user_id,))
    return cur.fetchone() is not None


# Проверяет, прошел ли пользователь опрос (ответил на все вопросы)
async def has_completed_survey(user_id):
    # Получаем количество вопросов и количество ответов пользователя
    cur.execute("SELECT COUNT(*) FROM survey_questions")
    total_questions = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(DISTINCT question_id) FROM user_survey_responses WHERE user_id = ?", (user_id,))
    answered_questions = cur.fetchone()[0]

    return answered_questions == total_questions


# Собирает статистику по каждому вопросу и количеству ответов на них
async def get_survey_statistics():
    statistics = {}

    # Получаем все вопросы
    cur.execute("SELECT question_id, question_text FROM survey_questions")
    questions = cur.fetchall()

    for question_id, question_text in questions:
        # Получаем все ответы на текущий вопрос
        cur.execute(
            "SELECT answer_text FROM survey_answers WHERE question_id = ?", (question_id,))
        answers = cur.fetchall()

        # Получаем количество ответов для каждого ответа
        statistics[question_text] = {}
        for answer_text in answers:
            answer_text = answer_text[0]  # Извлекаем текст ответа
            cur.execute("SELECT COUNT(*) FROM user_survey_responses WHERE question_id = ? AND answer_id = (SELECT answer_id FROM survey_answers WHERE answer_text = ? AND question_id = ?)",
                        (question_id, answer_text, question_id))
            count = cur.fetchone()[0]
            statistics[question_text][answer_text] = count

    # Рассчитываем проценты
    for question_text, answers in statistics.items():
        total_responses = sum(answers.values())
        for answer_text, count in answers.items():
            percentage = (count / total_responses *
                          100) if total_responses > 0 else 0
            answers[answer_text] = (count, round(
                percentage, 2))  # (количество, процент)

    return statistics
