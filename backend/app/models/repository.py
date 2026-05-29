from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    owner = Column(String, index=True, nullable=False)
    stars = Column(Integer, default=0)
    url = Column(String, unique=True, index=True, nullable=False)
    is_monitored = Column(Integer, default=1) # 1 = yes, 0 = no
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    findings = relationship("Finding", back_populates="repository", cascade="all, delete-orphan")
    scans = relationship("ScanHistory", back_populates="repository", cascade="all, delete-orphan")
