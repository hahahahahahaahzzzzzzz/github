from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class ScanHistory(Base):
    __tablename__ = "scan_histories"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="completed") # pending, running, completed, failed
    findings_count = Column(Integer, default=0)
    scan_duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    repository = relationship("Repository", back_populates="scans")
