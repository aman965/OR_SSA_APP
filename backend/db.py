"""
Tiny SQLAlchemy bootstrap used by the Streamlit pages.
Keeps the ORM completely separate from your Django models.
"""

from __future__ import annotations

import os
from pathlib import Path
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_models import Base   # same Base you already edited

# ────────────────────────────────────────────────────────────────────────
# Database URL
# • Uses env var if present (e.g. postgres://…)
# • Falls back to a project-local SQLite file:  ./data/ssa_app.db
# -----------------------------------------------------------------------
DB_URL = os.getenv("SSA_APP_SQLA_DB", "sqlite:///data/ssa_app.db")

# Make sure the folder for SQLite exists
if DB_URL.startswith("sqlite:///"):
    db_file = Path(DB_URL.replace("sqlite:///", "", 1))
    db_file.parent.mkdir(parents=True, exist_ok=True)

# SQLAlchemy engine & session factory
engine = create_engine(DB_URL, future=True, echo=False)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,   # ← ADD THIS
)

# Create tables if they’re missing
Base.metadata.create_all(bind=engine)

# Public helper used by Streamlit pages
@contextmanager
def get_session():
    """Context-manager that yields a DB session and commits / rolls back."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:           # noqa: BLE001  (let caller see the error)
        session.rollback()
        raise
    finally:
        session.close()
