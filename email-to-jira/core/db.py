"""SQLite engine and session helpers."""
from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from core.config import settings

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{settings.database_path}",
            connect_args={"check_same_thread": False},
        )
    return _engine


def set_engine(engine) -> None:
    """Used by tests to point the app at an in-memory/temp database."""
    global _engine
    _engine = engine


def init_db(engine=None) -> None:
    SQLModel.metadata.create_all(engine or get_engine())


@contextmanager
def session_scope() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
        session.commit()
