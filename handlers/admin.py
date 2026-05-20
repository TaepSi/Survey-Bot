from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from keyboards import main_menu

router = Router()


class AdminState(StatesGroup):
    waiting_title = State()
    waiting_questions = State()


@router.message(F.text == "Админ-панель")
async def admin_panel(message: Message):

    text = (
        "ДЕМО-РЕЖИМ\n\n"
        "Вы можете создать опрос как администратор.\n"
        "Данные НЕ сохраняются."
    )

    await message.answer(
        text +
        "\n\nВведите название опроса:"
    )


@router.message(F.text)
async def fake_admin_flow(message: Message, state: FSMContext):

    current_state = await state.get_state()

    # Начало создания опроса
    if current_state is None and len(message.text) > 3:

        if message.text in [
            "Пройти опрос",
            "Мои ответы",
            "Контакты",
            "Админ-панель"
        ]:
            return

        await state.update_data(title=message.text)

        await message.answer(
            "Введите вопросы.\n\n"
            "Пример:\n"
            "Как вас зовут? | text\n"
            "Ваш возраст? | text\n"
            "Любите Python? | yesno\n"
            "Любимый язык? | choice | Python, Java, C++"
        )

        await state.set_state(AdminState.waiting_questions)
        return

    # Финал демо-создания
    if current_state == AdminState.waiting_questions:

        await message.answer(
            "Опрос успешно создан! (демо-режим)\n\n"
            "В реальном проекте данные сохранились бы в БД.",
            reply_markup=main_menu()
        )

        await state.clear()