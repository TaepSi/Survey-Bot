from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пройти опрос")],
            [KeyboardButton(text="Мои ответы")],
            [KeyboardButton(text="Контакты")],
            [KeyboardButton(text="Админ-панель")]
        ],
        resize_keyboard=True
    )


def contacts_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Связаться с разработчиком",
                    url="https://t.me/your_username"
                )
            ]
        ]
    )


def yes_no_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Да"),
                KeyboardButton(text="Нет")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )