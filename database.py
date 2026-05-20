import aiosqlite

DB_NAME = "surveys.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица опросов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                creator_id INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        # Таблица вопросов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                q_type TEXT NOT NULL, -- text, yesno, choice
                options TEXT, -- для choice: варианты через запятую
                position INTEGER NOT NULL,
                FOREIGN KEY (survey_id) REFERENCES surveys(id)
            )
        """)
        # Таблица ответов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                survey_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (survey_id) REFERENCES surveys(id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        """)
        await db.commit()

# --- Опросы ---

async def create_survey(title: str, creator_id: int) -> int:
    from datetime import datetime
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO surveys (title, creator_id, created_at) VALUES (?, ?, ?)",
            (title, creator_id, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        await db.commit()
        return cursor.lastrowid

async def get_surveys() -> list:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM surveys ORDER BY id DESC")
        return await cursor.fetchall()

async def get_survey(survey_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,))
        return await cursor.fetchone()

# --- Вопросы ---

async def add_questions(survey_id: int, questions: list) -> None:
    """questions: список кортежей (text, q_type, options, position)"""
    async with aiosqlite.connect(DB_NAME) as db:
        for pos, q in enumerate(questions):
            text, q_type, options = q
            await db.execute(
                "INSERT INTO questions (survey_id, text, q_type, options, position) VALUES (?, ?, ?, ?, ?)",
                (survey_id, text, q_type, options, pos + 1)
            )
        await db.commit()

async def get_questions(survey_id: int) -> list:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM questions WHERE survey_id = ? ORDER BY position",
            (survey_id,)
        )
        return await cursor.fetchall()

# --- Ответы ---

async def save_answer(user_id: int, survey_id: int, question_id: int, answer_text: str) -> None:
    from datetime import datetime
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO answers (user_id, survey_id, question_id, answer_text, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, survey_id, question_id, answer_text, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        await db.commit()

async def get_user_answers(user_id: int) -> list:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT s.title, q.text, a.answer_text, a.created_at
            FROM answers a
            JOIN surveys s ON a.survey_id = s.id
            JOIN questions q ON a.question_id = q.id
            WHERE a.user_id = ?
            ORDER BY a.created_at DESC
        """, (user_id,))
        return await cursor.fetchall()

async def has_user_completed(user_id: int, survey_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM answers WHERE user_id = ? AND survey_id = ?",
            (user_id, survey_id)
        )
        row = await cursor.fetchone()
        return row[0] > 0 if row else False

async def get_survey_stats(survey_id: int) -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        # Количество прошедших
        cursor = await db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM answers WHERE survey_id = ?",
            (survey_id,)
        )
        row = await cursor.fetchone()
        total_users = row[0] if row else 0

        # Ответы по вопросам
        cursor = await db.execute(
            "SELECT q.text, a.answer_text FROM answers a JOIN questions q ON a.question_id = q.id WHERE a.survey_id = ?",
            (survey_id,)
        )
        answers = await cursor.fetchall()
        return {"total_users": total_users, "answers": answers}
        
async def delete_survey(survey_id: int) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM questions WHERE survey_id = ?", (survey_id,))
        await db.execute("DELETE FROM answers WHERE survey_id = ?", (survey_id,))
        await db.execute("DELETE FROM surveys WHERE id = ?", (survey_id,))
        await db.commit()
