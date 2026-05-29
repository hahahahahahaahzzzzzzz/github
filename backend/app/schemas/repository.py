from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class RepositoryBase(BaseModel):
    name: str
    owner: str
    url: str
    stars: Optional[int] = 0

class RepositoryCreate(RepositoryBase):
    pass

class RepositoryResponse(RepositoryBase):
    id: int
    is_monitored: int
    created_at: datetime

    class Config:
        from_attributes = True
