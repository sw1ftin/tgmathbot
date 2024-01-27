import asyncio
import logging
import wolframalpha
from translate import Translator
from configparser import ConfigParser
from tinydb import TinyDB, Query

from aiogram import Bot, Dispatcher, Router
from aiogram.dispatcher import router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

db = TinyDB('database.json')
table = db.table('Users modes')
User = Query()

keyboard_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Wolfram Alpha', callback_data='wolfram')],
    [InlineKeyboardButton(text='AI', callback_data='ai')]
])

translator = Translator(to_lang='ru', from_lang='en')

router = Router()


def get_answer(mode: str, question: str) -> str:
    match(mode):
        case 'wolfram':
            return '\n'.join([elem.text for elem in list(wolfram_client.query(question).results)])
        case 'ai':
            return 'Ответ ИИ'
    logging.error(f'Something went wrong on question: {question}')
    return 'Произошла ошибка. Повторите попытку позже'


@router.message(Command("start"))
async def start_handler(msg: Message):
    print('New user:', msg.from_user.id)
    await msg.answer_sticker(sticker='CAACAgIAAxkBAAEoJEplcvI8vYOFxhCjj4W9fsb50Y570gACPBMAAoElyUsiXeSDccqJwzME')
    await msg.answer("Привет!")
    await msg.answer("Я помогу тебе решить любое математическое выражение, просто отправь мне его")


@router.message(Command("mode"))
async def start_handler(msg: Message, state: FSMContext):
    await state.update_data(user_id=msg.from_user.id)
    await msg.answer("Выберите режим работы:", reply_markup=keyboard_markup)


@router.callback_query(lambda c: c.data in ['wolfram', 'ai'])
async def process_callback_button(callback_query: CallbackQuery, state: FSMContext):
    mode = callback_query.data

    data = await state.get_data()
    user_id = data.get("user_id")
    find_user = table.search(User.ID == str(user_id))
    
    if len(find_user) > 0:
        table.update({'mode': str(mode)}, User.ID == str(user_id))
    else:
        table.insert({'ID': str(user_id), 'mode': str(mode)})

    await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id,
                                text=f"Вы успешно сменили режим на {mode.upper()}")


@router.message()
async def message_handler(msg: Message):
    try:
        try:
            mode = table.search(User.ID == str(msg.from_user.id))[0]['mode']
        except IndexError:
            table.insert({'ID' : str(msg.from_user.id), 'mode': 'wolfram'})
            mode = 'wolfram'

        ans = get_answer(mode, msg.text)

        await msg.answer(f"Решение:\n{ans}")
    except:
        logging.error(f"AnswerError {mode} {msg.text}")
        await msg.answer(f"К сожалению, произошла ошибка. Повторите попытку позже")


async def main():
    global bot
    bot = Bot(token=token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    config = ConfigParser()
    config.read('config.ini')
    app_id = config.get('wolfram', 'app_id')
    token = config.get('telegram', 'token')

    if app_id and token:
        wolfram_client = wolframalpha.Client(app_id)
        logging.basicConfig(level=logging.INFO)
        asyncio.run(main())
    else:
        error = []
        if not app_id: error.append('app_id')
        if not token: error.append('token')
        raise ValueError(f"Fill {' and '.join(error)} fields in config.ini")
