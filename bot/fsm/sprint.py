"""Sprint FSM states."""
from aiogram.fsm.state import State, StatesGroup


class SprintState(StatesGroup):
    in_progress = State()
