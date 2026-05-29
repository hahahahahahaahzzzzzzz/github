import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

# =============================================================================
#                        REQUEST HELPERS
# =============================================================================

def _safe_get(url: str, headers: dict, timeout: int = 8) -> requests.Response:
    """Safe GET with timeout and exception catching."""
    return requests.get(url, headers=headers, timeout=timeout)

def _safe_post(url: str, headers: dict, json_data: dict = None, timeout: int = 8) -> requests.Response:
    """Safe POST with timeout and exception catching."""
    return requests.post(url, headers=headers, json=json_data, timeout=timeout)


# =============================================================================
#           AI / ML PLATFORM VALIDATORS (30+ platforms)
# =============================================================================

def check_openai_key(api_key: str) -> bool:
    """Validates OpenAI key by querying OpenAI's models list endpoint."""
    url = "https://api.openai.com/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_anthropic_key(api_key: str) -> bool:
    """Validates Anthropic API key using the models listing endpoint."""
    url = "https://api.anthropic.com/v1/models"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    try:
        res = _safe_get(url, headers)
        # 200 = valid, 401 = invalid, 403 = valid but restricted
        return res.status_code in (200, 403)
    except Exception:
        return False

def check_google_gemini_key(api_key: str) -> bool:
    """Validates Google AI / Gemini API key by listing available models."""
    url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
    try:
        res = requests.get(url, timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def check_mistral_key(api_key: str) -> bool:
    """Validates Mistral AI API key by querying their models endpoint."""
    url = "https://api.mistral.ai/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_groq_key(api_key: str) -> bool:
    """Validates Groq key via lightweight models query."""
    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_grok_xai_key(api_key: str) -> bool:
    """Validates xAI / Grok API key via their models endpoint."""
    url = "https://api.x.ai/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_deepseek_key(api_key: str) -> bool:
    """Validates DeepSeek API key via their OpenAI-compatible models endpoint."""
    url = "https://api.deepseek.com/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_together_key(api_key: str) -> bool:
    """Validates Together AI API key via their models endpoint."""
    url = "https://api.together.xyz/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_cohere_key(api_key: str) -> bool:
    """Validates Cohere tokens by calling their check-api-key route."""
    url = "https://api.cohere.com/v1/check-api-key"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_post(url, headers)
        if res.status_code == 200:
            return res.json().get("valid", False)
        return False
    except Exception:
        return False

def check_stability_key(api_key: str) -> bool:
    """Validates Stability AI key via account endpoint."""
    url = "https://api.stability.ai/v1/user/account"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_ai21_key(api_key: str) -> bool:
    """Validates AI21 Labs key via tokenize endpoint."""
    url = "https://api.ai21.com/studio/v1/tokenize"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        res = _safe_post(url, headers, json_data={"text": "test"})
        return res.status_code in (200, 400, 422)
    except Exception:
        return False

def check_perplexity_key(api_key: str) -> bool:
    """Validates Perplexity key via chat completions (1-token test)."""
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "sonar",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1
    }
    try:
        res = _safe_post(url, headers, json_data=payload)
        # 200 or 400/422 (if payload format varies) means key is verified
        return res.status_code in (200, 400, 422)
    except Exception:
        return False

def check_fireworks_key(api_key: str) -> bool:
    """Validates Fireworks AI API key via models endpoint."""
    url = "https://api.fireworks.ai/inference/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_cerebras_key(api_key: str) -> bool:
    """Validates Cerebras API key via models endpoint."""
    url = "https://api.cerebras.ai/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_openrouter_key(api_key: str) -> bool:
    """Validates OpenRouter API key via auth/key endpoint."""
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_elevenlabs_key(api_key: str) -> bool:
    """Validates ElevenLabs API key via user info endpoint."""
    url = "https://api.elevenlabs.io/v1/user"
    headers = {"xi-api-key": api_key}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_assemblyai_key(api_key: str) -> bool:
    """Validates AssemblyAI API key via transcript listing endpoint."""
    url = "https://api.assemblyai.com/v2/transcript?limit=1"
    headers = {"authorization": api_key}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_deepgram_key(api_key: str) -> bool:
    """Validates Deepgram API key via projects listing endpoint."""
    url = "https://api.deepgram.com/v1/projects"
    headers = {"Authorization": f"Token {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_pinecone_key(api_key: str) -> bool:
    """Validates Pinecone API key via indexes listing endpoint."""
    url = "https://api.pinecone.io/indexes"
    headers = {"Api-Key": api_key}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_wandb_key(api_key: str) -> bool:
    """Validates Weights & Biases API key via GraphQL viewer query."""
    url = "https://api.wandb.ai/graphql"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"query": "{ viewer { id username } }"}
    try:
        res = _safe_post(url, headers, json_data=payload)
        if res.status_code == 200:
            data = res.json()
            return data.get("data", {}).get("viewer") is not None
        return False
    except Exception:
        return False

def check_runpod_key(api_key: str) -> bool:
    """Validates RunPod API key via GraphQL query."""
    url = "https://api.runpod.io/graphql"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"query": "{ myself { id } }"}
    try:
        res = _safe_post(url, headers, json_data=payload)
        return res.status_code == 200
    except Exception:
        return False

def check_clarifai_key(api_key: str) -> bool:
    """Validates Clarifai PAT via user info endpoint."""
    url = "https://api.clarifai.com/v2/users/me"
    headers = {"Authorization": f"Key {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_roboflow_key(api_key: str) -> bool:
    """Validates Roboflow API key via workspace query."""
    url = f"https://api.roboflow.com/?api_key={api_key}"
    try:
        res = requests.get(url, timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def check_baseten_key(api_key: str) -> bool:
    """Validates Baseten API key via models listing."""
    url = "https://api.baseten.co/v1/models"
    headers = {"Authorization": f"Api-Key {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_huggingface_token(token: str) -> bool:
    """Validates HuggingFace credentials by querying their whoami endpoint."""
    url = "https://huggingface.co/api/whoami-v2"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_replicate_token(token: str) -> bool:
    """Validates Replicate key via account endpoint."""
    url = "https://api.replicate.com/v1/account"
    headers = {"Authorization": f"Token {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_langsmith_key(api_key: str) -> bool:
    """Validates LangSmith API key via sessions list."""
    url = "https://api.smith.langchain.com/api/v1/sessions?limit=1"
    headers = {"x-api-key": api_key}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_voyage_key(api_key: str) -> bool:
    """Validates Voyage AI API key via embeddings (smallest test)."""
    url = "https://api.voyageai.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"input": "test", "model": "voyage-3-lite"}
    try:
        res = _safe_post(url, headers, json_data=payload)
        return res.status_code in (200, 400, 422)
    except Exception:
        return False


# =============================================================================
#          CLOUD / DEVOPS PLATFORM VALIDATORS
# =============================================================================

def check_aws_key(access_key: str, secret_key: str = "") -> bool:
    """Validates AWS access key using lightweight STS get-caller-identity check."""
    try:
        import botocore.session
        from botocore.exceptions import ClientError
        session = botocore.session.get_session()
        session.set_credentials(access_key, secret_key)
        client = session.create_client('sts', region_name='us-east-1')
        client.get_caller_identity()
        return True
    except Exception as e:
        err_str = str(e)
        if "AccessDenied" in err_str:
            return True  # Key exists but lacks STS permission
        return False

def check_github_pat(token: str) -> bool:
    """Validates GitHub PAT by querying GitHub's user profile endpoint."""
    url = "https://api.github.com/user"
    headers = {"Authorization": f"token {token}", "User-Agent": "RepoLeak-Watcher-X"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_gitlab_pat(token: str) -> bool:
    """Validates GitLab PAT via user info endpoint."""
    url = "https://gitlab.com/api/v4/user"
    headers = {"PRIVATE-TOKEN": token}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_digitalocean_pat(token: str) -> bool:
    """Validates DigitalOcean PAT via account endpoint."""
    url = "https://api.digitalocean.com/v2/account"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_vercel_token(token: str) -> bool:
    """Validates Vercel token via user info endpoint."""
    url = "https://api.vercel.com/v2/user"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_netlify_token(token: str) -> bool:
    """Validates Netlify token via user info endpoint."""
    url = "https://api.netlify.com/api/v1/user"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_render_key(api_key: str) -> bool:
    """Validates Render API key via owners listing."""
    url = "https://api.render.com/v1/owners?limit=1"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_railway_token(token: str) -> bool:
    """Validates Railway token via GraphQL viewer."""
    url = "https://backboard.railway.app/graphql/v2"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"query": "{ me { id } }"}
    try:
        res = _safe_post(url, headers, json_data=payload)
        return res.status_code == 200
    except Exception:
        return False

def check_cloudflare_token(token: str) -> bool:
    """Validates Cloudflare API token via token verification endpoint."""
    url = "https://api.cloudflare.com/client/v4/user/tokens/verify"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_get(url, headers)
        if res.status_code == 200:
            return res.json().get("success", False)
        return False
    except Exception:
        return False

def check_terraform_cloud_token(token: str) -> bool:
    """Validates Terraform Cloud token via account details."""
    url = "https://app.terraform.io/api/v2/account/details"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False


# =============================================================================
#          PAYMENT PLATFORM VALIDATORS
# =============================================================================

def check_stripe_key(api_key: str) -> bool:
    """Validates Stripe token by querying Stripe's balance endpoint."""
    url = "https://api.stripe.com/v1/balance"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_razorpay_key(api_key: str) -> bool:
    """Validates Razorpay key by querying payments endpoint."""
    url = "https://api.razorpay.com/v1/payments?count=1"
    try:
        # Razorpay uses key_id:key_secret as basic auth but key_id alone can be checked
        res = requests.get(url, auth=(api_key, ""), timeout=8)
        # 401 with specific message means key_id is valid but secret is missing
        # 200 means both are valid (unlikely without secret)
        return res.status_code in (200, 401)
    except Exception:
        return False


# =============================================================================
#          COMMUNICATION PLATFORM VALIDATORS
# =============================================================================

def check_telegram_token(token: str) -> bool:
    """Validates Telegram Bot token using standard getMe API."""
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        res = requests.get(url, timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def check_discord_token(token: str) -> bool:
    """Validates Discord Bot token via users/@me endpoint."""
    url = "https://discord.com/api/v10/users/@me"
    headers = {"Authorization": f"Bot {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_slack_token(token: str) -> bool:
    """Validates Slack token via auth.test API."""
    url = "https://slack.com/api/auth.test"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_post(url, headers)
        if res.status_code == 200:
            return res.json().get("ok", False)
        return False
    except Exception:
        return False

def check_twitch_secret(secret: str) -> bool:
    """Validates Twitch client secret by attempting OAuth token generation."""
    # This requires client_id which we don't have, so we check format and length
    # A real validator would need both client_id and client_secret
    return len(secret) >= 30 and secret.isalnum()


# =============================================================================
#          MONITORING / ANALYTICS VALIDATORS
# =============================================================================

def check_sendgrid_key(api_key: str) -> bool:
    """Validates SendGrid API key via user profile endpoint."""
    url = "https://api.sendgrid.com/v3/user/profile"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_datadog_key(api_key: str) -> bool:
    """Validates Datadog API key via validation endpoint."""
    url = "https://api.datadoghq.com/api/v1/validate"
    headers = {"DD-API-KEY": api_key}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_sentry_token(token: str) -> bool:
    """Validates Sentry auth token via organizations listing."""
    url = "https://sentry.io/api/0/organizations/"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_pagerduty_key(api_key: str) -> bool:
    """Validates PagerDuty API token via abilities endpoint."""
    url = "https://api.pagerduty.com/abilities"
    headers = {"Authorization": f"Token token={api_key}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_newrelic_key(api_key: str) -> bool:
    """Validates New Relic API key via NerdGraph user query."""
    url = "https://api.newrelic.com/graphql"
    headers = {"API-Key": api_key, "Content-Type": "application/json"}
    payload = {"query": "{ actor { user { id } } }"}
    try:
        res = _safe_post(url, headers, json_data=payload)
        return res.status_code == 200
    except Exception:
        return False

def check_postman_key(api_key: str) -> bool:
    """Validates Postman API key via user info endpoint."""
    url = "https://api.getpostman.com/me"
    headers = {"X-Api-Key": api_key}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_linear_key(api_key: str) -> bool:
    """Validates Linear API key via GraphQL viewer query."""
    url = "https://api.linear.app/graphql"
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    payload = {"query": "{ viewer { id } }"}
    try:
        res = _safe_post(url, headers, json_data=payload)
        return res.status_code == 200
    except Exception:
        return False

def check_grafana_token(token: str) -> bool:
    """Validates Grafana Cloud token via orgs endpoint."""
    url = "https://grafana.com/api/orgs"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_shopify_token(token: str) -> bool:
    """
    Validates Shopify access token. Needs store domain context.
    Returns True by format-check if no domain is available.
    """
    # Shopify tokens require a store domain for validation
    # Format validation: shpat_ + 32 hex chars
    return token.startswith("shpat_") and len(token) >= 38

def check_npm_token(token: str) -> bool:
    """Validates NPM auth token via user profile endpoint."""
    url = "https://registry.npmjs.org/-/npm/v1/user"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_mapbox_token(token: str) -> bool:
    """Validates Mapbox token via tokens listing endpoint."""
    url = f"https://api.mapbox.com/tokens/v2?access_token={token}"
    try:
        res = requests.get(url, timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def check_mailgun_key(api_key: str) -> bool:
    """Validates Mailgun API key via domains listing."""
    url = "https://api.mailgun.net/v3/domains"
    try:
        res = requests.get(url, auth=("api", api_key), timeout=8)
        return res.status_code == 200
    except Exception:
        return False

def check_algolia_key(api_key: str) -> bool:
    """
    Validates Algolia API key. Requires application ID for full validation.
    Returns True as a format check since standalone validation isn't possible.
    """
    return len(api_key) == 32 and all(c in '0123456789abcdef' for c in api_key.lower())

def check_circleci_token(token: str) -> bool:
    """Validates CircleCI token via user info endpoint."""
    url = "https://circleci.com/api/v2/me"
    headers = {"Circle-Token": token}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_notion_token(token: str) -> bool:
    """Validates Notion integration token via users listing."""
    url = "https://api.notion.com/v1/users?page_size=1"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28"
    }
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_airtable_pat(token: str) -> bool:
    """Validates Airtable PAT via user info endpoint."""
    url = "https://api.airtable.com/v0/meta/whoami"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False

def check_doppler_token(token: str) -> bool:
    """Validates Doppler token via workplace info."""
    url = "https://api.doppler.com/v3/workplace"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = _safe_get(url, headers)
        return res.status_code == 200
    except Exception:
        return False


# =============================================================================
#           MASTER DISPATCHER
# =============================================================================

# Map of all secret types to their validator functions
VALIDATOR_MAP = {
    # AI / ML Platforms
    "OpenAI API Key": lambda v: check_openai_key(v),
    "Anthropic API Key": lambda v: check_anthropic_key(v),
    "Claude API Key (New)": lambda v: check_anthropic_key(v),
    "Google API Key / Google AI Key": lambda v: check_google_gemini_key(v),
    "Google Gemini API Key": lambda v: check_google_gemini_key(v),
    "Mistral AI API Key": lambda v: check_mistral_key(v),
    "Groq API Key": lambda v: check_groq_key(v),
    "Grok (xAI) API Key": lambda v: check_grok_xai_key(v),
    "DeepSeek API Key": lambda v: check_deepseek_key(v),
    "Together AI API Key": lambda v: check_together_key(v),
    "Cohere API Key": lambda v: check_cohere_key(v),
    "Cohere V2 API Key": lambda v: check_cohere_key(v),
    "Stability AI API Key": lambda v: check_stability_key(v),
    "AI21 Labs API Key": lambda v: check_ai21_key(v),
    "Perplexity API Key": lambda v: check_perplexity_key(v),
    "Fireworks AI API Key": lambda v: check_fireworks_key(v),
    "Cerebras API Key": lambda v: check_cerebras_key(v),
    "OpenRouter API Key": lambda v: check_openrouter_key(v),
    "ElevenLabs API Key": lambda v: check_elevenlabs_key(v),
    "AssemblyAI API Key": lambda v: check_assemblyai_key(v),
    "Deepgram API Key": lambda v: check_deepgram_key(v),
    "Pinecone API Key": lambda v: check_pinecone_key(v),
    "Weights & Biases API Key": lambda v: check_wandb_key(v),
    "RunPod API Key": lambda v: check_runpod_key(v),
    "Clarifai PAT": lambda v: check_clarifai_key(v),
    "Roboflow API Key": lambda v: check_roboflow_key(v),
    "Baseten API Key": lambda v: check_baseten_key(v),
    "HuggingFace Token": lambda v: check_huggingface_token(v),
    "Replicate API Key": lambda v: check_replicate_token(v),
    "LangSmith API Key": lambda v: check_langsmith_key(v),
    "Voyage AI API Key": lambda v: check_voyage_key(v),
    # Cloud / DevOps Platforms
    "GitHub PAT": lambda v: check_github_pat(v),
    "GitLab PAT": lambda v: check_gitlab_pat(v),
    "DigitalOcean PAT": lambda v: check_digitalocean_pat(v),
    "Vercel Token": lambda v: check_vercel_token(v),
    "Netlify Token": lambda v: check_netlify_token(v),
    "Render API Key": lambda v: check_render_key(v),
    "Railway Token": lambda v: check_railway_token(v),
    "Cloudflare API Token": lambda v: check_cloudflare_token(v),
    "Terraform Cloud Token": lambda v: check_terraform_cloud_token(v),
    "Doppler Token": lambda v: check_doppler_token(v),
    # Payment Platforms
    "Stripe API Key": lambda v: check_stripe_key(v),
    "Razorpay API Key": lambda v: check_razorpay_key(v),
    # Communication Platforms
    "Telegram Bot Token": lambda v: check_telegram_token(v),
    "Discord Bot Token": lambda v: check_discord_token(v),
    "Slack Token": lambda v: check_slack_token(v),
    # Monitoring / Analytics / SaaS
    "SendGrid API Key": lambda v: check_sendgrid_key(v),
    "Datadog API Key": lambda v: check_datadog_key(v),
    "Sentry DSN": lambda v: check_sentry_token(v),
    "PagerDuty API Token": lambda v: check_pagerduty_key(v),
    "New Relic Key": lambda v: check_newrelic_key(v),
    "Postman API Key": lambda v: check_postman_key(v),
    "Linear API Key": lambda v: check_linear_key(v),
    "Grafana Token": lambda v: check_grafana_token(v),
    "Shopify Access Token": lambda v: check_shopify_token(v),
    "NPM Auth Token": lambda v: check_npm_token(v),
    "Mapbox Token": lambda v: check_mapbox_token(v),
    "Mailgun API Key": lambda v: check_mailgun_key(v),
    "CircleCI PAT": lambda v: check_circleci_token(v),
    "Notion Integration Token": lambda v: check_notion_token(v),
    "Airtable PAT": lambda v: check_airtable_pat(v),
}


def verify_secret_validity(secret_type: str, raw_value: str) -> bool:
    """
    Master dispatcher that routes key verification requests based on the
    detected signature type.

    Returns True if the key is valid (active) OR if the key type is not verifiable.
    Returns False if the key is verified as invalid (inactive/revoked).
    """
    validator = VALIDATOR_MAP.get(secret_type)

    if not validator:
        # Key type has no validator - assume potentially valid (err on side of caution)
        return True

    try:
        logger.info(f"Validating {secret_type} key...")
        is_valid = validator(raw_value)
        status = "ACTIVE" if is_valid else "INACTIVE/REVOKED"
        logger.info(f"Validation result for {secret_type}: {status}")
        return is_valid
    except Exception as e:
        logger.error(f"Error checking secret validity for {secret_type}: {str(e)}")
        return False
