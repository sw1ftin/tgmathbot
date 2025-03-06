import os
from ai.openrouter import AIAssistant
from ai.latexocr import FormulaRecognizer
import asyncio
import logging
import wolframalpha
from configparser import ConfigParser
from tinydb import TinyDB, Query

from aiogram import Bot, Dispatcher, Router
from aiogram.dispatcher import router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.client.bot import DefaultBotProperties
from aiogram.utils import markdown

db = TinyDB('database.json')
table = db.table('Users modes')
User = Query()

keyboard_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Wolfram Alpha', callback_data='wolfram')],
    [InlineKeyboardButton(text='Openrouter', callback_data='text')],
    [InlineKeyboardButton(text='Image Recognition', callback_data='image')]
])

router = Router()


def get_answer(mode: str, question: str, image_url: str = "") -> str:
    match(mode):
        case 'wolfram':
            return '\n'.join([elem.text for elem in list(wolfram_client.query(question).results)])
        case 'text':
            return assistant.get_response(question)
        case 'image':
            return assistant.get_image_response(image_url)
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


@router.callback_query(lambda c: c.data in ['wolfram', 'text', 'image'])
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
        # print(msg.json())
        # print('---------')
        print(msg.text)
        if msg.photo:
            if mode == 'image':
                print('Image received')
                file_id = msg.photo[-1].file_id
                file = await bot.get_file(file_id)
                file_path = file.file_path

                image_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                print("Image URL:", image_url)

                try:
                    ans = get_answer(mode, "", image_url)
                    print("Answer", ans)
                    await msg.answer("Ответ нейросети:")
                    await msg.answer(markdown.pre(ans))
                except Exception as e:
                    logging.error(f"FormulaRecognitionError: {e}")
                    await msg.answer("Не удалось распознать текст на изображении.")
            
            else:
                print('Image received')
                file_id = msg.photo[-1].file_id
                file = await bot.get_file(file_id)
                file_path = file.file_path

                image_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                print("Image URL:", image_url)

                local_image_path = f"temp_image_{msg.from_user.id}.jpg"
                await bot.download_file(file_path, local_image_path)

                try:
                    recognized_text = latex.recognize_from_image(local_image_path)
                    print(f"Recognized text: {recognized_text}")
                    # ans = get_answer(mode, recognized_text + "" if msg.text is None else " " + msg.text)
                    # print("Answer", ans)
                    await msg.answer("Распознанный текст:")
                    await msg.answer(markdown.pre(recognized_text))
                except Exception as e:
                    logging.error(f"FormulaRecognitionError: {e}")
                    await msg.answer("Не удалось распознать текст на изображении.")

                if os.path.exists(local_image_path):
                    os.remove(local_image_path)
        else:
            ans = get_answer(mode, msg.text)
            await msg.answer("Решение:")
            await msg.answer(ans)
    except:
        logging.error(f"AnswerError {mode} {msg.text}")
        await msg.answer(f"К сожалению, произошла ошибка. Повторите попытку позже")


async def main():
    global bot
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    config = ConfigParser()
    config.read('config.ini')
    app_id = config.get('wolfram', 'app_id')
    token = config.get('telegram', 'token')
    api_key = config.get('openrouter', 'api_key')
    assistant = AIAssistant(api_key=api_key)
    latex = FormulaRecognizer()

    if app_id and token:
        wolfram_client = wolframalpha.Client(app_id)
        logging.basicConfig(level=logging.INFO)
        asyncio.run(main())
    else:
        error = []
        if not app_id: error.append('app_id')
        if not token: error.append('token')
        raise ValueError(f"Fill {' and '.join(error)} fields in config.ini")
