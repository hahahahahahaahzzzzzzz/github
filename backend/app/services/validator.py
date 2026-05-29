import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

def check_aws_key(access_key: str, secret_key: str) -> bool:
    """
    Validates AWS access key programmatically using lightweight STS get-caller-identity check.
    """
    import botocore.session
    from botocore.exceptions import ClientError
    session = botocore.session.get_session()
    # Configure dummy or custom client credentials
    session.set_credentials(access_key, secret_key)
    client = session.create_client('sts', region_name='us-east-1')
    try:
        client.get_caller_identity()
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidClientTokenId':
            return False
        # If access is denied but token is valid, credentials exist
        if e.response['Error']['Code'] == 'AccessDenied':
            return True
        return False
    except Exception:
        return False

def check_stripe_key(api_key: str) -> bool:
    """
    Validates Stripe token by querying Stripe's standard balance or accounts retrieve details.
    """
    url = "https://api.stripe.com/v1/balance"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def check_openai_key(api_key: str) -> bool:
    """
    Validates OpenAI key by querying OpenAI's models list endpoint.
    """
    url = "https://api.openai.com/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def check_github_pat(token: str) -> bool:
    """
    Validates GitHub PAT by querying GitHub's user profile endpoint.
    """
    url = "https://api.github.com/user"
    headers = {"Authorization": f"token {token}", "User-Agent": "RepoLeak-Watcher-X"}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def check_huggingface_token(token: str) -> bool:
    """
    Validates HuggingFace credentials by querying their whoami endpoint.
    """
    url = "https://huggingface.co/api/whoami-v2"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def check_cohere_key(api_key: str) -> bool:
    """
    Validates Cohere tokens by calling their validation route.
    """
    url = "https://api.cohere.com/v1/check-api-key"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = requests.post(url, headers=headers, timeout=8)
        if res.status_code == 200:
            return res.json().get("valid", False)
        return False
    except Exception:
        return False

def check_perplexity_key(api_key: str) -> bool:
    """
    Validates Perplexity key via test query.
    """
    # Uses standard model validation list or lightweight completion request
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "sonar-reasoning",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=8)
        # 200 or 400 (if payload invalid but auth matches) means key is verified
        return res.status_code in (200, 400, 422)
    except Exception:
        return False

def check_groq_key(api_key: str) -> bool:
    """
    Validates Groq key via lightweight models query.
    """
    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def check_telegram_token(token: str) -> bool:
    """
    Validates Telegram Bot token using standard getMe API.
    """
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        res = requests.get(url, timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def check_replicate_token(token: str) -> bool:
    """
    Validates Replicate key.
    """
    url = "https://api.replicate.com/v1/account"
    headers = {"Authorization": f"Token {token}"}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def verify_secret_validity(secret_type: str, raw_value: str) -> bool:
    """
    Dispatches key verification requests based on the detected signature type.
    """
    try:
        if secret_type == "Stripe API Key":
            return check_stripe_key(raw_value)
        elif secret_type == "OpenAI API Key":
            return check_openai_key(raw_value)
        elif secret_type == "GitHub PAT":
            return check_github_pat(raw_value)
        elif secret_type == "HuggingFace Token":
            return check_huggingface_token(raw_value)
        elif secret_type == "Groq API Key":
            return check_groq_key(raw_value)
        elif secret_type == "Cohere API Key":
            return check_cohere_key(raw_value)
        elif secret_type == "Perplexity API Key":
            return check_perplexity_key(raw_value)
        elif secret_type == "Telegram Bot Token":
            return check_telegram_token(raw_value)
        elif secret_type == "Replicate API Key":
            return check_replicate_token(raw_value)
    except Exception as e:
        logger.error(f"Error checking secret validity: {str(e)}")
    return False
