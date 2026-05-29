from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

from sqlalchemy.ext.hybrid import hybrid_property
from app.services.crypto import encrypt_value, decrypt_value

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    secret_type = Column(String, index=True, nullable=False) # e.g. AWS_KEY, STRIPE_KEY, etc.
    _secret_value = Column("secret_value", String, nullable=False) # Encrypted secret at rest
    severity = Column(String, index=True, nullable=False)    # CRITICAL, HIGH, MEDIUM, LOW, INFO

    @hybrid_property
    def secret_value(self) -> str:
        return decrypt_value(self._secret_value)

    @secret_value.setter
    def secret_value(self, value: str) -> None:
        self._secret_value = encrypt_value(value)
    confidence = Column(Float, default=0.5)                 # Confidence score (0.0 to 1.0)
    file_path = Column(String, index=True, nullable=False)   # Relative path in repo
    line_number = Column(Integer, nullable=False)
    commit_hash = Column(String, index=True)
    snippet = Column(Text, nullable=True)                    # Surrounding lines of code
    ai_analysis = Column(Text, nullable=True)                # AI remediation and justification
    disclosure_status = Column(String, default="Pending")    # Pending, Contacted, Acknowledged, Fixed, Closed
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    repository = relationship("Repository", back_populates="findings")
