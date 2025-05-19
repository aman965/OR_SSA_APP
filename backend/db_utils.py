"""
Helper functions that operate *on* a SQLAlchemy Session.
They delegate all engine / session creation to backend.db
so the whole app shares a single database file.
"""

from sqlalchemy.orm import Session
from backend.db import SessionLocal            # <- single source of truth
from backend.db_models import (
    Snapshot,
    Scenario,
    Action,
    ActionOwner,
)

# ────────────────────────────────────────────────────────────────────────
# session helper (kept for backward-compat with pages that import it)
# -----------------------------------------------------------------------
def get_session() -> Session:
    """
    Return a brand-new Session.
    (Uses the SessionLocal defined in backend.db, so every part of the
    app talks to the same database.)
    """
    return SessionLocal()


# ────────────────────────────────────────────────────────────────────────
# CRUD utilities
# -----------------------------------------------------------------------
def list_snapshots(db: Session):
    return db.query(Snapshot).order_by(Snapshot.created_at.desc()).all()


def list_scenarios_for_snapshot(db: Session, snapshot_id: int):
    return (
        db.query(Scenario)
        .filter(Scenario.snapshot_id == snapshot_id)
        .order_by(Scenario.created_at.asc())
        .all()
    )


def create_snapshot(
    db: Session, *, name: str, dataset_id: int, file_path: str
) -> Snapshot:
    snap = Snapshot(
        name=name,
        dataset_id=dataset_id,
        file_path=file_path,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def create_scenario(
    db: Session, *, name: str, description: str | None, snapshot_id: int
) -> Scenario:
    scn = Scenario(name=name, description=description, snapshot_id=snapshot_id)
    db.add(scn)
    db.commit()
    db.refresh(scn)
    return scn


def create_action(
    db: Session,
    *,
    name: str,
    owner_type: ActionOwner,
    owner_id: int,
    payload: str | None,
) -> Action:
    act = Action(
        name=name,
        owner_type=owner_type,
        owner_id=owner_id,
        payload=payload,
    )
    db.add(act)
    db.commit()
    return act
