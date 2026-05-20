from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import main_menu, surveys_inline, yesno_inline
from database import get_surveys, get_questions, save_answer, get_user_answers, has_user_completed

router = Router()

class TakingSurvey(StatesGroup):
    waiting_for_answer = State()

@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "📊 Добро пожаловать в SurveyBot!\n\n"
        "Здесь вы можете проходить опросы и смотреть свои ответы.\n"
        "Для создания опросов перейдите в Админ-панель.\n\n"
        "Это демо-версия. Для заказа персонального бота обратитесь к разработчику.",
        reply_markup=main_menu
    )

@router.message(F.text == "Пройти опрос")
async def choose_survey(message: Message):
    surveys = await get_surveys()
    if not surveys:
        await message.answer("Пока нет доступных опросов.")
        return
    await message.answer("Выберите опрос:", reply_markup=surveys_inline(surveys))

@router.callback_query(F.data.startswith("survey_"))
async def start_survey(callback: CallbackQuery, state: FSMContext):
    survey_id = int(callback.data.split("_")[1])
    if await has_user_completed(callback.from_user.id, survey_id):
        await callback.answer("Вы уже прошли этот опрос!", show_alert=True)
        return
    questions = await get_questions(survey_id)
    if not questions:
        await callback.answer("В этом опросе нет вопросов.", show_alert=True)
        return
    await state.update_data(survey_id=survey_id, questions=questions, current_q=0)
    await callback.message.answer(f"Опрос: {questions[0][2]}\n\n{questions[0][2]}")
    await ask_question(callback.message, state, questions[0])

async def ask_question(message: Message, state: FSMContext, question: tuple):
    q_id, survey_id, text, q_type, options, pos = question
    if q_type == "yesno":
        await message.answer(text, reply_markup=yesno_inline(q_id))
    elif q_type == "choice":
        opts = options.split(",") if options else []
        buttons = [[InlineKeyboardButton(text=o.strip(), callback_data=f"choice_{q_id}_{o.strip()}")] for o in opts]
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    else:
        await message.answer(f"{text}\n\n<i>Введите ваш ответ:</i>")
    await state.set_state(TakingSurvey.waiting_for_answer)

@router.callback_query(TakingSurvey.waiting_for_answer, F.data.startswith("yesno_"))
async def handle_yesno(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    q_id = int(parts[1])
    answer = parts[2]
    await process_answer(callback.message, state, q_id, answer, callback.from_user.id)
    await callback.answer()

@router.callback_query(TakingSurvey.waiting_for_answer, F.data.startswith("choice_"))
async def handle_choice(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    q_id = int(parts[1])
    answer = "_".join(parts[2:])
    await process_answer(callback.message, state, q_id, answer, callback.from_user.id)
    await callback.answer()

@router.message(TakingSurvey.waiting_for_answer)
async def handle_text_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions", [])
    current_q = data.get("current_q", 0)
    if current_q < len(questions):
        q = questions[current_q]
        await process_answer(message, state, q[0], message.text, message.from_user.id)

async def process_answer(message: Message, state: FSMContext, q_id: int, answer: str, user_id: int):
    data = await state.get_data()
    survey_id = data["survey_id"]
    questions = data["questions"]
    current_q = data["current_q"]
    await save_answer(user_id, survey_id, q_id, answer)
    current_q += 1
    if current_q < len(questions):
        await state.update_data(current_q=current_q)
        await ask_question(message, state, questions[current_q])
    else:
        await state.clear()
        await message.answer("✅ Спасибо! Вы прошли опрос.", reply_markup=main_menu)

@router.message(F.text == "Мои ответы")
async def my_answers(message: Message):
    answers = await get_user_answers(message.from_user.id)
    if not answers:
        await message.answer("У вас пока нет ответов.")
        return
    text = "<b>Ваши ответы:</b>\n\n"
    for title, q_text, answer_text, created_at in answers:
        text += f"📋 {title}\n❓ {q_text}\n→ {answer_text}\n<i>{created_at}</i>\n\n"
    await message.answer(text)

@router.message(F.text == "Контакты")
async def contacts(message: Message):
    await message.answer(
        "Связь с разработчиком:\n"
        "https://kwork.ru/user/demurgas"
    )

@router.message(F.text == "Главное меню")
async def go_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=main_menu)
