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
