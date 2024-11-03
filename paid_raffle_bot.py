from aiogram import Bot, Dispatcher, executor, types
from config import *
from requests_paid import *


# Инициализация бота и диспетчера
bot = Bot(PAID_RAFFLE_BOT_TOKEN)
dp = Dispatcher(bot)


async def on_start_up(_):
    await db_start()


@dp.message_handler(commands=['start'])
async def start_paid_raffle(message: types.Message):
    # Проверяем, зарегистрирован ли пользователь в базе данных
    user = await get_user_data(message.from_user.id)
    if user:
        _, _, _, _, _, first_name, last_name, _, _, _ = user
        await message.answer(f"Привет, {first_name} {last_name}! Добро пожаловать в платный розыгрыш.")
    else:
        await message.answer("Извините, вы не зарегистрированы. Пожалуйста, сначала зарегистрируйтесь в основном боте.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_start_up)
