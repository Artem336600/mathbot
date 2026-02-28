from random import randint
from db.models import User, Topic, Question, UserMistake

def create_user(
    id: int,
    username: str = "test_user",
    first_name: str = "Test",
    xp: int = 0,
    level: str = "Новичок",
    is_admin: bool = False
) -> User:
    return User(
        id=id,
        username=username,
        first_name=first_name,
        xp=xp,
        level=level,
        is_admin=is_admin,
    )

def create_topic(
    title: str = "Test Topic",
    is_active: bool = True
) -> Topic:
    return Topic(
        title=title,
        is_active=is_active
    )

def create_question(
    topic_id: int,
    text: str = "What is 2+2?",
    difficulty: int = 1,
    correct_option: str = "a"
) -> Question:
    return Question(
        topic_id=topic_id,
        text=text,
        difficulty=difficulty,
        option_a="4",
        option_b="3",
        option_c="5",
        option_d="6",
        correct_option=correct_option
    )

def create_mistake(
    user_id: int,
    question_id: int,
    is_fixed: bool = False
) -> UserMistake:
    return UserMistake(
        user_id=user_id,
        question_id=question_id,
        is_fixed=is_fixed
    )

