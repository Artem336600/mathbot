from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="Telegram user ID")
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), default="")
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[str] = mapped_column(String(32), default="Новичок")
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    accuracy_rate: Mapped[float] = mapped_column(Float, default=0.0)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    mistakes: Mapped[list["UserMistake"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    progress: Mapped[list["UserProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} level={self.level} xp={self.xp}>"


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    theory_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    questions: Mapped[list["Question"]] = relationship(back_populates="topic", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Topic id={self.id} title={self.title!r}>"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, comment="1=easy, 2=medium, 3=hard")
    option_a: Mapped[str] = mapped_column(String(256), nullable=False)
    option_b: Mapped[str] = mapped_column(String(256), nullable=False)
    option_c: Mapped[str] = mapped_column(String(256), nullable=False)
    option_d: Mapped[str] = mapped_column(String(256), nullable=False)
    correct_option: Mapped[str] = mapped_column(String(1), nullable=False, comment="a/b/c/d")
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    topic: Mapped["Topic"] = relationship(back_populates="questions")
    mistakes: Mapped[list["UserMistake"]] = relationship(back_populates="question", cascade="all, delete-orphan")
    progress: Mapped[list["UserProgress"]] = relationship(back_populates="question", cascade="all, delete-orphan")

    def get_options(self) -> dict:
        return {
            "a": self.option_a,
            "b": self.option_b,
            "c": self.option_c,
            "d": self.option_d,
        }

    def __repr__(self) -> str:
        return f"<Question id={self.id} topic_id={self.topic_id} difficulty={self.difficulty}>"


class UserMistake(Base):
    __tablename__ = "user_mistakes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="mistakes")
    question: Mapped["Question"] = relationship(back_populates="mistakes")

    def __repr__(self) -> str:
        return f"<UserMistake id={self.id} user_id={self.user_id} fixed={self.is_fixed}>"


class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="progress")
    question: Mapped["Question"] = relationship(back_populates="progress")

    def __repr__(self) -> str:
        return f"<UserProgress id={self.id} user_id={self.user_id} correct={self.is_correct}>"


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="'topic' or 'question'")
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    attachment_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="'photo' or 'document'")
    file_key: Mapped[str] = mapped_column(String(512), nullable=False)
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_entity_type_id", "entity_type", "entity_id"),
    )

    def __repr__(self) -> str:
        return f"<Attachment id={self.id} entity={self.entity_type}:{self.entity_id} type={self.attachment_type}>"
