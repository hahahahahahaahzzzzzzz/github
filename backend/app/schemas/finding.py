from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from app.schemas.repository import RepositoryResponse

class FindingBase(BaseModel):
    secret_type: str
    secret_value: str
    severity: str
    confidence: float
    file_path: str
    line_number: int
    commit_hash: Optional[str] = None
    snippet: Optional[str] = None
    ai_analysis: Optional[str] = None
    disclosure_status: Optional[str] = "Pending"
    is_resolved: Optional[bool] = False

class FindingCreate(FindingBase):
    repository_id: int

class FindingUpdate(BaseModel):
    disclosure_status: Optional[str] = None
    is_resolved: Optional[bool] = None
    ai_analysis: Optional[str] = None

class FindingResponse(FindingBase):
    id: int
    created_at: datetime
    repository: RepositoryResponse

    class Config:
        from_attributes = True

class FindingMetricOverview(BaseModel):
    total_leaks: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    resolved_count: int
    types_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
    disclosure_distribution: Dict[str, int]
