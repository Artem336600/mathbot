"""
Seed script: populate DB with 5 test topics and 12 questions each (60 total).

Run after migrations:
    python -m data.seed

Idempotent: skips topics/questions that already exist.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from sqlalchemy import select

from db.session import async_session_factory
from db.models import Topic, Question


SEED_DATA = [
    {
        "title": "Дроби",
        "theory": (
            "**Дроби** — числа вида a/b, где a — числитель, b — знаменатель.\n\n"
            "**Сложение:** a/b + c/d = (ad + bc) / bd\n"
            "**Умножение:** a/b × c/d = ac / bd\n"
            "**Деление:** a/b ÷ c/d = a/b × d/c\n"
            "**Сокращение:** делим числитель и знаменатель на НОД."
        ),
        "questions": [
            # Easy (difficulty=1)
            {
                "text": "Сколько будет 1/2 + 1/2?",
                "a": "1", "b": "2", "c": "1/4", "d": "0",
                "correct": "a",
                "explanation": "1/2 + 1/2 = 2/2 = 1",
                "difficulty": 1,
            },
            {
                "text": "Сколько будет 3/4 − 1/4?",
                "a": "1/2", "b": "1", "c": "2/4", "d": "4",
                "correct": "a",
                "explanation": "3/4 − 1/4 = 2/4 = 1/2",
                "difficulty": 1,
            },
            {
                "text": "Упростите дробь 4/8:",
                "a": "1/2", "b": "2/4", "c": "4/8", "d": "3/6",
                "correct": "a",
                "explanation": "НОД(4,8)=4 → 4/8 = 1/2",
                "difficulty": 1,
            },
            {
                "text": "Сколько будет 2/3 + 1/3?",
                "a": "3/3", "b": "1", "c": "3/6", "d": "2",
                "correct": "b",
                "explanation": "2/3 + 1/3 = 3/3 = 1",
                "difficulty": 1,
            },
            # Medium (difficulty=2)
            {
                "text": "Сколько будет 1/3 + 1/4?",
                "a": "7/12", "b": "2/7", "c": "1/6", "d": "5/12",
                "correct": "a",
                "explanation": "1/3 + 1/4 = 4/12 + 3/12 = 7/12",
                "difficulty": 2,
            },
            {
                "text": "Сколько будет 3/5 × 5/6?",
                "a": "1/2", "b": "15/30", "c": "8/11", "d": "3/6",
                "correct": "a",
                "explanation": "3/5 × 5/6 = 15/30 = 1/2",
                "difficulty": 2,
            },
            {
                "text": "Сколько будет 7/8 − 3/4?",
                "a": "1/8", "b": "4/4", "c": "1/4", "d": "4/8",
                "correct": "a",
                "explanation": "7/8 − 6/8 = 1/8",
                "difficulty": 2,
            },
            {
                "text": "Чему равно 2/3 ÷ 4/9?",
                "a": "3/2", "b": "8/27", "c": "1/2", "d": "6/4",
                "correct": "a",
                "explanation": "2/3 ÷ 4/9 = 2/3 × 9/4 = 18/12 = 3/2",
                "difficulty": 2,
            },
            # Hard (difficulty=3)
            {
                "text": "Найдите: 5/6 − 2/9 + 1/3",
                "a": "17/18", "b": "4/18", "c": "7/9", "d": "11/18",
                "correct": "a",
                "explanation": "5/6=15/18, 2/9=4/18, 1/3=6/18 → 15−4+6=17 → 17/18",
                "difficulty": 3,
            },
            {
                "text": "Сколько составляет (3/4)² ?",
                "a": "9/16", "b": "6/8", "c": "3/8", "d": "9/8",
                "correct": "a",
                "explanation": "(3/4)² = 9/16",
                "difficulty": 3,
            },
            {
                "text": "Решите: x/3 − x/5 = 4. Найдите x.",
                "a": "30", "b": "15", "c": "20", "d": "12",
                "correct": "a",
                "explanation": "x(1/3−1/5)=4 → x·2/15=4 → x=30",
                "difficulty": 3,
            },
            {
                "text": "Между какими целыми числами находится дробь 17/5?",
                "a": "3 и 4", "b": "2 и 3", "c": "4 и 5", "d": "5 и 6",
                "correct": "a",
                "explanation": "17/5 = 3.4, значит между 3 и 4",
                "difficulty": 3,
            },
        ],
    },
    {
        "title": "Проценты",
        "theory": (
            "**Процент** — сотая доля числа.\n\n"
            "**Формулы:**\n"
            "• P% от N = N × P / 100\n"
            "• Процент: P = (A/B) × 100%\n"
            "• Число по проценту: N = A × 100 / P\n"
            "**Изменение:** Если X выросло на P%, новое = X × (1 + P/100)"
        ),
        "questions": [
            {"text": "Найдите 10% от 200.", "a": "20", "b": "2", "c": "200", "d": "10", "correct": "a", "explanation": "200 × 10/100 = 20", "difficulty": 1},
            {"text": "Найдите 50% от 80.", "a": "40", "b": "80", "c": "4", "d": "50", "correct": "a", "explanation": "80 × 50/100 = 40", "difficulty": 1},
            {"text": "25% от 400 равно:", "a": "100", "b": "25", "c": "40", "d": "200", "correct": "a", "explanation": "400 × 25/100 = 100", "difficulty": 1},
            {"text": "Чему равно 1% от 1000?", "a": "10", "b": "1", "c": "100", "d": "0.1", "correct": "a", "explanation": "1000 × 1/100 = 10", "difficulty": 1},
            {"text": "Цена выросла с 500 до 600 ₽. На сколько процентов?", "a": "20%", "b": "10%", "c": "15%", "d": "25%", "correct": "a", "explanation": "(600−500)/500 × 100 = 20%", "difficulty": 2},
            {"text": "Найдите 35% от 260.", "a": "91", "b": "35", "c": "88", "d": "95", "correct": "a", "explanation": "260 × 35/100 = 91", "difficulty": 2},
            {"text": "После скидки 20% товар стоит 400 ₽. Какова первоначальная цена?", "a": "500", "b": "480", "c": "420", "d": "450", "correct": "a", "explanation": "400 / 0.8 = 500", "difficulty": 2},
            {"text": "Число 75 — это 60% от какого числа?", "a": "125", "b": "100", "c": "150", "d": "75", "correct": "a", "explanation": "75 / 0.6 = 125", "difficulty": 2},
            {"text": "Вклад 10 000 ₽ под 12% годовых на 2 года (простые проценты). Итог?", "a": "12 400", "b": "12 000", "c": "11 200", "d": "12 200", "correct": "a", "explanation": "10000 + 10000×0.12×2 = 12 400", "difficulty": 3},
            {"text": "НДС 20% включён в цену 1 200 ₽. Чему равен НДС?", "a": "200", "b": "240", "c": "180", "d": "120", "correct": "a", "explanation": "1200/1.2 = 1000, НДС = 200", "difficulty": 3},
            {"text": "Сколько % составляет 45 от 360?", "a": "12.5%", "b": "8%", "c": "15%", "d": "10%", "correct": "a", "explanation": "45/360 × 100 = 12.5%", "difficulty": 3},
            {"text": "После роста на 25% и снижения на 25% от чего зависит итог?", "a": "−6.25% от начала", "b": "0%", "c": "+6.25%", "d": "−12.5%", "correct": "a", "explanation": "1×1.25×0.75=0.9375 → −6.25%", "difficulty": 3},
        ],
    },
    {
        "title": "Уравнения",
        "theory": (
            "**Линейное уравнение:** ax + b = c → x = (c−b)/a\n\n"
            "**Квадратное:** ax² + bx + c = 0\n"
            "Дискриминант: D = b² − 4ac\n"
            "x = (−b ± √D) / 2a\n\n"
            "**Правило переноса:** слагаемые переносятся с противоположным знаком."
        ),
        "questions": [
            {"text": "Решите: x + 5 = 12", "a": "7", "b": "17", "c": "5", "d": "12", "correct": "a", "explanation": "x = 12 − 5 = 7", "difficulty": 1},
            {"text": "Решите: 3x = 18", "a": "6", "b": "3", "c": "18", "d": "54", "correct": "a", "explanation": "x = 18 / 3 = 6", "difficulty": 1},
            {"text": "Решите: x − 8 = 4", "a": "12", "b": "4", "c": "8", "d": "−4", "correct": "a", "explanation": "x = 4 + 8 = 12", "difficulty": 1},
            {"text": "Решите: 2x + 3 = 11", "a": "4", "b": "7", "c": "3", "d": "8", "correct": "a", "explanation": "2x = 8, x = 4", "difficulty": 1},
            {"text": "Решите: 4x − 5 = 3x + 2", "a": "7", "b": "3", "c": "−7", "d": "5", "correct": "a", "explanation": "4x−3x = 2+5, x = 7", "difficulty": 2},
            {"text": "Решите: 2(x − 3) = 8", "a": "7", "b": "4", "c": "5", "d": "11", "correct": "a", "explanation": "x−3=4, x=7", "difficulty": 2},
            {"text": "Дискриминант x²−5x+6=0 равен:", "a": "1", "b": "4", "c": "−1", "d": "25", "correct": "a", "explanation": "D = 25 − 24 = 1", "difficulty": 2},
            {"text": "Корни x²−5x+6=0:", "a": "2 и 3", "b": "1 и 5", "c": "−2 и −3", "d": "1 и 6", "correct": "a", "explanation": "D=1, x=(5±1)/2 → 2 и 3", "difficulty": 2},
            {"text": "Решите: x²= 25", "a": "±5", "b": "5", "c": "−5", "d": "25", "correct": "a", "explanation": "x = ±5", "difficulty": 3},
            {"text": "Если (x+1)(x−3)=0, то x:", "a": "−1 или 3", "b": "1 или −3", "c": "3", "d": "−1", "correct": "a", "explanation": "Произведение = 0 → x = −1 или x = 3", "difficulty": 3},
            {"text": "Решите систему: x+y=5, x−y=1", "a": "x=3,y=2", "b": "x=4,y=1", "c": "x=2,y=3", "d": "x=1,y=4", "correct": "a", "explanation": "Сложим: 2x=6, x=3, y=2", "difficulty": 3},
            {"text": "Корень уравнения 3x²−12=0:", "a": "±2", "b": "±4", "c": "2", "d": "±√3", "correct": "a", "explanation": "x²=4, x=±2", "difficulty": 3},
        ],
    },
    {
        "title": "Геометрия",
        "theory": (
            "**Периметры:**\n"
            "• Квадрат: P = 4a\n"
            "• Прямоугольник: P = 2(a+b)\n"
            "• Круг: P = 2πr\n\n"
            "**Площади:**\n"
            "• Квадрат: S = a²\n"
            "• Прямоугольник: S = a×b\n"
            "• Треугольник: S = a×h/2\n"
            "• Круг: S = πr²\n\n"
            "**Теорема Пифагора:** c² = a² + b²"
        ),
        "questions": [
            {"text": "Периметр квадрата со стороной 5 см:", "a": "20", "b": "25", "c": "10", "d": "15", "correct": "a", "explanation": "P = 4×5 = 20 см", "difficulty": 1},
            {"text": "Площадь прямоугольника 4×6:", "a": "24", "b": "20", "c": "12", "d": "48", "correct": "a", "explanation": "S = 4×6 = 24", "difficulty": 1},
            {"text": "Площадь квадрата со стороной 7:", "a": "49", "b": "28", "c": "14", "d": "21", "correct": "a", "explanation": "S = 7² = 49", "difficulty": 1},
            {"text": "Периметр прямоугольника 3×8:", "a": "22", "b": "11", "c": "24", "d": "44", "correct": "a", "explanation": "P = 2×(3+8) = 22", "difficulty": 1},
            {"text": "Гипотенуза прямоугольного треугольника с катетами 3 и 4:", "a": "5", "b": "7", "c": "4", "d": "6", "correct": "a", "explanation": "√(9+16) = √25 = 5", "difficulty": 2},
            {"text": "Площадь треугольника с основ. 10 и высотой 6:", "a": "30", "b": "60", "c": "16", "d": "15", "correct": "a", "explanation": "S = 10×6/2 = 30", "difficulty": 2},
            {"text": "Радиус круга 7. Площадь (π≈3.14):", "a": "153.86", "b": "44", "c": "49", "d": "154", "correct": "a", "explanation": "S = π×7² ≈ 3.14×49 ≈ 153.86", "difficulty": 2},
            {"text": "Длина окружности при r=5 (π≈3.14):", "a": "31.4", "b": "15.7", "c": "78.5", "d": "25", "correct": "a", "explanation": "C = 2×3.14×5 = 31.4", "difficulty": 2},
            {"text": "Диагональ квадрата со стороной 6 равна:", "a": "6√2", "b": "12", "c": "36", "d": "9", "correct": "a", "explanation": "d = a√2 = 6√2 ≈ 8.49", "difficulty": 3},
            {"text": "Площадь трапеции с основаниями 6,10 и высотой 5:", "a": "40", "b": "80", "c": "20", "d": "50", "correct": "a", "explanation": "S = (6+10)/2 × 5 = 40", "difficulty": 3},
            {"text": "Катет прямоугольного Δ при гипотенузе 13 и другом катете 5:", "a": "12", "b": "8", "c": "10", "d": "11", "correct": "a", "explanation": "√(169−25) = √144 = 12", "difficulty": 3},
            {"text": "Площадь ромба с диагоналями 8 и 12:", "a": "48", "b": "96", "c": "40", "d": "24", "correct": "a", "explanation": "S = 8×12/2 = 48", "difficulty": 3},
        ],
    },
    {
        "title": "Степени и корни",
        "theory": (
            "**Степень:** aⁿ = a × a × ... × a (n раз)\n\n"
            "**Свойства:**\n"
            "• aᵐ × aⁿ = aᵐ⁺ⁿ\n"
            "• aᵐ ÷ aⁿ = aᵐ⁻ⁿ\n"
            "• (aᵐ)ⁿ = aᵐⁿ\n"
            "• a⁰ = 1 (a ≠ 0)\n\n"
            "**Корень:** √a = a^(1/2)\n"
            "√(a×b) = √a × √b"
        ),
        "questions": [
            {"text": "Вычислите 2³:", "a": "8", "b": "6", "c": "9", "d": "4", "correct": "a", "explanation": "2³ = 2×2×2 = 8", "difficulty": 1},
            {"text": "Вычислите √36:", "a": "6", "b": "18", "c": "8", "d": "4", "correct": "a", "explanation": "√36 = 6 т.к. 6²=36", "difficulty": 1},
            {"text": "Чему равно 5⁰?", "a": "1", "b": "0", "c": "5", "d": "−1", "correct": "a", "explanation": "Любое число в степени 0 равно 1", "difficulty": 1},
            {"text": "Вычислите 3²:", "a": "9", "b": "6", "c": "8", "d": "3", "correct": "a", "explanation": "3² = 3×3 = 9", "difficulty": 1},
            {"text": "Упростите: 2³ × 2⁴", "a": "2⁷", "b": "2¹²", "c": "4⁷", "d": "2", "correct": "a", "explanation": "aᵐ × aⁿ = aᵐ⁺ⁿ → 2³⁺⁴ = 2⁷ = 128", "difficulty": 2},
            {"text": "Вычислите: 4² − √81", "a": "7", "b": "25", "c": "−1", "d": "9", "correct": "a", "explanation": "16 − 9 = 7", "difficulty": 2},
            {"text": "Чему равно 2⁻³?", "a": "1/8", "b": "−8", "c": "−1/8", "d": "8", "correct": "a", "explanation": "2⁻³ = 1/2³ = 1/8", "difficulty": 2},
            {"text": "√(4×25) = ?", "a": "10", "b": "√100", "c": "20", "d": "29", "correct": "a", "explanation": "√100 = 10", "difficulty": 2},
            {"text": "Упростите: (3²)³", "a": "729", "b": "27", "c": "81", "d": "18", "correct": "a", "explanation": "(3²)³ = 3⁶ = 729", "difficulty": 3},
            {"text": "Решите: 2ˣ = 32", "a": "5", "b": "4", "c": "6", "d": "3", "correct": "a", "explanation": "2⁵ = 32 → x = 5", "difficulty": 3},
            {"text": "Упростите: √48", "a": "4√3", "b": "6√2", "c": "8√3", "d": "2√12", "correct": "a", "explanation": "√48 = √(16×3) = 4√3", "difficulty": 3},
            {"text": "Найдите x: x² = 2ˣ, x = 4. Верно?", "a": "Да, 16=16", "b": "Нет, 16≠8", "c": "Нет, 8≠4", "d": "Нет, 4≠2", "correct": "a", "explanation": "4² = 16, 2⁴ = 16 ✓", "difficulty": 3},
        ],
    },
]


async def seed():
    logger.info("[SEED] Starting seed script...")
    async with async_session_factory() as db:
        for topic_data in SEED_DATA:
            # Check if topic already exists
            result = await db.execute(
                select(Topic).where(Topic.title == topic_data["title"])
            )
            topic = result.scalar_one_or_none()

            if topic is None:
                topic = Topic(
                    title=topic_data["title"],
                    theory_text=topic_data["theory"],
                )
                db.add(topic)
                await db.flush()  # get topic.id
                logger.info(f"[SEED] Inserting topic: {topic_data['title']}")
            else:
                logger.info(f"[SEED] Topic already exists, skipping: {topic_data['title']}")

            # Insert questions that don't exist yet
            inserted = 0
            for q in topic_data["questions"]:
                result = await db.execute(
                    select(Question).where(
                        Question.topic_id == topic.id,
                        Question.text == q["text"],
                    )
                )
                if result.scalar_one_or_none() is None:
                    db.add(Question(
                        topic_id=topic.id,
                        text=q["text"],
                        option_a=q["a"],
                        option_b=q["b"],
                        option_c=q["c"],
                        option_d=q["d"],
                        correct_option=q["correct"],
                        explanation=q["explanation"],
                        difficulty=q["difficulty"],
                    ))
                    inserted += 1

            await db.commit()
            logger.info(f"[SEED] Topic '{topic_data['title']}': inserted {inserted} questions")

    logger.info("[SEED] Done!")


if __name__ == "__main__":
    asyncio.run(seed())
