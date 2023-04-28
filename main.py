from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import IDFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton
from db import Database

TOKEN = "5829458882:AAFjrDgoS1u8byarrBURNIIoHai0-l6_6U8"
admin_id = -1001964500086
tema_id = 931419194


boty = Bot(token=TOKEN)
dp = Dispatcher(boty, storage=MemoryStorage())
db = Database('database.db')

button_cou = KeyboardButton('⚡️Мои баллы')
button_get = KeyboardButton('🏆Топ участников')
button_sch = KeyboardButton('🗓 Расписание')
button_rep = KeyboardButton('✍️ Оставить отзыв')

choose_kb = ReplyKeyboardMarkup(resize_keyboard=True, ).add(button_cou, button_get).add(button_sch, button_rep)

exit_btn = KeyboardButton(text="Отменить")

exit_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, ).add(exit_btn)


class Form(StatesGroup):
    text = State()


async def anti_flood(*args, **kwargs):
    m = args[0]
    await m.answer("Слишком много запросов.\nПодожди пару секунд.")


def extract_arg(arg):
    return arg.split()[1:]


@dp.message_handler(IDFilter(chat_id=admin_id), commands=['get_id'])
async def get_id(message: types.Message):
    await boty.send_message(message.chat.id, message.chat.id)


@dp.message_handler(commands=['start'])
@dp.throttled(anti_flood, rate=3)
async def start(message: types.Message):
    if message.chat.type == 'private':
        if not db.user_exists(message.from_user.id):
            try:
                text = "@" + message.from_user.username
                db.add_user(message.from_user.id, text)
            except:
                pass
        await boty.send_message(message.from_user.id,
                                f"Привет, {message.from_user.username}!\n"
                                f"Что будем делать?", reply_markup=choose_kb)


@dp.message_handler(text=['⚡️Мои баллы'])
@dp.throttled(anti_flood, rate=3)
async def get_points_message(message: types.Message):
    text = db.get_point(message.from_user.id)
    await boty.send_message(message.from_user.id, "У вас *" + str(text[0]) + "* баллов",
                            parse_mode='Markdown')


@dp.message_handler(text=['✍️ Оставить отзыв'])
@dp.throttled(anti_flood, rate=3)
async def get_report(message: types.Message):
    if message.chat.id == admin_id:
        return
    await boty.send_message(message.chat.id, "Введите сообщение ниже", reply_markup=exit_keyboard)
    await Form.text.set()


@dp.message_handler(state=Form.text)
@dp.throttled(anti_flood, rate=3)
async def ask_process(message: types.Message, state: FSMContext):
    if message.text == "Отменить":
        await boty.send_message(chat_id=message.chat.id, text="Хорошо, как хотите :)", reply_markup=choose_kb)
        await state.finish()
    else:
        async with state.proxy() as text:
            text['text'] = message.text
            await state.finish()
        if message.chat.username is None:
            who = "Ник не установлен"
        else:
            who = "@" + message.from_user.username
        await boty.send_message(chat_id=tema_id,
                                text=f"<b>Новый отзыв</b>\nОт: {who}\nId: {message.from_user.id}\n"
                                     f"<b>Сообщение:</b>\n{message.text}",
                                parse_mode='HTML')
        await boty.send_message(chat_id=message.chat.id,
                                text="Передал отзыв организаторам.\nСпасибо!",
                                reply_markup=choose_kb)


@dp.message_handler(IDFilter(chat_id=tema_id), commands=['ans'])
async def ans_process(message: types.Message):
    arg = extract_arg(message.text)
    id = arg[0]
    arg.pop(0)
    answer = ""
    for add in arg:
        answer += add + " "
    await boty.send_message(id, f"*Сообщение администратора:*\n\n{answer}\n\n",
                            parse_mode='Markdown')


@dp.message_handler(text=['🏆Топ участников'])
@dp.throttled(anti_flood, rate=3)
async def get_top(message: types.Message):
    text = db.get_sorted()
    answer = "<b>ТОП пользователей:</b>\n"
    for row in range(10):
        try:
            answer += "<b>" + str(row + 1) + ".</b> " + str(text[row]) + "\n"
        except:
            pass
    answer = answer.replace("('", "")
    answer = answer.replace("',", " - ")
    answer = answer.replace(")", "")
    await boty.send_message(message.chat.id, answer, parse_mode="HTML")


@dp.message_handler(text=['🗓 Расписание'])
@dp.throttled(anti_flood, rate=3)
async def schedule_sed_photo(message: types.Message):
    await boty.send_photo(message.from_user.id, types.InputFile('test.jpg'))


@dp.message_handler(IDFilter(chat_id=admin_id), commands=['plus'])
async def plus_points_message(message: types.Message):
    text = message.text[6:]
    text = text.partition(" ")
    l_en = len(text[0])
    count = message.text[7 + l_en:]
    db.plus_point(text[0], count)


@dp.message_handler(IDFilter(chat_id=admin_id), commands=['minus'])
async def minus_points_message(message: types.Message):
    text = message.text[7:]
    text = text.partition(" ")
    l_en = len(text[0])
    count = message.text[8 + l_en:]
    db.minus_point(text[0], count)


@dp.message_handler(IDFilter(chat_id=admin_id), commands='sendall')
async def send_all(message: types.Message):
    text = message.text[9:]
    if len(text) == 0:
        await boty.send_message(admin_id, f"@{message.from_user.username}, сообщение не может быть пустым")
        return
    users = db.get_users()
    for row in users:
        try:
            await boty.send_message(row[0], text)
            if int(row[1]) != 1:
                db.set_active(row[0], 1)
        except:
            db.set_active(row[0], 0)
    await boty.send_message(admin_id, f"@{message.from_user.username}, отправил всем пользователям")


if __name__ == '__main__':
    print("starting")
    executor.start_polling(dp)
