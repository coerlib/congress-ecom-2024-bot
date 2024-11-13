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
        raffle_participant INTEGER DEFAULT 0,  -- 1 для участия, 0 для отсутствия, -1 для ожидания проверки
        file_path TEXT
    )''')

    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT,
            answer_type INTEGER CHECK (answer_type IN (0, 1)) DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            answers_index INTEGER,
            answer_text TEXT,
            FOREIGN KEY (question_id) REFERENCES questions (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            message_id INTEGER,
            FOREIGN KEY (question_id) REFERENCES questions (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users_responses (
            user_id INTEGER,
            poll_id INTEGER,
            answers TEXT,
            FOREIGN KEY (poll_id) REFERENCES polls (id)
        )
    """)

    await fill_questions_data()

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


# Проверяет, участвует ли пользователь в платном розыгрыше.
async def is_user_in_raffle(chat_id):
    cur.execute(
        "SELECT raffle_participant FROM users WHERE chat_id = ?", (chat_id,))
    result = cur.fetchone()
    return result is not None and result[0] == 1


# соц опрос
async def add_question(question_text, answer_type=1):
    cur.execute("""
        INSERT INTO questions (question_text, answer_type) VALUES (?, ?)
    """, (question_text, answer_type))
    db.commit()


async def add_answer(question_id, answer_text, answers_index):
    cur.execute("""
        INSERT INTO answers (question_id, answer_text, answers_index) VALUES (?, ?, ?)
    """, (question_id, answer_text, answers_index,))
    db.commit()


async def fill_questions_data():
    cur.execute("SELECT COUNT(*) FROM questions")
    questions_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM answers")
    answers_count = cur.fetchone()[0]

    if questions_count == 0 and answers_count == 0:
        # Вопросы
        await add_question("Ваш пол:", answer_type=0)
        question_id_1 = cur.lastrowid

        await add_question("Ваш возраст:", answer_type=0)
        question_id_2 = cur.lastrowid

        await add_question("Как долго Вы продаете на маркетплейсах?", answer_type=0)
        question_id_3 = cur.lastrowid

        await add_question("Ваш ежемесячный оборот продаж?", answer_type=0)
        question_id_4 = cur.lastrowid

        await add_question("Какую категорию товара Вы продаете? (можно несколько вариантов)", answer_type=1)
        question_id_5 = cur.lastrowid

        await add_question("Кто производит товары, которые Вы продаете?", answer_type=0)
        question_id_6 = cur.lastrowid

        await add_question("Время, которое Вы тратите в день для работы с маркетплейсами:", answer_type=0)
        question_id_7 = cur.lastrowid

        await add_question("Кто занимается работой в Вашем личном кабинете на маркетплейсе?", answer_type=0)
        question_id_8 = cur.lastrowid

        await add_question("Является ли для вас работа с МП полной занятостью или вы совмещаете с другой деятельностью?", answer_type=0)
        question_id_9 = cur.lastrowid

        await add_question("Что Вы считаете самым важным для успешных продаж на маркетплейсах, исходя из своего опыта? (можно несколько вариантов)", answer_type=1)
        question_id_10 = cur.lastrowid

        await add_question("Используете ли Вы услуги по упаковке своего товара (фулфилмент)?", answer_type=0)
        question_id_11 = cur.lastrowid

        await add_question("Пользовались ли вы когда-то помощью Центра Мой бизнес?", answer_type=0)
        question_id_12 = cur.lastrowid

        # Варианты ответов
        await add_answer(question_id_1, "мужской", 0)
        await add_answer(question_id_1, "женский", 1)

        await add_answer(question_id_2, "до 20 лет", 0)
        await add_answer(question_id_2, "20-30 лет", 1)
        await add_answer(question_id_2, "30-45 лет", 2)
        await add_answer(question_id_2, "старше 45 лет", 3)

        await add_answer(question_id_3, "пока не продаю", 0)
        await add_answer(question_id_3, "меньше 1 года", 1)
        await add_answer(question_id_3, "от 1 года до 2 лет", 2)
        await add_answer(question_id_3, "от 2 до 5 лет", 3)
        await add_answer(question_id_3, "больше 5 лет", 4)

        await add_answer(question_id_4, "меньше 100 тысяч рублей", 0)
        await add_answer(question_id_4, "от 100 до 500 тысяч рублей", 1)
        await add_answer(question_id_4, "от 500 тысяч до 1 миллиона рублей", 2)
        await add_answer(question_id_4, "от 1 миллиона до 3 миллионов рублей", 3)
        await add_answer(question_id_4, "свыше 3 миллионов рублей", 4)

        await add_answer(question_id_5, "дом и сад", 0)
        await add_answer(question_id_5, "товары для автомобиля", 1)
        await add_answer(question_id_5, "электроника и техника", 2)
        await add_answer(question_id_5, "детские товары", 3)
        await add_answer(question_id_5, "косметика, парфюмерия", 4)
        await add_answer(question_id_5, "канцтовары, хобби, книги", 5)
        await add_answer(question_id_5, "одежда и обувь", 6)
        await add_answer(question_id_5, "продукты питания", 7)
        await add_answer(question_id_5, "товары для животных", 8)

        await add_answer(question_id_6, "самостоятельно на своем производстве", 0)
        await add_answer(question_id_6, "российские поставщики (по индивидуальному заказу)", 1)
        await add_answer(question_id_6, "российские поставщики (закупаем готовую продукцию)", 2)
        await add_answer(question_id_6, "зарубежные поставщики (по индивидуальному заказу)", 3)
        await add_answer(question_id_6, "зарубежные поставщики (закупаем готовую продукцию)", 4)

        await add_answer(question_id_7, "меньше 1 часа", 0)
        await add_answer(question_id_7, "от 1 до 3 часов", 1)
        await add_answer(question_id_7, "от 3 до 5 часов", 2)
        await add_answer(question_id_7, "более 5 часов", 3)

        await add_answer(question_id_8, "самостоятельно", 0)
        await add_answer(question_id_8, "менеджер", 1)

        await add_answer(question_id_9, "полная занятость", 0)
        await add_answer(question_id_9, "совмещаю", 1)

        await add_answer(question_id_10, "выбор категории", 0)
        await add_answer(question_id_10, "анализ продаж и ведение статистики", 1)
        await add_answer(question_id_10, "контент, публикуемый в карточке (описание и фото)", 2)
        await add_answer(question_id_10, "работа с отзывами", 3)
        await add_answer(question_id_10, "настройка рекламы", 4)
        await add_answer(question_id_10, "распределение товара в разные города", 5)
        await add_answer(question_id_10, "ценообразование", 6)

        await add_answer(question_id_11, "да, всегда использую", 0)
        await add_answer(question_id_11, "нет, самостоятельно упаковываю", 1)
        await add_answer(question_id_11, "использую только при больших поставках", 2)

        await add_answer(question_id_12, "да", 0)
        await add_answer(question_id_12, "нет", 1)


async def save_poll(id, question_id, message_id):
    cur.execute("""
        INSERT INTO polls (id, question_id, message_id) VALUES (?, ?, ?)
    """, (id, question_id, message_id))
    db.commit()


async def get_question_text_by_id(question_id):
    cur.execute("""
        SELECT question_text FROM questions WHERE id = ?
    """, (question_id,))

    question_text = cur.fetchone()

    if question_text:
        return question_text[0]
    else:
        return None


async def get_total_questions_count():
    cur.execute("""
        SELECT COUNT(*) FROM questions
    """)

    count = cur.fetchone()[0]
    return count


async def add_user_response(user_id, poll_id, option_ids):
    answers = ','.join(map(str, option_ids))

    cur.execute("""
        SELECT * FROM users_responses WHERE user_id = ? AND poll_id = ? AND answers = ?
    """, (user_id, poll_id, answers))

    existing_response = cur.fetchone()

    if not existing_response:
        cur.execute("""
            INSERT INTO users_responses (user_id, poll_id, answers) VALUES (?, ?, ?)
        """, (user_id, poll_id, answers))
        db.commit()
        return True
    else:
        return False


async def get_question_and_answers(question_id):
    cur.execute("""
        SELECT id, question_text, answer_type FROM questions WHERE id = ?
    """, (question_id,))

    question_data = cur.fetchone()

    if question_data:
        question_id, question_text, answer_type = question_data

        cur.execute("""
            SELECT id, answer_text, answers_index FROM answers WHERE question_id = ?
        """, (question_id,))

        answers_data = cur.fetchall()

        answers = [ans[1] for ans in answers_data]

        return {'question_text': question_text, 'answer_type': answer_type, 'answers': answers}
    else:
        return None


async def get_user_responses(user_id):
    # Получаем все записи ответов пользователя из базы данных
    cur.execute("""
        SELECT pr.poll_id, pr.answers, q.id AS question_id
        FROM users_responses AS pr
        JOIN polls AS p ON pr.poll_id = p.id
        JOIN questions AS q ON p.question_id = q.id
        WHERE pr.user_id = ?
    """, (user_id,))

    user_responses = cur.fetchall()

    # Формируем ответ в нужном формате
    formatted_responses = []
    for poll_id, answers, question_id in user_responses:
        answers_list = answers.split(',')

        # Получаем текст вопроса
        cur.execute("""
            SELECT question_text FROM questions WHERE id = ?
        """, (question_id,))
        question_text = cur.fetchone()[0]

        # Получаем тексты ответов по индексам
        answer_texts = []
        for answer_index in answers_list:
            cur.execute("""
                SELECT answer_text FROM answers WHERE question_id = ? AND answers_index = ?
            """, (question_id, int(answer_index)))
            answer_texts.append(cur.fetchone()[0])

        formatted_responses.append(
            {'question_text': question_text, 'answer_texts': answer_texts})

    return formatted_responses


async def get_question_id_by_poll_id(poll_id):
    cur.execute("""
        SELECT question_id FROM polls WHERE id = ?
    """, (poll_id,))

    question_id = cur.fetchone()[0]
    return question_id


async def get_total_participants():
    cur.execute("""
        SELECT COUNT(DISTINCT user_id) FROM users_responses
    """)
    total_participants = cur.fetchone()[0]
    return total_participants


async def get_responses_count_by_question_id(question_id):
    cur.execute("""
        SELECT COUNT(*) FROM answers
        WHERE question_id = ?
    """, (question_id,))
    responses_count = cur.fetchone()[0]
    return responses_count


async def get_message_id_by_poll_id(poll_id):
    cur.execute("""
        SELECT message_id FROM polls WHERE id = ?
    """, (poll_id,))

    message_id = cur.fetchone()[0]
    return message_id


async def get_answer_text_by_question_and_index(question_id, answer_index):
    cur.execute("""
        SELECT answer_text
        FROM answers
        WHERE question_id = ? AND answers_index = ?
    """, (question_id, answer_index))

    answer_text = cur.fetchone()

    if answer_text:
        return answer_text[0]
    else:
        return None


async def has_user_responses(user_id):
    cur.execute("""
        SELECT 1
        FROM users_responses
        WHERE user_id = ?
        LIMIT 1
    """, (user_id,))

    result = cur.fetchone()

    return bool(result)


async def get_answer_counts_by_question_id(question_id):
    cur.execute("""
        SELECT answers
        FROM users_responses
        WHERE poll_id IN (SELECT id FROM polls WHERE question_id = ?)
    """, (question_id,))

    answers_data = cur.fetchall()

    all_answers = [answer for sublist in answers_data for answer in sublist]
    indices_lists = [answers.split(',') for answers in all_answers]
    all_indices = [index for sublist in indices_lists for index in sublist]
    answer_counts = {index: all_indices.count(
        index) for index in set(all_indices)}

    sorted_answer_counts = dict(
        sorted(answer_counts.items(), key=lambda item: int(item[0])))
    sorted_answer_array = [{"index": index, "count": count}
                           for index, count in sorted_answer_counts.items()]
    return sorted_answer_array


async def get_statistics():
    result_string = ""
    users_count = await get_total_participants()

    for i in range(1, 1 + await get_total_questions_count()):
        question_id = i
        result_string += f"[{i}] Вопрос: {await get_question_text_by_id(question_id)}\n"
        answer_counts = await get_answer_counts_by_question_id(question_id)

        answer_array = []
        for item in answer_counts:
            index = item['index']
            answer_text = await get_answer_text_by_question_and_index(question_id, index)
            answer_array.append(
                {'index': index, 'answer_text': answer_text, 'count': item['count']})

        max_index = await get_responses_count_by_question_id(question_id) - 1

        for index in range(max_index + 1):
            if not any(item['index'] == str(index) for item in answer_array):
                answer_text = await get_answer_text_by_question_and_index(question_id, index)
                answer_array.append(
                    {'index': index, 'answer_text': answer_text, 'count': 0})

        answer_array = sorted(answer_array, key=lambda x: int(x['index']))

        for item in answer_array:
            percentage = item['count'] / users_count * 100
            result_string += f"{item['index']}) Ответ: {item['answer_text']} => количество: {item['count']} из {users_count} ({percentage:.2f}%)\n"
        result_string += "\n"
    return result_string
