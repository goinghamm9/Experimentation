import sys
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import db as core_db  # noqa: E402


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    core_db.set_engine(engine)
    yield engine
    core_db.set_engine(None)


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session
        session.commit()
