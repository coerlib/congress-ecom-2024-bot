from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import *
from requests import *


bot = Bot(RANDOM_BOT_TOKEN)
dp = Dispatcher(bot)


async def on_start_up(_):
    await db_start()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button = KeyboardButton("Проведение розыгрыша")
    keyboard.add(button)
    await message.answer("Для начала розыгрыша нажмите на кнопку ниже:", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Проведение розыгрыша")
async def cmd_random_user(message: types.Message):
    user = await select_random_raffle_user()
    if user:
        user_id, tg_username, tg_phone, tg_first_name, tg_last_name, last_name, first_name, phone, _, _ = user

        if tg_phone:
            masked_phone = '*' * (len(tg_phone) - 4) + tg_phone[-4:]
        else:
            masked_phone = "не указан"

        response = (
            f"Имя: {first_name}\n"
            f"Фамилия: {last_name}\n"
            f"Телефон: {masked_phone}"
        )
    else:
        response = "Пользователи не найдены."
    await message.answer(response)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_start_up)
