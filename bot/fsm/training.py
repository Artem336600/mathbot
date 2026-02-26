"""Training FSM states."""
from aiogram.fsm.state import State, StatesGroup


class TrainingState(StatesGroup):
    selecting_topics = State()
    in_progress = State()
