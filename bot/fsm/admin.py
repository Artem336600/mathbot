"""Admin FSM states for content management and broadcast."""
from aiogram.fsm.state import State, StatesGroup


class AddTopicFSM(StatesGroup):
    waiting_title = State()
    waiting_theory = State()


class EditTopicFSM(StatesGroup):
    waiting_new_title = State()
    waiting_new_theory = State()


class AddQuestionFSM(StatesGroup):
    waiting_topic_choice = State()
    waiting_text = State()
    waiting_option_a = State()
    waiting_option_b = State()
    waiting_option_c = State()
    waiting_option_d = State()
    waiting_correct = State()
    waiting_explanation = State()
    waiting_difficulty = State()


class BroadcastFSM(StatesGroup):
    waiting_message = State()
    confirming = State()
