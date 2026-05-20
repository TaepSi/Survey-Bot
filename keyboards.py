from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Пройти опрос"), KeyboardButton(text="Мои ответы")],
        [KeyboardButton(text="Контакты"), KeyboardButton(text="Админ-панель")],
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Создать опрос"), KeyboardButton(text="Статистика"), KeyboardButton(text="Удалить опрос")],
        [KeyboardButton(text="Главное меню")],
    ],
    resize_keyboard=True
)

def surveys_inline(surveys: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=s[1], callback_data=f"survey_{s[0]}")]
        for s in surveys
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def yesno_inline(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data=f"yesno_{question_id}_yes"),
         InlineKeyboardButton(text="Нет", callback_data=f"yesno_{question_id}_no")]
    ])
