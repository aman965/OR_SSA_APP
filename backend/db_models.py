from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class UploadedDataset(Base):
    __tablename__ = "uploaded_datasets"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    file_path = Column(String)
    file_type = Column(String)
    upload_time = Column(DateTime, default=datetime.datetime.now)

class Snapshot(Base):
    __tablename__ = "snapshots"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    snapshot_id = Column(String)
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"))
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now) 