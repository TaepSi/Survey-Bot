import aiosqlite


DB_NAME = "survey_bot.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        # Таблица опросов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT
            )
        """)

        # Таблица вопросов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id INTEGER,
                question TEXT,
                q_type TEXT,
                options TEXT
            )
        """)

        # Таблица ответов пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                survey_title TEXT,
                question TEXT,
                answer TEXT
            )
        """)

        await db.commit()


async def get_surveys():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, title FROM surveys")
        return await cursor.fetchall()


async def get_questions(survey_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT question, q_type, options FROM questions WHERE survey_id = ?",
            (survey_id,)
        )
        return await cursor.fetchall()


async def save_answer(user_id, survey_title, question, answer):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO answers (user_id, survey_title, question, answer)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, survey_title, question, answer)
        )
        await db.commit()


async def get_user_answers(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT survey_title, question, answer
            FROM answers
            WHERE user_id = ?
            """,
            (user_id,)
        )

        return await cursor.fetchall()