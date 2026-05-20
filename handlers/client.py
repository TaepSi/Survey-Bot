from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from keyboards import main_menu, contacts_keyboard, yes_no_keyboard
from database import (
    get_surveys,
    get_questions,
    save_answer,
    get_user_answers
)

router = Router()


class SurveyState(StatesGroup):
    answering = State()


@router.message(F.text == "/start")
async def start_command(message: Message):

    text = (
        "Это демо-версия бота для опросов.\n\n"
        "Вы можете пройти опросы и посмотреть свои ответы.\n\n"
        "Админ-панель доступна по кнопке \"Админ-панель\".\n\n"
        "Для заказа персонального бота обратитесь к разработчику."
    )

    await message.answer(text, reply_markup=main_menu())


@router.message(F.text == "Контакты")
async def contacts(message: Message):
    await message.answer(
        "Связь с разработчиком:",
        reply_markup=contacts_keyboard()
    )


@router.message(F.text == "Пройти опрос")
async def choose_survey(message: Message):

    surveys = await get_surveys()

    if not surveys:
        await message.answer("Список опросов пуст.")
        return

    text = "Доступные опросы:\n\n"

    for survey in surveys:
        text += f"{survey[0]}. {survey[1]}\n"

    text += "\nВведите ID опроса."

    await message.answer(text)


@router.message(F.text.regexp(r"^\d+$"))
async def start_survey(message: Message, state: FSMContext):

    survey_id = int(message.text)

    surveys = await get_surveys()

    survey_exists = False
    survey_title = ""

    for survey in surveys:
        if survey[0] == survey_id:
            survey_exists = True
            survey_title = survey[1]

    if not survey_exists:
        return

    questions = await get_questions(survey_id)

    if not questions:
        await message.answer("В этом опросе нет вопросов.")
        return

    await state.update_data(
        survey_title=survey_title,
        questions=questions,
        index=0
    )

    first_question = questions[0]

    await message.answer(first_question[0])

    await state.set_state(SurveyState.answering)


@router.message(SurveyState.answering)
async def process_answers(message: Message, state: FSMContext):

    data = await state.get_data()

    questions = data["questions"]
    index = data["index"]
    survey_title = data["survey_title"]

    current_question = questions[index]

    # Сохраняем ответ
    await save_answer(
        user_id=message.from_user.id,
        survey_title=survey_title,
        question=current_question[0],
        answer=message.text
    )

    index += 1

    # Проверяем, закончились ли вопросы
    if index >= len(questions):
        await message.answer(
            "Опрос завершён!",
            reply_markup=main_menu()
        )

        await state.clear()
        return

    # Следующий вопрос
    next_question = questions[index]

    await state.update_data(index=index)

    q_text = next_question[0]
    q_type = next_question[1]
    options = next_question[2]

    # Вопрос типа да/нет
    if q_type == "yesno":
        await message.answer(
            q_text,
            reply_markup=yes_no_keyboard()
        )

    # Вопрос с вариантами
    elif q_type == "choice":

        variants = options.split(",")

        text = q_text + "\n\n"

        for variant in variants:
            text += f"- {variant.strip()}\n"

        await message.answer(text)

    else:
        await message.answer(q_text)


@router.message(F.text == "Мои ответы")
async def my_answers(message: Message):

    answers = await get_user_answers(message.from_user.id)

    if not answers:
        await message.answer("У вас пока нет ответов.")
        return

    text = "Ваши ответы:\n\n"

    for survey_title, question, answer in answers:
        text += (
            f"Опрос: {survey_title}\n"
            f"Вопрос: {question}\n"
            f"Ответ: {answer}\n\n"
        )

    await message.answer(text)