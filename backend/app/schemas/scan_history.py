from pydantic import BaseModel
from datetime import datetime
from app.schemas.repository import RepositoryResponse

class ScanHistoryBase(BaseModel):
    status: str
    findings_count: int
    scan_duration_ms: int

class ScanHistoryResponse(ScanHistoryBase):
    id: int
    created_at: datetime
    repository: RepositoryResponse

    class Config:
        from_attributes = True
