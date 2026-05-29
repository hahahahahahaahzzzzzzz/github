import time
import logging
import threading
from app.config import settings
from app.models.repository import Repository
from app.services.github_client import github_client
from app.api.endpoints.scans import execute_repository_scan

logger = logging.getLogger(__name__)

def run_auto_scanner(db_session_factory):
    """
    Background daemon thread that runs continuously.
    1. Fetches all repositories for the configured GitHub tokens.
    2. Registers any new repositories in the database.
    3. Triggers a scan for all monitored repositories.
    4. Sleeps for a configured interval before repeating.
    """
    logger.info("Automatic GitHub Repositories Discovery and Scan daemon started.")
    
    # Small initial delay to let the app start up completely
    time.sleep(5)
    
    while True:
        db = db_session_factory()
        try:
            logger.info("Auto-scanner: Querying GitHub for user repositories...")
            repos_discovered = github_client.get_user_repositories()
            logger.info(f"Auto-scanner: Discovered {len(repos_discovered)} repositories from GitHub.")
            
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
                    logger.info(f"Auto-scanner: Registered new repository: {repo.owner}/{repo.name}")
                    new_repos_count += 1
            
            if new_repos_count > 0:
                logger.info(f"Auto-scanner: Registered {new_repos_count} new repositories in the database.")
            
            # Fetch all monitored repositories
            monitored_repos = db.query(Repository).filter(Repository.is_monitored == 1).all()
            logger.info(f"Auto-scanner: Starting scans for {len(monitored_repos)} monitored repositories.")
            
            for repo in monitored_repos:
                try:
                    logger.info(f"Auto-scanner: Initiating scan check for {repo.owner}/{repo.name}...")
                    execute_repository_scan(repo.id, db_session_factory)
                except Exception as scan_err:
                    logger.error(f"Auto-scanner: Failed to scan {repo.owner}/{repo.name}: {str(scan_err)}")
                    
        except Exception as e:
            logger.error(f"Auto-scanner Daemon Error: {str(e)}")
        finally:
            db.close()
            
        logger.info(f"Auto-scanner: Sweep completed. Sleeping for {settings.AUTO_SCAN_INTERVAL_SECONDS} seconds.")
        time.sleep(settings.AUTO_SCAN_INTERVAL_SECONDS)

def start_auto_scan_daemon(db_session_factory) -> None:
    """
    Spawns the background auto-scanner daemon thread.
    """
    daemon_thread = threading.Thread(
        target=run_auto_scanner,
        args=(db_session_factory,),
        daemon=True
    )
    daemon_thread.start()
    logger.info("Auto-scanner background thread spawned successfully.")
