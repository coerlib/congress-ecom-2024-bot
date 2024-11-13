from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import PAID_RAFFLE_BOT_TOKEN, MAIN_BOT_LINK, MODERATOR_ID, DEV_ID
from requests_paid import *


class Form(StatesGroup):
    waiting_for_phone = State()


storage = MemoryStorage()
bot = Bot(PAID_RAFFLE_BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)


async def on_start_up(_):
    await db_start()


@dp.message_handler(commands=['start'])
async def start_paid_raffle(message: types.Message):
    user = await get_user_data(message.from_user.id)
    if user:
        _, _, tg_phone, _, _, last_name, first_name, _, _, _ = user
        # Проверяем участие в розыгрыше
        if await is_user_in_raffle(message.from_user.id):
            await message.answer(
                "Вы уже участвуете в розыгрыше призов! Для помощи детям Курской области Вы можете осуществить перевод повторно по ссылке.\n\n"
                "Ссылка для оплаты:\n"
                "http://sberbank.com/sms/shpa/?cs=602497483482&psh=p&did=1730468347468000418\n\n"
                "Благодарим Вас!\n"
                "#Мойдобрыйбизнес"
            )
        else:
            if tg_phone == "":
                await Form.waiting_for_phone.set()
                phone_button = KeyboardButton(
                    "Отправить номер телефона", request_contact=True)
                keyboard = ReplyKeyboardMarkup(
                    resize_keyboard=True).add(phone_button)

                await message.answer(f"{first_name}, добро пожаловать! Введите Ваш номер телефона.", reply_markup=keyboard)
            else:
                await message.answer(
                    f"Мы предлагаем Вам помочь детям Курской области и перевести любую сумму в Благотворительный фонд.\n"
                    "Для участия в розыгрыше направьте чек в виде документа, подтверждающий оплату.\n\n"
                    "Ссылка для оплаты:\n"
                    "http://sberbank.com/sms/shpa/?cs=602497483482&psh=p&did=1730468347468000418\n\n"
                    "#Мойдобрыйбизнес"
                )
    else:
        main_bot_url = MAIN_BOT_LINK
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(
            "Перейти в основной бот", url=main_bot_url))
        await message.answer("Извините, вы не зарегистрированы. Пожалуйста, сначала зарегистрируйтесь в основном боте", reply_markup=keyboard)


@dp.message_handler(content_types=types.ContentTypes.CONTACT, state=Form.waiting_for_phone)
async def process_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await update_user_phone(message.from_user.id, phone)

    await message.answer(
        f"Мы предлагаем Вам помочь детям Курской области и перевести любую сумму в Благотворительный фонд.\n"
        "Для участия в розыгрыше направьте чек в виде документа, подтверждающий оплату.\n\n"
        "Ссылка для оплаты:\n"
        "http://sberbank.com/sms/shpa/?cs=602497483482&psh=p&did=1730468347468000418\n\n"
        "#Мойдобрыйбизнес"
    )
    await state.finish()


@dp.message_handler(state=Form.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text
    await update_user_phone(message.from_user.id, phone)

    await message.answer(
        f"Мы предлагаем Вам помочь детям Курской области и перевести любую сумму в Благотворительный фонд.\n"
        "Для участия в розыгрыше направьте чек в виде документа, подтверждающий оплату.\n\n"
        "Ссылка для оплаты:\n"
        "http://sberbank.com/sms/shpa/?cs=602497483482&psh=p&did=1730468347468000418\n\n"
        "#Мойдобрыйбизнес"
    )
    await state.finish()


@dp.message_handler(content_types=[types.ContentType.DOCUMENT, types.ContentType.PHOTO])
async def handle_payment_confirmation(message: types.Message):
    user_id = message.from_user.id

    # Проверяем, участвует ли пользователь в розыгрыше
    if await is_user_in_raffle(user_id):
        main_bot_url = MAIN_BOT_LINK
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Перейти в основной бот", url=main_bot_url))
        await message.answer("Вы уже участвуете в розыгрыше", reply_markup=keyboard)
        return
    elif await is_user_waiting_for_approval(user_id):
        await message.answer("Ваше подтверждение на проверке, пожалуйста, ожидайте ответа от модератора.")
        return

    if message.content_type == types.ContentType.PHOTO:
        # Получаем наибольшее качество фото
        file_id = message.photo[-1].file_id
        sent_message = await bot.send_photo(chat_id=MODERATOR_ID, photo=file_id, caption=f"‼️ Подтверждение оплаты ({user_id})")

        # Дублируем фото на dev_id
        await bot.send_photo(chat_id=DEV_ID, photo=file_id, caption=f"Дубл. Подтверждение оплаты ({user_id})")
    else:
        file_id = message.document.file_id
        sent_message = await bot.send_document(chat_id=MODERATOR_ID, document=file_id, caption=f"‼️ Подтверждение оплаты ({user_id})")

        # Дублируем документ на dev_id
        await bot.send_document(chat_id=DEV_ID, document=file_id, caption=f"Дубл. Подтверждение оплаты ({user_id})")

    await message.answer("Ваш файл отправлен на проверку")

    # Отмечаем, что пользователь ожидает проверки
    await mark_user_waiting_for_approval(user_id)

    approval_keyboard = InlineKeyboardMarkup()
    approval_keyboard.row(
        InlineKeyboardButton(
            "ОК", callback_data=f"approve:{user_id}:{sent_message.message_id}"),
        InlineKeyboardButton(
            "Не ОК", callback_data=f"reject:{user_id}:{sent_message.message_id}")
    )

    await bot.send_message(chat_id=MODERATOR_ID, text=f"Оцените подтверждение оплаты ({user_id})", reply_markup=approval_keyboard)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('approve:'))
async def approve_payment(callback_query: types.CallbackQuery):
    _, user_id, message_id = callback_query.data.split(":")

    # Изменяем текст сообщения с файлом или фото
    await bot.edit_message_caption(chat_id=MODERATOR_ID, message_id=int(message_id), caption="Подтверждение оплаты одобрено")

    # Удаляем сообщение с кнопками
    await callback_query.message.delete()

    # Отметить пользователя как участника розыгрыша
    await mark_user_in_raffle(user_id)

    main_bot_url = MAIN_BOT_LINK
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(
        "Перейти в основной бот", url=main_bot_url))
    await bot.send_message(chat_id=user_id, text="Ваше подтверждение оплаты одобрено. Вы участвуете в розыгрыше!", reply_markup=keyboard)
    await callback_query.answer("Оплата одобрена")

    # Дублируем сообщение о том, что оплата одобрена на dev_id
    await bot.send_message(chat_id=DEV_ID, text=f"Дубл. Оплата одобрена для пользователя {user_id}.")


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('reject:'))
async def reject_payment(callback_query: types.CallbackQuery):
    _, user_id, message_id = callback_query.data.split(":")

    # Изменяем текст сообщения с файлом или фото
    await bot.edit_message_caption(chat_id=MODERATOR_ID, message_id=int(message_id), caption="Подтверждение оплаты отклонено")

    # Удаляем сообщение с кнопками
    await callback_query.message.delete()

    # Снимаем статус ожидания (ставим на 0)
    await reset_user_raffle_status(user_id)

    await bot.send_message(chat_id=user_id, text="Ваше подтверждение оплаты не прошло. Пожалуйста, загрузите другое подтверждение")
    await callback_query.answer("Оплата отклонена")

    # Дублируем сообщение о том, что оплата отклонена на dev_id
    await bot.send_message(chat_id=DEV_ID, text=f"Дубл. Оплата отклонена для пользователя {user_id}.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_start_up)
