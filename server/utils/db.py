"""SQLAlchemy engine + session management with savepoint-based episode isolation."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/env.db")

# SQLite needs check_same_thread=False for multi-session use
_connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager providing a database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class TransactionManager:
    """Manages per-episode database transactions using savepoints.

    Provides rollback isolation so each episode starts from a clean state.
    """

    def __init__(self) -> None:
        self._session: Session | None = None
        self._in_episode: bool = False

    def get_session(self) -> Session:
        """Return the active session, creating one if needed."""
        if self._session is None:
            self._session = SessionLocal()
        return self._session

    def begin_episode(self) -> None:
        """Create a savepoint for the episode. Rollback reverts DB to this point."""
        session = self.get_session()
        if not self._in_episode:
            session.begin_nested()  # SAVEPOINT
            self._in_episode = True

    def rollback_episode(self) -> None:
        """Roll back to the savepoint, undoing all changes from this episode."""
        if self._session is not None and self._in_episode:
            try:
                self._session.rollback()
            except Exception:
                pass
            self._in_episode = False

    def commit_episode(self) -> None:
        """Commit the episode's changes permanently."""
        if self._session is not None and self._in_episode:
            self._session.commit()
            self._in_episode = False

    def close(self) -> None:
        """Close the session entirely."""
        if self._session is not None:
            self._session.close()
            self._session = None
            self._in_episode = False
