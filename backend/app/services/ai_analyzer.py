import json
import logging
import requests
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Comprehensive threat intelligence for all 100+ secret types
THREAT_INTEL = {
    # === AWS ===
    "AWS Access Key": "This AWS Access Key allows programmatic API calls. If leaked, bad actors can deploy compute resources, exfiltrate data from S3 buckets, or pivot across AWS services.",
    "AWS Secret Key": "Pairs with AWS Access Key. Grants full account access or role privileges depending on IAM configurations. Immediate credential rotation required.",
    "AWS Session Token": "Temporary session token granting time-limited AWS access. Can be replayed until expiry to perform any action the session role permits.",
    "AWS Cognito ID": "Identity pool ID enabling unauthenticated or authenticated access to AWS resources. Attackers can assume temporary credentials for S3, DynamoDB, and Lambda.",
    # === AI / ML Platforms ===
    "OpenAI API Key": "Grants complete access to OpenAI account credits, GPT models, and fine-tuned assets. Attackers can exhaust billing quotas rapidly.",
    "Anthropic API Key": "Provides full access to Anthropic Claude models. Exposed keys allow unauthorized API consumption and potential billing exploitation.",
    "Claude API Key (New)": "New-format Anthropic Claude API key. Grants the same Claude model access as legacy keys with potential for significant billing abuse.",
    "Google API Key / Google AI Key": "Allows usage of Google Cloud APIs (Maps, YouTube, Gemini, etc.). Vulnerable to quota exhaustion and financial spikes on billing accounts.",
    "Google Gemini API Key": "Direct access to Google Gemini AI models. Attackers can consume API quota, run inference at scale, and drive up billing costs.",
    "Mistral AI API Key": "Grants access to Mistral AI inference endpoints. Attackers can consume credits for model inference and fine-tuning operations.",
    "Groq API Key": "Provides access to Groq's high-speed LPU inference. Exposed keys enable unauthorized model queries and quota exhaustion.",
    "Grok (xAI) API Key": "Access to xAI's Grok models. Attackers can perform unrestricted inference calls and deplete account credits.",
    "DeepSeek API Key": "Grants access to DeepSeek's AI models. Can be exploited for unauthorized inference, code generation, and quota abuse.",
    "Together AI API Key": "Provides access to Together AI's open-source model hosting. Attackers can run large-scale inference and incur compute charges.",
    "Cohere API Key": "Access to Cohere's NLP models (embeddings, generation, classification). Enables unauthorized text processing at scale.",
    "Cohere V2 API Key": "V2-format Cohere API key with the same risk profile as legacy keys. Grants full platform API access.",
    "Stability AI API Key": "Grants access to Stability AI image generation models (Stable Diffusion). Attackers can generate content and exhaust API credits.",
    "AI21 Labs API Key": "Access to AI21's Jurassic language models. Exposed keys allow unauthorized text generation and token consumption.",
    "Perplexity API Key": "Provides access to Perplexity's AI search and reasoning models. Attackers can perform queries and consume subscription quota.",
    "Fireworks AI API Key": "Access to Fireworks AI inference platform. Enables unauthorized model serving, fine-tuning job creation, and billing exploitation.",
    "Cerebras API Key": "Grants access to Cerebras Cloud inference. Attackers can run high-performance model inference and consume compute credits.",
    "OpenRouter API Key": "Multi-model routing key. Provides access to 100+ LLMs through OpenRouter's unified API, amplifying potential for abuse.",
    "ElevenLabs API Key": "Access to ElevenLabs voice synthesis and cloning. Attackers can generate deepfake audio and exhaust character quotas.",
    "AssemblyAI API Key": "Grants access to AssemblyAI transcription services. Exposed keys allow unauthorized audio processing and data access.",
    "Deepgram API Key": "Access to Deepgram speech-to-text API. Attackers can transcribe audio and consume API credits at scale.",
    "Pinecone API Key": "Provides access to Pinecone vector database. Attackers can read, modify, or delete vector indexes containing sensitive embeddings.",
    "Weights & Biases API Key": "Access to W&B experiment tracking. Attackers can view ML experiments, model artifacts, datasets, and training configurations.",
    "RunPod API Key": "Grants access to RunPod GPU cloud. Attackers can deploy GPU instances, run workloads, and incur significant compute charges.",
    "Clarifai PAT": "Access to Clarifai's computer vision and NLP platform. Enables unauthorized model inference, training, and data access.",
    "Roboflow API Key": "Provides access to Roboflow computer vision datasets and models. Attackers can access training data and deployed model endpoints.",
    "Scale AI API Key": "Access to Scale AI data annotation and evaluation platform. Exposed keys enable unauthorized task creation and data access.",
    "Baseten API Key": "Grants access to Baseten model serving infrastructure. Attackers can invoke deployed models and consume compute resources.",
    "Databricks PAT": "Full access to Databricks workspace. Attackers can execute notebooks, access data lakes, manage clusters, and exfiltrate datasets.",
    "Lepton AI API Key": "Access to Lepton AI serverless inference. Enables unauthorized model deployment and API consumption.",
    "Anyscale API Key": "Grants access to Anyscale Ray clusters. Attackers can deploy workloads, access data, and consume cloud compute.",
    "SambaNova API Key": "Access to SambaNova's AI chip inference. Enables unauthorized high-performance model inference and credit exhaustion.",
    "Writer AI API Key": "Provides access to Writer's enterprise AI models. Attackers can generate content and access organizational knowledge bases.",
    "HuggingFace Token": "Access to HuggingFace Hub. Attackers can download private models, upload malicious models, and modify repository assets.",
    "Replicate API Key": "Grants access to Replicate's model hosting. Enables unauthorized model inference, deployment, and GPU compute billing.",
    "LangSmith API Key": "Access to LangChain's LangSmith tracing platform. Exposes LLM traces, prompts, inputs/outputs, and debugging data.",
    "Voyage AI API Key": "Access to Voyage AI embedding models. Attackers can generate embeddings and consume API quota.",
    "Cursor Token": "Access to Cursor AI IDE features. May expose code completion data, workspace configurations, and usage credits.",
    # === Code & DevOps ===
    "GitHub PAT": "Grants access to code repositories, pipelines, and releases. Risk of source code theft, supply chain attacks, and secret pivoting.",
    "GitLab PAT": "Full access to GitLab projects, CI/CD pipelines, and container registries. Enables code theft and pipeline manipulation.",
    "SSH Private Key": "Enables remote SSH shell execution. High risk of server takeover, lateral movement, and persistent backdoor establishment.",
    "DigitalOcean PAT": "Full access to DigitalOcean infrastructure. Attackers can create/destroy droplets, access databases, and modify DNS.",
    "Vercel Token": "Access to Vercel deployments and projects. Attackers can deploy malicious code, access environment secrets, and modify domains.",
    "Netlify Token": "Grants access to Netlify sites and deployments. Enables malicious site deployment and environment variable extraction.",
    "Render API Key": "Access to Render services and databases. Attackers can deploy services, access logs, and modify environment configurations.",
    "Railway Token": "Full access to Railway projects and services. Enables deployment manipulation, database access, and secret extraction.",
    "Cloudflare Token": "Access to Cloudflare account services. Can modify DNS records, WAF rules, and redirect traffic for phishing attacks.",
    "Cloudflare API Token": "Scoped Cloudflare API access. Risk depends on token permissions — could enable DNS hijacking or cache poisoning.",
    "Terraform Cloud Token": "Access to Terraform Cloud workspaces. Attackers can modify infrastructure-as-code, deploy resources, and access state files containing secrets.",
    "Doppler Token": "Access to Doppler secret management. Exposes all application secrets stored in the project environment.",
    "Vault Token": "HashiCorp Vault access token. Grants access to secrets engine — critical risk of exposing all stored credentials.",
    "Pulumi Access Token": "Access to Pulumi infrastructure management. Enables infrastructure modification and state file access.",
    "LaunchDarkly SDK Key": "Access to LaunchDarkly feature flags. Attackers can toggle features, access user targeting data, and disrupt releases.",
    "Notion Integration Token": "Access to Notion workspace data. Attackers can read, modify, and delete pages, databases, and shared content.",
    "Airtable PAT": "Full access to Airtable bases. Enables data exfiltration, record manipulation, and schema modification.",
    # === Payment ===
    "Stripe API Key": "Allows card charging, customer data access, refund processing, and bank account configurations. Critical financial exposure.",
    "Braintree Access Token": "Full access to Braintree payment processing. Enables unauthorized charges, refunds, and customer data access.",
    "Razorpay API Key": "Access to Razorpay payment gateway. Risk of unauthorized transactions and customer payment data exposure.",
    "PayPal Client Secret": "Grants PayPal API access for payment processing. Enables unauthorized transactions and account manipulation.",
    "Coinbase API Secret": "Access to Coinbase exchange account. Attackers can view balances, initiate transfers, and access transaction history.",
    # === Communication ===
    "Telegram Bot Token": "Full control of Telegram bot. Attackers can send messages, access chat history, and impersonate the bot to users.",
    "Discord Bot Token": "Complete control of Discord bot. Enables message sending, server manipulation, and user data access.",
    "Slack Token": "Access to Slack workspace. Attackers can read/send messages, access files, and enumerate users and channels.",
    "Slack Webhook": "Enables posting messages to a Slack channel. Can be used for phishing, social engineering, or spam campaigns.",
    "Twitch Client Secret": "Access to Twitch API. Enables stream manipulation, chat access, and user data enumeration.",
    "Twitter Bearer Token": "Read-only access to Twitter/X API. Enables data scraping, user enumeration, and timeline access.",
    "Instagram Token": "Access to Instagram Graph API. Enables profile data access, media retrieval, and account information exposure.",
    "Intercom Access Token": "Access to Intercom customer messaging. Exposes customer conversations, user data, and support history.",
    "Zendesk API Token": "Access to Zendesk support platform. Enables ticket access, customer data exposure, and agent impersonation.",
    # === Databases ===
    "Generic Credentials URL": "Database connection URL with embedded credentials. Grants direct database access for data exfiltration and modification.",
    "MongoDB Connection String": "MongoDB connection with embedded credentials. Enables full database access, data theft, and potential ransomware.",
    "Redis Connection URL": "Redis connection with credentials. Enables cache poisoning, session hijacking, and data manipulation.",
    "MySQL Connection String": "MySQL connection with credentials. Grants full database access for data exfiltration and schema manipulation.",
    "Weaviate API Key": "Access to Weaviate vector database. Enables reading, modifying, or deleting vector data and schemas.",
    "Qdrant API Key": "Access to Qdrant vector database. Attackers can manipulate vector collections and access stored embeddings.",
    # === Monitoring & SaaS ===
    "SendGrid API Key": "Access to SendGrid email service. Enables spam campaigns, phishing emails, and sender reputation damage.",
    "Datadog API Key": "Access to Datadog monitoring. Exposes infrastructure metrics, logs, and application performance data.",
    "Sentry DSN": "Sentry error tracking endpoint. Enables error log access and potential injection of fake error reports.",
    "PagerDuty API Token": "Access to PagerDuty incident management. Enables incident creation, escalation manipulation, and on-call disruption.",
    "New Relic Key": "Access to New Relic observability platform. Exposes application metrics, traces, and infrastructure data.",
    "Postman API Key": "Access to Postman collections and workspaces. May expose API documentation, test credentials, and environment secrets.",
    "Linear API Key": "Access to Linear project management. Enables issue access, project data exposure, and workflow manipulation.",
    "Grafana Token": "Access to Grafana dashboards and data sources. Exposes monitoring data and potentially connected database credentials.",
    "Shopify Access Token": "Access to Shopify store admin. Enables order manipulation, customer data access, and store configuration changes.",
    "NPM Auth Token": "Access to NPM registry. Enables publishing malicious packages, modifying existing ones, and supply chain attacks.",
    "PyPI API Token": "Access to Python Package Index. Enables malicious package publishing and existing package version manipulation.",
    "Mapbox Token": "Access to Mapbox APIs. Enables quota exhaustion, location data access, and billing exploitation.",
    "Mailgun API Key": "Access to Mailgun email service. Enables unauthorized email sending, domain access, and bounce/complaint data.",
    "Mailchimp API Key": "Access to Mailchimp marketing platform. Exposes subscriber lists, campaign data, and audience analytics.",
    "HubSpot API Key": "Access to HubSpot CRM. Exposes customer contacts, deal pipelines, and marketing automation data.",
    "Algolia API Key": "Access to Algolia search. Enables index manipulation, search data access, and analytics exposure.",
    "CircleCI PAT": "Access to CircleCI CI/CD. Enables pipeline manipulation, build log access, and environment secret extraction.",
    "Supabase Key": "Access to Supabase backend. Enables database queries, auth manipulation, and storage access.",
    "Plaid Secret": "Access to Plaid financial data. Enables bank account access, transaction history, and identity verification data.",
    # === Cloud Infrastructure ===
    "Azure Connection String": "Azure storage connection with embedded key. Grants full access to blob storage, queues, and table data.",
    "Firebase Config": "Firebase project configuration. May expose database URLs, storage buckets, and authentication settings.",
    "Heroku API Key": "Access to Heroku platform. Enables app deployment, config var access, and add-on manipulation.",
    "Fly.io Token": "Access to Fly.io applications. Enables deployment manipulation, secrets access, and machine management.",
    # === Auth ===
    "JWT HS256 Secret": "JWT signing secret. Attackers can forge authentication tokens and impersonate any user in the system.",
    "Auth0 Client Secret": "Auth0 OAuth client secret. Enables token generation, user impersonation, and authentication bypass.",
    "Facebook OAuth Token": "Facebook OAuth access token. Enables profile access, friend list enumeration, and social graph data.",
    "Atlassian API Token": "Access to Atlassian products (Jira, Confluence). Enables project data access and document modification.",
    "Asana PAT": "Access to Asana workspace. Enables task access, project data exposure, and workflow manipulation.",
    "Square Access Token": "Access to Square payment processing. Enables transaction access and payment manipulation.",
    "Square Sandbox Token": "Square sandbox token. Lower risk but may indicate proximity to production credentials.",
    "Render API Key": "Access to Render deployment platform. Enables service manipulation and environment variable access.",
    # === Generic ===
    "Generic Bearer Token": "Bearer authentication token. Risk depends on the target API — could grant any level of access.",
    "Generic High Entropy Key": "High-entropy string detected in security-sensitive context. May be an API key, password, or cryptographic material.",
    "Generic Credentials URL": "Connection URL with embedded credentials. Grants direct access to the connected service.",
    "Shodan API Key": "Access to Shodan internet scanning. Enables infrastructure reconnaissance and vulnerability identification.",
}

# Free AI API endpoints (no key required) — cascading fallback chain
FREE_AI_ENDPOINTS = [
    {"name": "GPT-5", "url": "https://apis.prexzyvilla.site/ai/gpt-5?text=", "param": "text"},
    {"name": "Copilot-Think", "url": "https://apis.prexzyvilla.site/ai/copilot-think?text=", "param": "text"},
    {"name": "Copilot", "url": "https://apis.prexzyvilla.site/ai/copilot?text=", "param": "text"},
    {"name": "AI4Chat", "url": "https://apis.prexzyvilla.site/ai/ai4chat?prompt=", "param": "prompt"},
    {"name": "AIServ", "url": "https://apis.prexzyvilla.site/ai/aiserv?prompt=", "param": "prompt"},
    {"name": "ChatEX", "url": "https://apis.prexzyvilla.site/ai/chatex?text=", "param": "text"},
]


def _build_security_prompt(secret_type: str, severity: str, snippet: str) -> str:
    """Builds the cybersecurity analysis prompt for all AI engines."""
    return (
        f"As an enterprise cyber-security threat analyst, review this exposed secret finding. "
        f"Secret Type: {secret_type}. Severity: {severity}. "
        f"Code Snippet: {snippet[:300]}. "
        f"Assess if this is a real active leak or a placeholder/example (e.g. YOUR_KEY, dummy_value). "
        f"Provide a 2-sentence summary explaining the immediate threat level and what actions "
        f"an attacker can perform if they exploit this leak. "
        f"Do not output HTML or markdown tags. Just pure text. "
        f"Do NOT include remediation instructions or steps to rotate/revoke the key."
    )


def _try_gemini(prompt: str) -> str | None:
    """Try Google Gemini API (requires AI_API_KEY)."""
    if not settings.AI_API_KEY:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.AI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            text = res_data['candidates'][0]['content']['parts'][0]['text']
            return f"[Gemini AI Analyst] {text.strip()}"
    except Exception as e:
        logger.warning(f"Gemini API failed: {str(e)}")
    return None


def _try_free_ai(prompt: str) -> str | None:
    """Try all free AI endpoints in cascading order. Returns first successful response."""
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt, safe='')

    for endpoint in FREE_AI_ENDPOINTS:
        try:
            url = f"{endpoint['url']}{encoded_prompt}"
            response = requests.get(url, timeout=12)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") and data.get("text"):
                    text = data["text"].strip()
                    if len(text) > 20:  # Ensure meaningful response
                        model_name = data.get("model", endpoint["name"])
                        logger.info(f"Free AI response from {endpoint['name']} ({model_name})")
                        return f"[AI Analyst ({model_name})] {text}"

        except Exception as e:
            logger.warning(f"Free AI endpoint {endpoint['name']} failed: {str(e)}")
            continue

    return None


def evaluate_finding_context(finding: Dict[str, Any], file_content_context: str = "") -> str:
    """
    Multi-tier AI threat analysis engine with cascading fallback:
    
    Tier 1: Google Gemini 2.0 Flash (requires AI_API_KEY)
    Tier 2: Free AI APIs (GPT-5, Copilot-Think, Copilot, AI4Chat, AIServ, ChatEX)
    Tier 3: Local rules-based cyber engine (112 threat intel entries)
    """
    secret_type = finding.get("secret_type", "API Key")
    severity = finding.get("severity", "HIGH")
    snippet = finding.get("snippet", "")
    confidence = finding.get("confidence", 0.5)

    # Build the analysis prompt
    prompt = _build_security_prompt(secret_type, severity, snippet)

    # === Tier 1: Gemini (if configured) ===
    result = _try_gemini(prompt)
    if result:
        return result

    # === Tier 2: Free AI APIs (cascading) ===
    result = _try_free_ai(prompt)
    if result:
        return result

    # === Tier 3: Local Rules Engine (always available) ===
    threat_info = THREAT_INTEL.get(
        secret_type,
        f"A credential of type '{secret_type}' was exposed in code. Exposes account access and API usage depending on privileges."
    )
    return f"[Cyber Engine Ruleset] THREAT ASSESSMENT: {threat_info} CONFIDENCE: {confidence*100:.1f}%"
