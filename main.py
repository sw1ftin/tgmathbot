import asyncio
import logging
import wolframalpha
from translate import Translator
from configparser import ConfigParser

from aiogram import Bot, Dispatcher, Router
from aiogram.dispatcher import router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.filters import Command

get_answer = lambda question: next(wolframalpha.Client(app_id).query(question).results).text
translator = Translator(to_lang='ru', from_lang='en')
router = Router()


@router.message(Command("start"))
async def start_handler(msg: Message):
    await msg.answer_sticker(sticker='CAACAgIAAxkBAAEoJEplcvI8vYOFxhCjj4W9fsb50Y570gACPBMAAoElyUsiXeSDccqJwzME')
    await msg.answer("Привет!")
    await msg.answer("Я помогу тебе решить любое математическое выражение, просто отправь мне его")


@router.message()
async def message_handler(msg: Message):
    try:
        ans = get_answer(msg.text)
        await msg.answer(f"Решение:\n{translator.translate(ans)}")
    except:
        logging.error(f"Invalid answer on question {msg.text}")
        await msg.answer(f"К сожалению, произошла ошибка. Повторите попытку позже")


async def main():
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
        logging.basicConfig(level=logging.INFO)
        asyncio.run(main())
    else:
        error = []
        if not app_id: error.append('app_id')
        if not token: error.append('token')
        raise ValueError(f"Fill {' and '.join(error)} fields in config.ini")
