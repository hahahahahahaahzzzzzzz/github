import time
import os
import logging
import threading
from app.config import settings
from app.models.repository import Repository
from app.services.github_client import github_client
from app.api.endpoints.scans import execute_repository_scan

logger = logging.getLogger(__name__)

# File path to persist the sequential public repository crawl state
STATE_FILE = "public_crawler_state.txt"

def load_since_id() -> int:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
        except Exception as e:
            logger.error(f"Failed to load since_id state: {str(e)}")
    # Safe default starting ID (around mid-2023 or random midpoint)
    return 650000000

def save_since_id(since_id: int):
    try:
        with open(STATE_FILE, "w") as f:
            f.write(str(since_id))
    except Exception as e:
        logger.error(f"Failed to save since_id state: {str(e)}")

def run_user_repo_scanner(db_session_factory):
    """
    Background daemon thread that sweeps configured user repositories.
    """
    logger.info("Automatic User GitHub Repositories Discovery and Scan daemon started.")
    while True:
        db = db_session_factory()
        try:
            logger.info("User Auto-scanner: Querying GitHub for user repositories...")
            repos_discovered = github_client.get_user_repositories()
            logger.info(f"User Auto-scanner: Discovered {len(repos_discovered)} repositories from GitHub.")
            
            # Register new ones
            new_repos_count = 0
            for r_meta in repos_discovered:
                repo_url = r_meta["url"]
                repo = db.query(Repository).filter(Repository.url == repo_url).first()
                if not repo:
                    repo = Repository(
                        name=r_meta["name"],
                        owner=r_meta["owner"],
                        stars=r_meta["stars"],
                        url=repo_url,
                        is_monitored=1
                    )
                    db.add(repo)
                    db.commit()
                    db.refresh(repo)
                    logger.info(f"User Auto-scanner: Registered new repository: {repo.owner}/{repo.name}")
                    new_repos_count += 1
            
            if new_repos_count > 0:
                logger.info(f"User Auto-scanner: Registered {new_repos_count} new repositories.")
            
            # Fetch all user-owned/monitored repositories
            # Filter by matching URLs from settings.github_token_list where possible,
            # or simply scan all registered monitored assets.
            monitored_repos = db.query(Repository).filter(Repository.is_monitored == 1).all()
            for repo in monitored_repos:
                try:
                    # Execute checkpoint verification and scanning
                    execute_repository_scan(repo.id, db_session_factory)
                except Exception as scan_err:
                    logger.error(f"User Auto-scanner: Failed to scan {repo.owner}/{repo.name}: {str(scan_err)}")
                    
        except Exception as e:
            logger.error(f"User Auto-scanner Daemon Error: {str(e)}")
        finally:
            db.close()
            
        time.sleep(settings.AUTO_SCAN_INTERVAL_SECONDS)

def run_public_repo_harvester(db_session_factory):
    """
    Background daemon thread running 24/7.
    Continually discovers and scans public repos from GitHub Live Push Feed
    and crawls random public repos sequentially.
    """
    logger.info("Public GitHub Leak Harvester Daemon started.")
    since_id = load_since_id()
    
    while True:
        if not settings.SCAN_PUBLIC_REPOS:
            time.sleep(10)
            continue
            
        db = db_session_factory()
        try:
            logger.info("Public Harvester: Querying GitHub public events...")
            public_repos = github_client.get_public_events()
            logger.info(f"Public Harvester: Extracted {len(public_repos)} active repositories from live push activity.")
            
            # Query sequentially as well to get random new repositories
            logger.info(f"Public Harvester: Querying random sequential public repositories from ID {since_id}...")
            seq_repos, next_since = github_client.get_public_repositories(since_id)
            if seq_repos:
                public_repos.extend(seq_repos)
                since_id = next_since
                save_since_id(since_id)
                logger.info(f"Public Harvester: Added {len(seq_repos)} sequential repositories. Next since_id checkpoint: {since_id}")
                
            # Deduplicate the list
            unique_repos = []
            seen_urls = set()
            for pr in public_repos:
                if pr["url"] not in seen_urls:
                    seen_urls.add(pr["url"])
                    unique_repos.append(pr)
                    
            logger.info(f"Public Harvester: Discovering and staging {len(unique_repos)} public repositories for leak scanning.")
            
            # Scan them
            for r_meta in unique_repos:
                repo_url = r_meta["url"]
                repo = db.query(Repository).filter(Repository.url == repo_url).first()
                if not repo:
                    repo = Repository(
                        name=r_meta["name"],
                        owner=r_meta["owner"],
                        stars=r_meta["stars"],
                        url=repo_url,
                        is_monitored=1
                    )
                    db.add(repo)
                    db.commit()
                    db.refresh(repo)
                    
                # Scan repository
                try:
                    logger.info(f"Public Harvester: Harvesting security intelligence on {repo.owner}/{repo.name}...")
                    execute_repository_scan(repo.id, db_session_factory)
                except Exception as e:
                    logger.error(f"Public Harvester: Scan failed for {repo.owner}/{repo.name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Public Harvester Daemon Error: {str(e)}")
        finally:
            db.close()
            
        logger.info(f"Public Harvester: Cycle complete. Sleeping for {settings.SCAN_PUBLIC_INTERVAL_SECONDS} seconds.")
        time.sleep(settings.SCAN_PUBLIC_INTERVAL_SECONDS)

def start_auto_scan_daemon(db_session_factory) -> None:
    """
    Spawns all auto-scanner and threat intelligence harvester daemon threads.
    """
    # 1. Start User Repository scanner daemon
    user_thread = threading.Thread(
        target=run_user_repo_scanner,
        args=(db_session_factory,),
        daemon=True
    )
    user_thread.start()
    
    # 2. Start Public GitHub Leak Harvester daemon
    public_thread = threading.Thread(
        target=run_public_repo_harvester,
        args=(db_session_factory,),
        daemon=True
    )
    public_thread.start()
    
    logger.info("Auto-scanner and Threat Harvester background threads spawned successfully.")
