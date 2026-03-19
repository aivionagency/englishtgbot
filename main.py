import asyncio
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery
# ==========================================
# КЛЮЧИ И НАСТРОЙКИ
# ==========================================
BOT_TOKEN = "8244205106:AAGYh6dYZcy762h_tRLzesu2cvh7711R-O4"
MINI_APP_URL = "https://aivion.moscow/"
SUPPORT_USERNAME = "@andlv00"
SUPPORT_URL = f"https://t.me/{SUPPORT_USERNAME}"
CHANNEL_URL = "t.me/aivionagency"

# Настройки Google Таблиц
GOOGLE_CREDENTIALS_FILE = "credentials.json"  # Файл, который выдаст Google Cloud
GOOGLE_SHEET_NAME = "Учет пользователей  ANOVA"
# ==========================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация подключения к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(GOOGLE_SHEET_NAME).sheet1
except Exception as e:
    logging.warning(f"Google Sheets не подключены (отсутствует файл credentials.json или ошибка): {e}")
    sheet = None

# Создаем пустое множество для хранения ников в памяти бота
known_users = set()


def load_known_users():
    """Загружает уже существующих пользователей из таблицы при старте"""
    if sheet:
        try:
            # col_values(1) берет все данные из первого столбца таблицы
            users = sheet.col_values(1)
            known_users.update(users)
            logging.info(f"Загружено уникальных пользователей из базы: {len(known_users)}")
        except Exception as e:
            logging.error(f"Ошибка чтения таблицы при старте: {e}")


def add_user_to_sheet(username: str):
    """Синхронная функция записи в таблицу только новых пользователей"""
    formatted_name = f"@{username}"

    # Проверяем, что таблица доступна и пользователя еще нет в нашей памяти
    if sheet and formatted_name not in known_users:
        try:
            # Записываем ник в первую свободную строку
            sheet.append_row([formatted_name])
            # Добавляем в память бота, чтобы больше не проверять и не дублировать
            known_users.add(formatted_name)
            logging.info(f"Добавлен новый пользователь: {formatted_name}")
        except Exception as e:
            logging.error(f"Ошибка записи в таблицу: {e}")
# --- КЛАВИАТУРЫ ---
def get_main_menu():
    # Кнопка Mini App в отдельном ряду с зеленым стилем (success)
    webapp_button = [
        InlineKeyboardButton(
            text="Открыть Mini App 🚀",
            web_app=WebAppInfo(url=MINI_APP_URL),
            style="success"  # <--- Правильный параметр из обновления API 9.4
        )
    ]

    # Остальные кнопки остаются стандартными
    other_buttons = [
        [InlineKeyboardButton(text="Служба поддержки", url=SUPPORT_URL)]
#        [InlineKeyboardButton(text="Telegram-канал", url=CHANNEL_URL)]
    ]

    return InlineKeyboardMarkup(inline_keyboard=[webapp_button] + other_buttons)

def get_back_to_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Главное меню", callback_data="back_to_menu")]
    ])


# --- ОБРАБОТЧИКИ ---
@dp.message(Command(commands=["start", "menu"]))
async def cmd_start_menu(message: Message):
    user_name = message.from_user.first_name

    # Проверяем кэш и записываем в Google Таблицу
    if message.from_user.username:
        await asyncio.to_thread(add_user_to_sheet, message.from_user.username)

    # Новый текст приветствия
    welcome_text = (
        f"Добро пожаловать, {user_name}!\n\n"
        f"Вы открыли **ANOVA** — сервис, который использует ИИ, чтобы сделать ваше "
        f"изучение английского языка в разы эффективнее.\n\n"
        f"⚠️ Приложение сейчас в активной разработке, поэтому если что-то пошло не так - напишите в поддержку.\n"
    )

    await message.answer(
    welcome_text,
    reply_markup=get_main_menu(),
    parse_mode="Markdown"
)

    # второе сообщение — полностью пассивное
    await message.answer(
    "Дорогие друзья!\n\n"
    "Из-за ограничений со стороны РКН сервис может нестабильно работать без VPN. "
    "Для большинства пользователей это уже привычная практика (в том числе при использовании Telegram), "
    "поэтому надеемся, что это не доставит неудобств.\n\n"
    "Приятного использования!"
)

@dp.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@dp.message(F.text)
async def handle_text(message: Message):
    await message.answer(
        "Если у Вас возникли вопросы, пожалуйста свяжитесь со Службой поддержки через основное меню",
        reply_markup=get_back_to_menu_keyboard()
    )


async def main():
    # Запускаем чтение базы данных перед стартом бота.
    # Используем to_thread, чтобы не блокировать асинхронный цикл.
    await asyncio.to_thread(load_known_users)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
