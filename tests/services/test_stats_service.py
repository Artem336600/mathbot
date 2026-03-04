import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User
from services.stats_service import award_xp, update_streak, update_accuracy
from tests.factories import create_user

@pytest.mark.asyncio
async def test_award_xp_normal(db: AsyncSession):
    # Setup
    user = create_user(id=1, xp=0, level="Новичок")
    db.add(user)
    await db.commit()

    # Action
    result = await award_xp(1, 50, db)

    # Assert
    assert result["xp"] == 50
    assert result["level"] == "Новичок"
    assert not result["level_up"]

    db_user = await db.get(User, 1)
    assert db_user.xp == 50

@pytest.mark.asyncio
async def test_award_xp_level_up(db: AsyncSession):
    # Setup
    user = create_user(id=2, xp=90, level="Новичок")
    db.add(user)
    await db.commit()

    # Action
    result = await award_xp(2, 20, db)

    # Assert
    assert result["xp"] == 110
    assert result["level"] == "Ученик"
    assert result["level_up"]

    db_user = await db.get(User, 2)
    assert db_user.level == "Ученик"

@pytest.mark.asyncio
async def test_award_xp_exact_boundary(db: AsyncSession):
    # Setup
    user = create_user(id=3, xp=90, level="Новичок")
    db.add(user)
    await db.commit()

    # Action: 90 + 10 = 100 (threshold for "Ученик")
    result = await award_xp(3, 10, db)

    # Assert
    assert result["xp"] == 100
    assert result["level"] == "Ученик"
    assert result["level_up"]
