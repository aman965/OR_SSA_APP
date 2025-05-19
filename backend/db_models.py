from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
import datetime as _dt
import enum

Base = declarative_base()


# ────────────────────────────────────────────────────────────
# Existing tables
# ────────────────────────────────────────────────────────────
class UploadedDataset(Base):
    __tablename__ = "uploaded_datasets"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    file_path = Column(String)
    file_type = Column(String)
    upload_time = Column(DateTime, default=_dt.datetime.now)


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    snapshot_id = Column(String)  # external ID if any
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"))
    file_path = Column(String)
    created_at = Column(DateTime, default=_dt.datetime.now)
    # The `scenarios` relationship is attached *below* once Scenario is declared


# ────────────────────────────────────────────────────────────
# New tables
# ────────────────────────────────────────────────────────────
class Scenario(Base):
    """
    A Scenario is a child of a Snapshot.
    (Later you can add Stage objects chained to Scenario.)
    """
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    snapshot_id = Column(
        Integer,
        ForeignKey("snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime, default=_dt.datetime.utcnow)

    # ORM link to parent
    snapshot = relationship("Snapshot", back_populates="scenarios")

    __table_args__ = (
        UniqueConstraint("snapshot_id", "name",
                         name="uq_scenario_name_per_snapshot"),
    )


class ActionOwner(enum.Enum):
    SNAPSHOT = "snapshot"
    SCENARIO = "scenario"
    # STAGE   = "stage"   # uncomment once Stage model exists


class Action(Base):
    """
    Generic registry of user-triggerable actions.
    `owner_type` tells whether the action belongs to a snapshot,
    a scenario, (or later) a stage.
    """
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    owner_type = Column(Enum(ActionOwner), nullable=False)
    owner_id = Column(Integer, nullable=False)
    payload = Column(Text)  # free-form JSON / text
    created_at = Column(DateTime, default=_dt.datetime.utcnow)


# ────────────────────────────────────────────────────────────
# Attach the inverse relationship now that Scenario exists
# ────────────────────────────────────────────────────────────
Snapshot.scenarios = relationship(
    "Scenario",
    order_by=Scenario.id,
    cascade="all, delete-orphan",
    back_populates="snapshot",
)
