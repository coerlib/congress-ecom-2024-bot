from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import PAID_RAFFLE_BOT_TOKEN, MAIN_BOT_LINK, MODERATOR_ID, DEV_ID
from requests_paid import db_start, get_user_data

bot = Bot(PAID_RAFFLE_BOT_TOKEN)
dp = Dispatcher(bot)


async def on_start_up(_):
    await db_start()


@dp.message_handler(commands=['start'])
async def start_paid_raffle(message: types.Message):
    user = await get_user_data(message.from_user.id)
    if user:
        _, _, _, _, _, first_name, last_name, _, _, _ = user
        await message.answer(f"Добро пожаловать в платный розыгрыш. Для участия отправьте фото, подтверждающее оплату")
    else:
        main_bot_url = MAIN_BOT_LINK
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(
            "Перейти в основной бот", url=main_bot_url))
        await message.answer("Извините, вы не зарегистрированы. Пожалуйста, сначала зарегистрируйтесь в основном боте", reply_markup=keyboard)


@dp.message_handler(content_types=[types.ContentType.DOCUMENT, types.ContentType.PHOTO])
async def handle_payment_confirmation(message: types.Message):
    user_id = message.from_user.id
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

    await bot.send_message(chat_id=user_id, text="Ваше подтверждение оплаты одобрено. Вы участвуете в розыгрыше!")
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

    await bot.send_message(chat_id=user_id, text="Ваше подтверждение оплаты не прошло. Пожалуйста, загрузите другое подтверждение")
    await callback_query.answer("Оплата отклонена")

    # Дублируем сообщение о том, что оплата отклонена на dev_id
    await bot.send_message(chat_id=DEV_ID, text=f"Дубл. Оплата отклонена для пользователя {user_id}.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_start_up)
