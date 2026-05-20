import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import admin_menu, main_menu, surveys_inline
from database import create_survey, add_questions, get_surveys, get_survey_stats, delete_survey

router = Router()

class AdminCreate(StatesGroup):
    waiting_title = State()
    building = State()
    adding_question_text = State()
    adding_yesno = State()
    adding_choice_options = State()

@router.message(F.text == "Админ-панель")
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("⚙️ <b>Админ-панель</b>\n\nВыберите действие:", reply_markup=admin_menu)

@router.message(F.text == "Создать опрос")
async def create_survey_start(message: Message, state: FSMContext):
    await state.set_state(AdminCreate.waiting_title)
    await message.answer("📝 Введите <b>название</b> опроса:")

@router.message(AdminCreate.waiting_title)
async def create_survey_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip(), questions=[])
    await state.set_state(AdminCreate.building)
    await show_builder_menu(message)

async def show_builder_menu(message: Message):
    data = await state.get_data()
    questions = data.get("questions", [])
    text = f"📝 <b>Создание опроса «{data.get('title', '')}»</b>\n\n✅ Вопросов: {len(questions)}\n\nДобавьте вопрос:"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Текстовый", callback_data="add_text")],
        [InlineKeyboardButton(text="✅ Да/Нет", callback_data="add_yesno")],
        [InlineKeyboardButton(text="🔘 С выбором", callback_data="add_choice")],
        [InlineKeyboardButton(text="🎉 ГОТОВО", callback_data="done_building")],
    ])
    await message.answer(text, reply_markup=kb)

@router.callback_query(AdminCreate.building, F.data == "add_text")
async def add_text_q(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminCreate.adding_question_text)
    await callback.message.answer("📝 Введите текст вопроса:")
    await callback.answer()

@router.message(AdminCreate.adding_question_text)
async def got_text_q(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions", [])
    questions.append(("text", message.text.strip()))
    await state.update_data(questions=questions)
    await state.set_state(AdminCreate.building)
    await show_builder_menu(message)

@router.callback_query(AdminCreate.building, F.data == "add_yesno")
async def add_yesno_q(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminCreate.adding_yesno)
    await callback.message.answer("✅ Введите текст вопроса (Да/Нет):")
    await callback.answer()

@router.message(AdminCreate.adding_yesno)
async def got_yesno_q(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions", [])
    questions.append(("yesno", message.text.strip()))
    await state.update_data(questions=questions)
    await state.set_state(AdminCreate.building)
    await show_builder_menu(message)

@router.callback_query(AdminCreate.building, F.data == "add_choice")
async def add_choice_q(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminCreate.adding_choice_options)
    await callback.message.answer("🔘 Введите вопрос и варианты через запятую:\n\n<i>Пример: Любимый цвет?, Красный, Синий</i>")
    await callback.answer()

@router.message(AdminCreate.adding_choice_options)
async def got_choice_q(message: Message, state: FSMContext):
    parts = message.text.split(",")
    if len(parts) < 2:
        await message.answer("⚠️ Нужно указать вопрос и хотя бы один вариант через запятую.")
        return
    q_text = parts[0].strip()
    options = [o.strip() for o in parts[1:]]
    data = await state.get_data()
    questions = data.get("questions", [])
    questions.append(("choice", q_text, options))
    await state.update_data(questions=questions)
    await state.set_state(AdminCreate.building)
    await show_builder_menu(message)

@router.callback_query(AdminCreate.building, F.data == "done_building")
async def finish_building(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    title = data.get("title")
    questions = data.get("questions", [])
    if not questions:
        await callback.answer("⚠️ Добавьте хотя бы один вопрос!")
        return
    survey_id = await create_survey(title, callback.from_user.id)
    for q in questions:
        if q[0] == "choice":
            _, q_text, options = q
            await add_questions(survey_id, [(q_text, "choice", ",".join(options), 0)])
        else:
            await add_questions(survey_id, [(q[1], q[0], None, 0)])
    await state.clear()
    await callback.message.answer(
        f"🎉 <b>Опрос «{title}» создан!</b>\n\n✅ Вопросов: {len(questions)}\n📊 Пройти: кнопка «Пройти опрос»",
        reply_markup=admin_menu
    )
    await callback.answer()

@router.message(F.text == "Удалить опрос")
async def delete_survey_start(message: Message):
    surveys = await get_surveys()
    if not surveys:
        await message.answer("📭 Нет опросов для удаления.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=s[1], callback_data=f"del_{s[0]}")] for s in surveys
    ])
    await message.answer("🗑 Выберите опрос для удаления:", reply_markup=kb)

@router.callback_query(F.data.startswith("del_"))
async def delete_survey_confirm(callback: CallbackQuery):
    survey_id = int(callback.data.split("_")[1])
    await delete_survey(survey_id)
    await callback.message.edit_text("✅ Опрос удалён.")
    await callback.answer()

@router.message(F.text == "Статистика")
async def stats_list(message: Message):
    surveys = await get_surveys()
    if not surveys:
        await message.answer("📊 Нет созданных опросов.")
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
