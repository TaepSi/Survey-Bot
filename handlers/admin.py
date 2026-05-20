from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import admin_menu, main_menu
from database import create_survey, add_questions, get_surveys, get_survey_stats

router = Router()

class AdminCreate(StatesGroup):
    waiting_title = State()
    waiting_questions = State()

class AdminStats(StatesGroup):
    waiting_survey = State()

@router.message(F.text == "Админ-панель")
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("⚙️ Админ-панель", reply_markup=admin_menu)

@router.message(F.text == "Создать опрос")
async def create_survey_start(message: Message, state: FSMContext):
    await state.set_state(AdminCreate.waiting_title)
    await message.answer("Введите название опроса:")

@router.message(AdminCreate.waiting_title)
async def create_survey_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminCreate.waiting_questions)
    await message.answer(
        "Введите вопросы. Каждый с новой строки в формате:\n"
        "<b>текст вопроса | тип</b>\n\n"
        "Типы:\n"
        "<b>text</b> — свободный ответ\n"
        "<b>yesno</b> — Да/Нет\n"
        "<b>choice | вариант1, вариант2</b> — выбор из вариантов\n\n"
        "Пример:\n"
        "<code>Как вас зовут? | text\n"
        "Любите Python? | yesno\n"
        "Любимый язык? | choice | Python, Java, C++</code>"
    )

@router.message(AdminCreate.waiting_questions)
async def create_survey_questions(message: Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    parsed = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) < 2:
            await message.answer(f"Ошибка в строке: {line}\nФормат: вопрос | тип")
            return
        q_text = parts[0].strip()
        q_type = parts[1].strip().lower()
        options = None
        if q_type == "choice":
            if len(parts) < 3:
                await message.answer(f"Для choice нужны варианты: вопрос | choice | в1, в2")
                return
            options = parts[2].strip()
        if q_type not in ("text", "yesno", "choice"):
            await message.answer(f"Неизвестный тип: {q_type}")
            return
        parsed.append((q_text, q_type, options))
    if not parsed:
        await message.answer("Вы не ввели ни одного вопроса.")
        return
    data = await state.get_data()
    survey_id = await create_survey(data["title"], message.from_user.id)
    await add_questions(survey_id, parsed)
    await state.clear()
    await message.answer(
        f"✅ Опрос «{data['title']}» создан! ({len(parsed)} вопросов)\n"
        f"Пользователи могут пройти его через кнопку «Пройти опрос».",
        reply_markup=admin_menu
    )

@router.message(F.text == "Статистика")
async def stats_list(message: Message, state: FSMContext):
    surveys = await get_surveys()
    if not surveys:
        await message.answer("Нет созданных опросов.")
        return
    text = "📊 <b>Статистика опросов:</b>\n\n"
    for s in surveys:
        sid, title, creator_id, created_at = s
        stats = await get_survey_stats(sid)
        text += f"📋 {title} (создан {created_at})\n👥 Прошли: {stats['total_users']}\n\n"
    await message.answer(text)

@router.message(F.text == "Главное меню")
async def go_main_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=main_menu)
