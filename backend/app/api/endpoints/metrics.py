from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from app.database import get_db
from app.models.finding import Finding
from app.models.repository import Repository
from app.schemas.finding import FindingMetricOverview
from app.api.endpoints.auth import get_current_user

router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.get("/overview", response_model=FindingMetricOverview)
def get_metrics_overview(db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    # Total count
    total_leaks = db.query(Finding).count()
    
    # Severity distribution
    critical_count = db.query(Finding).filter(Finding.severity == "CRITICAL").count()
    high_count = db.query(Finding).filter(Finding.severity == "HIGH").count()
    medium_count = db.query(Finding).filter(Finding.severity == "MEDIUM").count()
    low_count = db.query(Finding).filter(Finding.severity == "LOW").count()
    
    # Resolved count
    resolved_count = db.query(Finding).filter(Finding.is_resolved == True).count()
    
    # Secret type distribution
    type_stats = db.query(Finding.secret_type, func.count(Finding.id)).group_by(Finding.secret_type).all()
    types_distribution = {t[0]: t[1] for t in type_stats}
    
    # Severity list for graphing
    severity_distribution = {
        "CRITICAL": critical_count,
        "HIGH": high_count,
        "MEDIUM": medium_count,
        "LOW": low_count
    }
    
    # Disclosure distribution
    disclosure_stats = db.query(Finding.disclosure_status, func.count(Finding.id)).group_by(Finding.disclosure_status).all()
    disclosure_distribution = {d[0]: d[1] for d in disclosure_stats}
    
    return {
        "total_leaks": total_leaks,
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "resolved_count": resolved_count,
        "types_distribution": types_distribution,
        "severity_distribution": severity_distribution,
        "disclosure_distribution": disclosure_distribution
    }
