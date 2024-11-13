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


storage = MemoryStorage()
bot = Bot(API_TOKEN)
dp = Dispatcher(bot, storage=storage)


async def get_raffle_keyboard(user_id):
    raffle_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    buttons = []
    if not await is_user_in_raffle(user_id):
        buttons.append(KeyboardButton("Розыгрыш"))
    if not await has_user_responses(user_id):
        buttons.append(KeyboardButton("Соц. опрос"))

    if buttons:
        raffle_keyboard.add(*buttons)

    if not buttons:
        return ReplyKeyboardRemove()

    return raffle_keyboard


async def on_start_up(_):
    await db_start()


@dp.message_handler(commands=['res'])
async def poll(message: types.Message):
    if message.from_user.id == ANASTASIA_ID or message.from_user.id == DEV_ID:
        await bot.send_message(message.from_user.id, await get_statistics())


@dp.message_handler(commands=['usr'])
async def cmd_random_user(message: types.Message):
    if message.from_user.id == ANASTASIA_ID or message.from_user.id == DEV_ID:
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


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # Проверка, зарегистрирован ли пользователь
    if await check_user_exists(message.from_user.id):
        await message.answer("Вы уже зарегистрированы!", reply_markup=(await get_raffle_keyboard(message.from_user.id)))
        return

    # Если пользователь не зарегистрирован, запускаем опрос
    await Form.waiting_for_first_name.set()
    await message.answer("Здравствуйте! Введите свое имя.")


@dp.message_handler(state=Form.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await Form.waiting_for_last_name.set()
    await message.answer("Введите свою фамилию.")


@dp.message_handler(state=Form.waiting_for_last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    last_name = message.text

    await save_user(
        message.from_user.id,
        tg_username=message.from_user.username or "",
        tg_phone="",
        tg_first_name=message.from_user.first_name or "",
        tg_last_name=message.from_user.last_name or "",
        first_name=user_data.get('first_name'),
        last_name=last_name
    )

    await state.finish()

    await message.answer(
        "Просим вас пройти опрос для составления портрета селлера, а также приглашаем сделать доброе дело и принять участие в розыгрыше призов!\nВыберите ниже",
        reply_markup=(await get_raffle_keyboard(message.from_user.id))
    )


@dp.message_handler(lambda message: message.text == "Соц. опрос")
async def survey_handler(message: types.Message):
    user_id = message.from_user.id

    if await check_user_exists(user_id):
        if await has_user_responses(user_id):
            await message.answer("Вы уже запустили опрос и не можете начать его заново. Благодарим за участие!", reply_markup=(await get_raffle_keyboard(user_id)))
        else:
            await display_question(user_id, 1)
    else:
        await message.answer("Извините, вы не зарегистрированы. Пожалуйста, зарегистрируйтесь, отправив команду /start")


@dp.message_handler(lambda message: message.text == "Розыгрыш")
async def paid_raffle_handler(message: types.Message):
    user_id = message.from_user.id

    if await check_user_exists(user_id):
        if await is_user_in_raffle(user_id):
            await message.answer("Вы уже участвуете в розыгрыше!", reply_markup=(await get_raffle_keyboard(user_id)))
        else:
            raffle_bot_url = PAID_BOT_LINK
            keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(
                "Перейти к розыгрышу", url=raffle_bot_url))

            await message.answer("Переход к розыгрышу:", reply_markup=keyboard)
    else:
        await message.answer("Извините, вы не зарегистрированы. Пожалуйста, зарегистрируйтесь, отправив команду /start")


async def display_question(chat_id, question_id):
    if await get_total_questions_count() < question_id:
        if await is_user_in_raffle(chat_id):
            await bot.send_message(
                chat_id,
                "Вы ответили на все вопросы. Благодарим Вас!",
                reply_markup=(await get_raffle_keyboard(chat_id))
            )
        else:
            await bot.send_message(
                chat_id,
                "Вы ответили на все вопросы. Благодарим Вас!\n"
                "Приглашаем принять участие в розыгрыше! С условиями Вы можете ознакомиться, "
                "нажав на кнопку ниже «Участие в розыгрыше».",
                reply_markup=(await get_raffle_keyboard(chat_id))
            )
        return

    question_data = await get_question_and_answers(question_id)
    if question_data:
        question_text = question_data['question_text']
        answers = question_data['answers']
        answer_type = question_data['answer_type']
        if answer_type:
            answer_type = True
        else:
            answer_type = False

        poll = await bot.send_poll(
            chat_id=chat_id,
            question=question_text,
            options=answers,
            type='regular',
            allows_multiple_answers=answer_type,
            is_anonymous=False
        )

        await save_poll(poll.poll.id, question_id, poll.message_id)


@dp.poll_answer_handler()
async def handle_poll_answer(answers: types.PollAnswer):
    await add_user_response(answers.user.id, answers.poll_id, answers.option_ids)

    await bot.stop_poll(answers.user.id, await get_message_id_by_poll_id(answers.poll_id))

    question_id = await get_question_id_by_poll_id(answers.poll_id)
    await display_question(answers.user.id, question_id + 1)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_start_up)
