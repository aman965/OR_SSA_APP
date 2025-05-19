from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from backend.db_models import Base, Scenario, Action, ActionOwner
import os

# Get the absolute path to the database file
db_path = os.path.join(os.path.dirname(__file__), "app.db")
DATABASE_URL = f"sqlite:///{db_path}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Get a new database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e


# ── Scenario helpers ──────────────────────────────────────────────────────
def list_snapshots(db: Session):
    from backend.db_models import Snapshot
    return db.query(Snapshot).order_by(Snapshot.created_at.desc()).all()

def list_scenarios_for_snapshot(db: Session, snapshot_id: int):
    return (
        db.query(Scenario)
          .filter(Scenario.snapshot_id == snapshot_id)
          .order_by(Scenario.created_at.asc())
          .all()
    )

def create_scenario(db: Session, *, name: str, description: str | None,
                    snapshot_id: int) -> Scenario:
    scn = Scenario(name=name,
                   description=description,
                   snapshot_id=snapshot_id)
    db.add(scn)
    db.commit()
    db.refresh(scn)
    return scn

# ── Action helpers (very thin layer for now) ──────────────────────────────
def create_action(db: Session, *, name: str,
                  owner_type: ActionOwner, owner_id: int, payload: str | None):
    action = Action(name=name,
                    owner_type=owner_type,
                    owner_id=owner_id,
                    payload=payload)
    db.add(action)
    db.commit()
    return action