from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import API_TOKEN
from requests import *


class Form(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_phone = State()


storage = MemoryStorage()
bot = Bot(API_TOKEN)
dp = Dispatcher(bot, storage=storage)


async def on_start_up(_):
    await db_start()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # Проверка, зарегистрирован ли пользователь
    if await check_user_exists(message.from_user.id):
        await message.answer("Вы уже зарегистрированы!", reply_markup=ReplyKeyboardRemove())
        return

    # Если пользователь не зарегистрирован, запускаем опрос
    await Form.waiting_for_first_name.set()
    await message.answer("Привет! Пожалуйста, введи своё имя.")


@dp.message_handler(state=Form.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await Form.waiting_for_last_name.set()
    await message.answer("Спасибо! Теперь введи свою фамилию.")


@dp.message_handler(state=Form.waiting_for_last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await Form.waiting_for_phone.set()
    phone_button = KeyboardButton(
        "Отправить номер телефона", request_contact=True)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(phone_button)
    await message.answer("Отлично! Нажми на кнопку или введи номер телефона текстом:", reply_markup=keyboard)


@dp.message_handler(content_types=types.ContentTypes.CONTACT, state=Form.waiting_for_phone)
async def process_contact(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    phone = message.contact.phone_number
    await save_user(
        message.from_user.id,
        tg_username=message.from_user.username or "",
        tg_phone=phone,
        tg_first_name=message.from_user.first_name or "",
        tg_last_name=message.from_user.last_name or "",
        first_name=user_data.get('first_name'),
        last_name=user_data.get('last_name')
    )
    await message.answer("Спасибо за регистрацию! Ваши данные сохранены.", reply_markup=ReplyKeyboardRemove())
    await state.finish()


@dp.message_handler(state=Form.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    phone = message.text
    await save_user(
        message.from_user.id,
        tg_username=message.from_user.username or "",
        tg_phone=phone,
        tg_first_name=message.from_user.first_name or "",
        tg_last_name=message.from_user.last_name or "",
        first_name=user_data.get('first_name'),
        last_name=user_data.get('last_name')
    )
    await message.answer("Спасибо за регистрацию! Ваши данные сохранены.", reply_markup=ReplyKeyboardRemove())
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_start_up)
