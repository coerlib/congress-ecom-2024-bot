from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import *
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
    await message.answer("Здравствуйте! Введите своё имя")


# todo ограничить доступ к функции
@dp.message_handler(commands=['random_user'])
async def cmd_random_user(message: types.Message):
    user = await select_random_user()
    if user:
        user_id, tg_username, tg_phone, tg_first_name, tg_last_name, first_name, last_name, phone, _, _ = user

        # Маскируем номер телефона
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


@dp.message_handler(state=Form.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await Form.waiting_for_last_name.set()
    await message.answer("Введи свою фамилию")


@dp.message_handler(state=Form.waiting_for_last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await Form.waiting_for_phone.set()
    phone_button = KeyboardButton(
        "Отправить номер телефона", request_contact=True)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(phone_button)
    await message.answer("Нажмите на кнопку или введите номер телефона текстом:", reply_markup=keyboard)


# Создаем клавиатуру с кнопками "Платный розыгрыш" и "Соц опрос"
menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
menu_keyboard.add(KeyboardButton("Платный розыгрыш"))
menu_keyboard.add(KeyboardButton("Соц опрос"))


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
    await message.answer("Спасибо за регистрацию! Вы участвуете в розыгрыше", reply_markup=menu_keyboard)
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
    await message.answer("Спасибо за регистрацию! Вы участвуете в розыгрыше", reply_markup=menu_keyboard)
    await state.finish()


# Добавляем обработчик для кнопки "Платный розыгрыш"
@dp.message_handler(lambda message: message.text == "Платный розыгрыш")
async def paid_raffle_handler(message: types.Message):
    if await check_user_exists(message.from_user.id):
        raffle_bot_url = PAID_BOT_LINK
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(
            "Перейти к платному розыгрышу", url=raffle_bot_url))

        await message.answer("Переход к платному розыгрышу:", reply_markup=keyboard)
    else:
        await message.answer("Извините, вы не зарегистрированы. Пожалуйста, зарегистрируйтесь, отправив команду /start")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_start_up)
