from __future__ import annotations

import logging
import time
from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

log = logging.getLogger(__name__)

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def init_db(retries: int = 30, delay: float = 2.0) -> None:
    """Wait for Postgres to accept connections, then create tables."""
    from . import models  # noqa: F401  (register tables)

    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception as exc:  # pragma: no cover - depends on environment
            if attempt == retries:
                raise
            log.info("Database not ready (%s); retrying in %ss", exc.__class__.__name__, delay)
            time.sleep(delay)
    Base.metadata.create_all(engine)
