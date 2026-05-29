from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from app.database import get_db
from app.models.finding import Finding
from app.models.repository import Repository
from app.schemas.finding import FindingResponse, FindingUpdate
from app.api.endpoints.auth import get_current_user
from app.services.ai_analyzer import evaluate_finding_context

router = APIRouter(prefix="/findings", tags=["Findings"])

@router.get("/", response_model=List[FindingResponse])
def get_findings(
    db: Session = Depends(get_db),
    severity: Optional[str] = Query(None, description="Filter by CRITICAL, HIGH, etc."),
    disclosure_status: Optional[str] = Query(None, description="Filter by Pending, Fixed, etc."),
    is_resolved: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search by repository name or file path"),
    skip: int = 0,
    limit: int = 50,
    current_user: Any = Depends(get_current_user)
):
    query = db.query(Finding).join(Repository)
    
    if severity:
        query = query.filter(Finding.severity == severity.upper())
    if disclosure_status:
        query = query.filter(Finding.disclosure_status == disclosure_status)
    if is_resolved is not None:
        query = query.filter(Finding.is_resolved == is_resolved)
    if search:
        query = query.filter(
            (Repository.name.ilike(f"%{search}%")) | 
            (Finding.file_path.ilike(f"%{search}%")) |
            (Finding.secret_type.ilike(f"%{search}%"))
        )
        
    return query.order_by(Finding.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{finding_id}", response_model=FindingResponse)
def get_finding_by_id(finding_id: int, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding

@router.patch("/{finding_id}", response_model=FindingResponse)
def update_finding(
    finding_id: int,
    finding_in: FindingUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    if finding_in.is_resolved is not None:
        finding.is_resolved = finding_in.is_resolved
    if finding_in.disclosure_status is not None:
        finding.disclosure_status = finding_in.disclosure_status
    if finding_in.ai_analysis is not None:
        finding.ai_analysis = finding_in.ai_analysis
        
    db.commit()
    db.refresh(finding)
    return finding

@router.post("/{finding_id}/analyze-ai", response_model=FindingResponse)
def trigger_ai_analysis(finding_id: int, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    # Compile simple contextual text for the analyzer
    finding_data = {
        "secret_type": finding.secret_type,
        "severity": finding.severity,
        "snippet": finding.snippet,
        "confidence": finding.confidence
    }
    
    ai_desc = evaluate_finding_context(finding_data)
    finding.ai_analysis = ai_desc
    db.commit()
    db.refresh(finding)
    return finding
