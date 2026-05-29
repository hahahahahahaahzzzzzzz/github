import requests
import base64
import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self):
        self.tokens = settings.github_token_list
        self.current_token_idx = 0
        
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RepoLeak-Watcher-X"
        }
        if self.tokens:
            token = self.tokens[self.current_token_idx]
            headers["Authorization"] = f"token {token}"
            # Simple rotation
            self.current_token_idx = (self.current_token_idx + 1) % len(self.tokens)
        return headers

    def get_repo_metadata(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetches repository details from GitHub API.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": data.get("name"),
                    "owner": data.get("owner", {}).get("login"),
                    "stars": data.get("stargazers_count", 0),
                    "url": data.get("html_url")
                }
            else:
                logger.error(f"GitHub API Error: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            logger.error(f"GitHub connection failed: {str(e)}")
            return {}

    def fetch_repo_files_recursive(self, owner: str, repo: str, branch: str = "main") -> List[Dict[str, str]]:
        """
        Finds target configuration files recursively in the repository.
        Returns a list of dicts with file path and file download URL.
        """
        # Targets that frequently contain secrets
        target_extensions = (
            ".env", "config.json", "settings.py", "yaml", "yml", 
            "docker-compose", "tf", "npmrc", "pypirc", "pem", "key"
        )
        
        # Get default branch sha
        url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
        headers = self._get_headers()
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            # Try master if main fails
            if res.status_code == 404 and branch == "main":
                url = f"https://api.github.com/repos/{owner}/{repo}/branches/master"
                res = requests.get(url, headers=headers, timeout=10)
                
            if res.status_code != 200:
                logger.error(f"Failed to fetch branch tree for {owner}/{repo}: {res.status_code}")
                return []
                
            sha = res.json().get("commit", {}).get("commit", {}).get("tree", {}).get("sha")
            if not sha:
                return []
                
            # Fetch recursive tree
            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{sha}?recursive=1"
            tree_res = requests.get(tree_url, headers=headers, timeout=15)
            if tree_res.status_code != 200:
                return []
                
            files = []
            for item in tree_res.json().get("tree", []):
                path = item.get("path", "")
                if item.get("type") == "blob" and (path.endswith(target_extensions) or any(t in path.lower() for t in ["secret", "config", "env", "credentials"])):
                    files.append({
                        "path": path,
                        "url": item.get("url") # API URL to fetch file blob
                    })
            return files
            
        except Exception as e:
            logger.error(f"Error recursively fetching repo files: {str(e)}")
            return []

    def get_latest_commit_sha(self, owner: str, repo: str, branch: str = "main") -> str:
        """
        Fetches the latest commit SHA for checkpoint comparison.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
        headers = self._get_headers()
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 404 and branch == "main":
                url = f"https://api.github.com/repos/{owner}/{repo}/branches/master"
                res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json().get("commit", {}).get("sha", "")
        except Exception as e:
            logger.error(f"Error fetching latest commit SHA: {str(e)}")
        return ""

    def fetch_recent_commits(self, owner: str, repo: str, branch: str = "main", count: int = 10) -> List[Dict[str, Any]]:
        """
        Fetches recent commit SHAs and metadata for history scanning.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?sha={branch}&per_page={count}"
        headers = self._get_headers()
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 404 and branch == "main":
                url = f"https://api.github.com/repos/{owner}/{repo}/commits?sha=master&per_page={count}"
                res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            logger.error(f"Error fetching recent commits: {str(e)}")
        return []

    def fetch_commit_details(self, owner: str, repo: str, sha: str) -> Dict[str, Any]:
        """
        Fetches full details of a commit including files mutated and patch diffs.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
        headers = self._get_headers()
        try:
            res = requests.get(url, headers=headers, timeout=12)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            logger.error(f"Error fetching commit details for {sha}: {str(e)}")
        return {}

    def fetch_file_content(self, blob_api_url: str) -> str:
        """
        Fetches blob contents from GitHub and decodes Base64 content.
        """
        try:
            res = requests.get(blob_api_url, headers=self._get_headers(), timeout=10)
            if res.status_code == 200:
                data = res.json()
                encoding = data.get("encoding", "")
                content_base64 = data.get("content", "")
                
                if encoding == "base64":
                    # GitHub embeds newlines, replace them
                    clean_b64 = content_base64.replace("\n", "").replace("\r", "")
                    return base64.b64decode(clean_b64).decode("utf-8", errors="ignore")
                return content_base64
            return ""
        except Exception as e:
            logger.error(f"Error fetching file content: {str(e)}")
            return ""

    def get_user_repositories(self) -> List[Dict[str, Any]]:
        """
        Fetches all repositories accessible by the configured GITHUB_TOKENS.
        """
        tokens = settings.github_token_list
        if not tokens:
            logger.warning("No GitHub tokens configured. Cannot discover user repositories.")
            return []
            
        repos = []
        seen_urls = set()
        
        for token in tokens:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "RepoLeak-Watcher-X",
                "Authorization": f"token {token}"
            }
            page = 1
            while True:
                url = f"https://api.github.com/user/repos?per_page=100&page={page}"
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    if response.status_code != 200:
                        logger.error(f"GitHub user repos API Error: {response.status_code} - {response.text}")
                        break
                    
                    data = response.json()
                    if not data or not isinstance(data, list):
                        break
                        
                    for repo in data:
                        repo_url = repo.get("html_url")
                        if repo_url and repo_url not in seen_urls:
                            seen_urls.add(repo_url)
                            repos.append({
                                "name": repo.get("name"),
                                "owner": repo.get("owner", {}).get("login"),
                                "stars": repo.get("stargazers_count", 0),
                                "url": repo_url
                            })
                    if len(data) < 100:
                        break
                    page += 1
                except Exception as e:
                    logger.error(f"Error fetching user repositories: {str(e)}")
                    break
        return repos

# Singleton Instance
github_client = GitHubClient()
