import time
import re
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Any
from app.database import get_db
from app.models.repository import Repository
from app.models.finding import Finding
from app.models.scan_history import ScanHistory
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.schemas.scan_history import ScanHistoryResponse
from app.api.endpoints.auth import get_current_user
from app.services.github_client import github_client
from app.services.scanner import scan_content
from app.services.ai_analyzer import evaluate_finding_context
from app.services.telegram import send_telegram_alert

router = APIRouter(prefix="/scans", tags=["Scans"])

def parse_github_url(url: str) -> tuple:
    """
    Parses owner and repo name from a typical GitHub URL:
    https://github.com/owner/repo -> (owner, repo)
    """
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")
    
    owner = match.group(1)
    repo = match.group(2)
    # Remove .git ending if present
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo

# Exclusion Patterns Glob Match
EXCLUSION_PATTERNS = [
    r"node_modules/",
    r"package-lock\.json",
    r"yarn\.lock",
    r"pnpm-lock\.yaml",
    r"\.git/",
    r"\.next/",
    r"dist/",
    r"build/",
    r"\.png$", r"\.jpg$", r"\.jpeg$", r"\.gif$", r"\.ico$", r"\.svg$", r"\.webp$",
    r"\.woff2?$", r"\.ttf$", r"\.eot$",
    r"\.mp[34]$", r"\.wav$", r"\.pdf$", r"\.zip$", r"\.tar\.gz$", r"\.rar$"
]

def is_excluded(file_path: str) -> bool:
    for pattern in EXCLUSION_PATTERNS:
        if re.search(pattern, file_path, re.IGNORECASE):
            return True
    return False

def scan_commit_history_diffs(repo, db) -> int:
    """
    Traverses recent commit hashes, fetches diff patches of additions,
    scans lines, and records new findings tagged with commit SHA context.
    """
    import logging
    logger = logging.getLogger(__name__)
    findings_created = 0
    commits = github_client.fetch_recent_commits(repo.owner, repo.name, count=10)
    
    for c in commits:
        commit_sha = c.get("sha")
        if not commit_sha:
            continue
            
        commit_details = github_client.fetch_commit_details(repo.owner, repo.name, commit_sha)
        files_mutated = commit_details.get("files", [])
        
        for f in files_mutated:
            file_path = f.get("filename", "")
            patch = f.get("patch", "")
            
            if not file_path or not patch or is_excluded(file_path):
                continue
                
            # Filter lines starting with '+' indicating additions in commit diffs
            added_lines = []
            for line_idx, line in enumerate(patch.splitlines()):
                if line.startswith("+") and not line.startswith("+++"):
                    added_lines.append(line[1:]) # Strip out leading '+'
                    
            if not added_lines:
                continue
                
            content = "\n".join(added_lines)
            raw_findings = scan_content(content, file_path=file_path)
            
            for rf in raw_findings:
                # Check for duplicates
                exists = db.query(Finding).filter(
                    Finding.repository_id == repo.id,
                    Finding.file_path == rf["file_path"],
                    Finding.secret_type == rf["secret_type"],
                    Finding.is_resolved == False
                ).first()
                
                if exists:
                    continue
                    
                ai_desc = evaluate_finding_context(rf)
                
                new_finding = Finding(
                    secret_type=rf["secret_type"],
                    secret_value=rf["raw_secret"], # Unmasked raw secret
                    severity=rf["severity"],
                    confidence=rf["confidence"],
                    file_path=rf["file_path"],
                    line_number=rf["line_number"],
                    commit_hash=commit_sha,
                    snippet=rf["snippet"],
                    ai_analysis=ai_desc,
                    repository_id=repo.id
                )
                db.add(new_finding)
                db.commit()
                db.refresh(new_finding)
                findings_created += 1
                
                repo_data = {
                    "name": repo.name,
                    "owner": repo.owner,
                    "url": repo.url
                }
                
                finding_data = {
                    "id": new_finding.id,
                    "secret_type": new_finding.secret_type,
                    "secret_value": rf["raw_secret"],
                    "severity": new_finding.severity,
                    "confidence": new_finding.confidence,
                    "file_path": new_finding.file_path,
                    "line_number": new_finding.line_number,
                    "snippet": new_finding.snippet,
                    "ai_analysis": new_finding.ai_analysis
                }
                send_telegram_alert(finding_data, repo_data)
                
    return findings_created

def execute_repository_scan(repo_id: int, db_session_factory) -> None:
    """
    Synchronous scanning function suitable for running in background threads.
    Fetches target files recursively, runs the scanner patterns,
    evaluates findings context via AI, saves results, and sends notifications.
    Supports checkpoint resume scanning using latest commit SHAs.
    """
    db = db_session_factory()
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        db.close()
        return

    # Fetch latest commit SHA to check for changes
    latest_commit = github_client.get_latest_commit_sha(repo.owner, repo.name)
    if latest_commit and repo.last_scanned_commit == latest_commit:
        # Checkpoint matches, skip scanning to avoid duplicates and save API limits
        scan_log = ScanHistory(
            repository_id=repo.id,
            status="completed",
            findings_count=0,
            scan_duration_ms=0
        )
        db.add(scan_log)
        db.commit()
        db.close()
        return

    # Log scan initiation
    scan_log = ScanHistory(repository_id=repo.id, status="running", findings_count=0, scan_duration_ms=0)
    db.add(scan_log)
    db.commit()
    db.refresh(scan_log)

    start_time = time.time()
    findings_created = 0
    
    try:
        # Scan Git Commit Diff Logs (Historical Traversal)
        diff_findings = scan_commit_history_diffs(repo, db)
        findings_created += diff_findings
        
        # Scan File Tree (Current State Snapshot)
        files = github_client.fetch_repo_files_recursive(repo.owner, repo.name)
        
        for file in files:
            file_path = file.get("path")
            blob_url = file.get("url")
            
            if is_excluded(file_path):
                continue
                
            content = github_client.fetch_file_content(blob_url)
            if not content:
                continue
                
            raw_findings = scan_content(content, file_path=file_path)
            
            for rf in raw_findings:
                # Deduplicate existing unresolved secret finding in this repository
                exists = db.query(Finding).filter(
                    Finding.repository_id == repo.id,
                    Finding.file_path == rf["file_path"],
                    Finding.secret_type == rf["secret_type"],
                    Finding.is_resolved == False
                ).first()
                
                if exists:
                    continue
                
                # Fetch AI contextual analysis
                ai_desc = evaluate_finding_context(rf)
                
                new_finding = Finding(
                    secret_type=rf["secret_type"],
                    secret_value=rf["raw_secret"], # Unmasked raw value
                    severity=rf["severity"],
                    confidence=rf["confidence"],
                    file_path=rf["file_path"],
                    line_number=rf["line_number"],
                    snippet=rf["snippet"],
                    ai_analysis=ai_desc,
                    repository_id=repo.id
                )
                db.add(new_finding)
                db.commit()
                db.refresh(new_finding)
                findings_created += 1
                
                # Send alert (raw secret passed for snippet inspection, details inside finding)
                # Ensure the repository parameters are loaded
                repo_data = {
                    "name": repo.name,
                    "owner": repo.owner,
                    "url": repo.url
                }
                
                finding_data = {
                    "id": new_finding.id,
                    "secret_type": new_finding.secret_type,
                    "secret_value": rf["raw_secret"], # Telegram gets raw for masking if needed
                    "severity": new_finding.severity,
                    "confidence": new_finding.confidence,
                    "file_path": new_finding.file_path,
                    "line_number": new_finding.line_number,
                    "snippet": new_finding.snippet,
                    "ai_analysis": new_finding.ai_analysis
                }
                
                send_telegram_alert(finding_data, repo_data)

        # Update last scanned commit SHA checkpoint
        if latest_commit:
            repo.last_scanned_commit = latest_commit

        # Mark scan log completed
        scan_log.status = "completed"
        scan_log.findings_count = findings_created
        scan_log.scan_duration_ms = int((time.time() - start_time) * 1000)
        db.commit()
        
    except Exception as e:
        scan_log.status = "failed"
        db.commit()
        # Log the error
        import logging
        logging.getLogger(__name__).error(f"Error during repository scan: {str(e)}")
    finally:
        db.close()

@router.post("/repositories", response_model=RepositoryResponse)
def register_repository(repo_in: RepositoryCreate, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    # Clean and parse URL
    owner, name = parse_github_url(repo_in.url)
    
    # Check if repository already exists
    existing = db.query(Repository).filter(Repository.url == repo_in.url).first()
    if existing:
        return existing
        
    # Get metadata from GitHub (or default if offline/failed)
    meta = github_client.get_repo_metadata(owner, name)
    
    repo = Repository(
        name=meta.get("name", name),
        owner=meta.get("owner", owner),
        stars=meta.get("stars", repo_in.stars or 0),
        url=repo_in.url,
        is_monitored=1
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo

@router.get("/repositories", response_model=List[RepositoryResponse])
def get_monitored_repositories(db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    return db.query(Repository).filter(Repository.is_monitored == 1).all()

@router.post("/repositories/{repo_id}/scan", response_model=ScanHistoryResponse)
def trigger_scan(
    repo_id: int, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db), 
    current_user: Any = Depends(get_current_user)
):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    # Create immediate scan record in database
    scan_log = ScanHistory(
        repository_id=repo.id,
        status="pending",
        findings_count=0,
        scan_duration_ms=0
    )
    db.add(scan_log)
    db.commit()
    db.refresh(scan_log)
    
    # Use FastAPI BackgroundTasks to process scanning asynchronously without celery dependency block
    from app.database import SessionLocal
    background_tasks.add_task(execute_repository_scan, repo.id, SessionLocal)
    
    return scan_log

@router.get("/history", response_model=List[ScanHistoryResponse])
def get_scan_history(db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    return db.query(ScanHistory).order_by(ScanHistory.created_at.desc()).limit(100).all()

@router.post("/webhook")
def receive_github_webhook(payload: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Receives live push updates via GitHub Webhook, registers repo targets if they do
    not exist in database configurations, and triggers scans asynchronously.
    """
    repository_meta = payload.get("repository", {})
    repo_url = repository_meta.get("html_url")
    repo_name = repository_meta.get("name")
    repo_owner = repository_meta.get("owner", {}).get("login") or repository_meta.get("owner", {}).get("name")
    
    if not repo_url or not repo_name or not repo_owner:
        raise HTTPException(status_code=400, detail="Invalid push webhook payload structure")
        
    repo = db.query(Repository).filter(Repository.url == repo_url).first()
    if not repo:
        repo = Repository(
            name=repo_name,
            owner=repo_owner,
            stars=repository_meta.get("stargazers_count", 0),
            url=repo_url,
            is_monitored=1
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        
    # Launch scan in background task
    from app.database import SessionLocal
    background_tasks.add_task(execute_repository_scan, repo.id, SessionLocal)
    
    return {"status": "webhook_queued", "repository_id": repo.id}
