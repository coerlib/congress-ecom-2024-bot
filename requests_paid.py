import sqlite3 as sq


async def db_start():
    global db, cur

    # Подключаемся к базе данных
    db = sq.connect('data.db')
    cur = db.cursor()


# Получение данных пользователя по его ID
async def get_user_data(user_id):
    cur.execute("SELECT * FROM users WHERE chat_id = ?", (user_id,))
    return cur.fetchone()


# Отмечает, что пользователь участвует в платном розыгрыше
async def mark_user_in_raffle(chat_id, file_path=None):
    cur.execute(
        "UPDATE users SET raffle_participant = 1, file_path = ? WHERE chat_id = ?",
        (file_path, chat_id)
    )
    db.commit()


# Проверяет, участвует ли пользователь в платном розыгрыше.
async def is_user_in_raffle(chat_id):
    cur.execute(
        "SELECT raffle_participant FROM users WHERE chat_id = ?", (chat_id,))
    result = cur.fetchone()
    return result is not None and result[0] == 1
