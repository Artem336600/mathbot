import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User
from services.stats_service import _calc_level, _xp_to_next_level, get_xp_bar, award_xp
from tests.factories import create_user

# Strategies
xp_st = st.integers(min_value=0, max_value=1_000_000)
award_amount_st = st.integers(min_value=0, max_value=1000)

@given(xp=xp_st)
def test_calc_level_fuzz(xp):
    level = _calc_level(xp)
    assert isinstance(level, str)
    assert level in ["Новичок", "Ученик", "Практик", "Профессионал"]
    
    if xp < 100:
        assert level == "Новичок"
    elif xp < 300:
        assert level == "Ученик"
    elif xp < 600:
        assert level == "Практик"
    else:
        assert level == "Профессионал"

@given(xp=xp_st)
def test_xp_to_next_level_fuzz(xp):
    next_level, current, needed = _xp_to_next_level(xp)
    assert isinstance(next_level, str)
    assert 0 <= current
    assert needed > 0
    
    # Invariants
    if xp < 600:
        assert current + (xp - current) == xp
        # needed is the distance between levels
        assert needed in [100, 200, 300] 

@given(xp=xp_st, bar_length=st.integers(min_value=1, max_value=100))
def test_get_xp_bar_fuzz(xp, bar_length):
    bar = get_xp_bar(xp, bar_length)
    assert len(bar) == bar_length
    assert set(bar).issubset({"█", "░"})

@pytest.mark.asyncio
@given(xp=xp_st, amount=award_amount_st)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_award_xp_fuzz(db: AsyncSession, xp, amount):
    # Setup - we need a user in the DB
    user_id = 1000 + xp % 10000 
    user = create_user(id=user_id, xp=xp, level=_calc_level(xp))
    db.add(user)
    await db.commit()
    
    # Action
    result = await award_xp(user_id, amount, db)
    
    # Assert
    assert result["xp"] == xp + amount
    assert result["level"] == _calc_level(xp + amount)
    
    # Verify DB
    db_user = await db.get(User, user_id)
    assert db_user.xp == xp + amount
    
    # Cleanup for next iteration
    await db.delete(db_user)
    await db.commit()
