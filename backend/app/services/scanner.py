import re
import math
from typing import Dict, Any, List, Tuple

# Pre-defined high fidelity patterns
PATTERNS = {
    "AWS Access Key": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|ASCA|ASIA)[A-Z0-9]{16}",
    "AWS Secret Key": r"(?i)aws_(?:secret|key|access)?_?(?:key)?['\"]\s*:\s*['\"]([A-Za-z0-9/+=]{40})['\"]",
    "AWS Session Token": r"(?i)aws_(?:session)?_?(?:token)?['\"]\s*:\s*['\"]([A-Za-z0-9/+=]{100,500})['\"]",
    "OpenAI API Key": r"sk-[a-zA-Z0-9]{48}|sk-proj-[a-zA-Z0-9]{80,120}",
    "Stripe API Key": r"sk_(?:test|live)_[0-9a-zA-Z]{24,99}",
    "Google API Key / Google AI Key": r"AIza[0-9A-Za-z-_]{35}",
    "Firebase Config": r"apiKey['\"]\s*:\s*['\"](AIza[0-9A-Za-z-_]{35})['\"]",
    "Slack Webhook": r"https://hooks\.slack\.com/services/T[A-Z0-9]{8}/B[A-Z0-9]{8,10}/[A-Za-z0-9]{24}",
    "Slack Token": r"xox[bapr]-[0-9]{10,13}-[a-zA-Z0-9]{24,32}",
    "Discord Bot Token": r"[MN][A-Za-z0-9]{23}\.[A-Za-z0-9-_]{6}\.[A-Za-z0-9-_]{27}",
    "Telegram Bot Token": r"[0-9]{8,10}:[A-Za-z0-9_-]{35}",
    "GitHub PAT": r"gh[oprs]_[A-Za-z0-9]{36,251}",
    "SSH Private Key": r"-----BEGIN\s+RSA\s+PRIVATE\s+KEY-----|-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----",
    "Generic Credentials URL": r"[a-zA-Z0-9]{3,20}://[a-zA-Z0-9_.-]{3,30}:[a-zA-Z0-9_.-]{3,30}@[a-zA-Z0-9_.-]{3,50}:[0-9]{2,5}",
    "JWT HS256 Secret": r"jwt_secret|jwt-secret|token_secret\s*=\s*['\"]([a-zA-Z0-9!@#$%^&*()_+]{32,})['\"]",
    "Anthropic API Key": r"sk-ant-sid01-[a-zA-Z0-9-_]{93,120}|sk-ant-api03-[a-zA-Z0-9-_]{86,120}",
    "HuggingFace Token": r"hf_[a-zA-Z0-9]{34,36}",
    "Groq API Key": r"gsk_[a-zA-Z0-9]{48,60}",
    "Grok (xAI) API Key": r"xai-[a-zA-Z0-9]{48,96}",
    "Cursor Token": r"(?i)(?:cursor_token\s*=\s*['\"]([a-zA-Z0-9._-]{32,100})['\"]|cur_[a-zA-Z0-9]{32,64})",
    "Together AI API Key": r"(?i)(?:together_api_key|together_key\s*=\s*['\"]([a-zA-Z0-9]{64})['\"]|together_[a-zA-Z0-9]{64})",
    "Replicate API Key": r"r8_[a-zA-Z0-9]{34,40}",
    "DeepSeek API Key": r"(?i)(?:deepseek_api_key|DEEPSEEK_API_KEY|deepseek_key)\s*[=:]\s*['\"]([a-zA-Z0-9_-]{32,64})['\"]|sk-[a-f0-9]{48,64}",
    "OpenRouter API Key": r"sk-or-v1-[a-zA-Z0-9]{64}",
    "Cohere API Key": r"(?i)(?:cohere_api_key|cohere_key\s*=\s*['\"]([a-zA-Z0-9]{40,64})['\"]|co-[a-zA-Z0-9]{40,64})",
    "Stability AI API Key": r"(?i)(?:sk-stability-[a-zA-Z0-9]{48}|stability_api_key|stability_key\s*=\s*['\"]([a-zA-Z0-9]{48,64})['\"])",
    "Perplexity API Key": r"pplx-[a-zA-Z0-9]{48}",
    "LangSmith API Key": r"lsv2_pt_[a-zA-Z0-9]{40,80}",
    "Voyage AI API Key": r"(?i)(?:voyage_api_key|voyage_key\s*=\s*['\"]([a-zA-Z0-9]{40,64})['\"]|vy-[a-zA-Z0-9]{40,64})",
    "AI21 Labs API Key": r"(?i)(?:ai21_api_key|ai21_key\s*=\s*['\"]([a-zA-Z0-9]{32,64})['\"])",
    "Twilio Auth Token": r"AC[a-f0-9]{32}.*?[a-f0-9]{32}",
    "Twilio API Secret": r"SK[a-f0-9]{32}",
    "GitLab PAT": r"glpat-[a-zA-Z0-9\-=_]{20,40}",
    "NPM Auth Token": r"npm_[a-zA-Z0-9]{36}",
    "PyPI API Token": r"pypi-AgEIcHlwaS5vcmc[A-Za-z0-9-_]{50,150}",
    "Cloudflare Token": r"cl_token_[a-zA-Z0-9-_]{32,45}",
    "Azure Connection String": r"DefaultEndpointsProtocol=https;AccountName=[a-zA-Z0-9]{3,30};AccountKey=[A-Za-z0-9/+=]{40,120}",
    "Heroku API Key": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    "Generic Bearer Token": r"(?i)bearer\s+['\"]([a-zA-Z0-9\-._~+/]+=*)['\"]",
    "SendGrid API Key": r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}",
    "Mailchimp API Key": r"[0-9a-f]{32}-us[0-9]{1,2}",
    "Facebook OAuth Token": r"EAACEdEose0cBA[a-zA-Z0-9]+",
    "Square Access Token": r"EAAA[a-zA-Z0-9\-_{}]{60}",
    "Square Sandbox Token": r"EAAAE[a-zA-Z0-9\-_{}]{60}",
    "Datadog API Key": r"\b[a-f0-9]{32}\b",
    "PagerDuty API Token": r"pd-[a-zA-Z0-9]{20}",
    "Shopify Access Token": r"shpat_[a-fA-F0-9]{32}",
    "DigitalOcean PAT": r"dop_v1_[a-f0-9]{64}",
    "Asana PAT": r"0/[0-9a-f]{16}/[0-9a-zA-Z]{1,100}",
    "Atlassian API Token": r"ATATT3xFfGF0[a-zA-Z0-9\-_=]{40,200}",
    "Auth0 Client Secret": r"(?i)auth0_client_secret['\"]\s*:\s*['\"]([a-zA-Z0-9\-_=]{64})['\"]",
    "Sentry DSN": r"https://[a-f0-9]{32}@[a-z0-9\.-]+\.ingest\.sentry\.io/[0-9]+",
    "Linear API Key": r"lin_api_[a-zA-Z0-9]{40}",
    "Supabase Key": r"(?i)supabase_(?:anon|service_role)_key\s*=\s*['\"](eyJ[a-zA-Z0-9._-]+)['\"]",
    "CircleCI PAT": r"(?i)circleci_token\s*=\s*['\"]([a-f0-9]{40})['\"]",
    "Postman API Key": r"PMAK-[a-f0-9]{24}-[a-f0-9]{24}",
    "Shodan API Key": r"\b[a-zA-Z0-9]{32}\b",
    "New Relic Key": r"NRRA-[a-f0-9]{42}",
    "Plaid Secret": r"(?i)plaid_(?:client_secret|secret)\s*=\s*['\"]([a-zA-Z0-9_-]{30,50})['\"]",
    "Mapbox Token": r"[ps]k\.eyJ1[a-zA-Z0-9._-]{50,150}",
    "Mailgun API Key": r"key-[a-f0-9]{32}",
    "HubSpot API Key": r"(?i)hubspot_api_key|pat-[a-zA-Z0-9-]{32,128}",
    "Algolia API Key": r"(?i)algolia_api_key|algolia_secret\s*=\s*['\"]([a-f0-9]{32})['\"]",
    "Grafana Token": r"glsa_[a-zA-Z0-9]{32}_[a-f0-9]{8}",
    # ===== AI / ML Platforms (Extended) =====
    "Mistral AI API Key": r"(?i)(?:mistral_api_key|MISTRAL_API_KEY|mistral_key)\s*[=:]\s*['\"]([a-zA-Z0-9]{32,64})['\"]|(?:mis_|cmpl-)[a-zA-Z0-9]{32,64}",
    "Fireworks AI API Key": r"(?i)(?:fw_[a-zA-Z0-9]{20,48}|(?:fireworks_api_key|FIREWORKS_API_KEY)\s*[=:]\s*['\"]([a-zA-Z0-9]{20,64})['\"])",
    "Cerebras API Key": r"csk-[a-zA-Z0-9]{20,64}",
    "ElevenLabs API Key": r"(?i)(?:xi.api.key|elevenlabs_api_key|ELEVENLABS_API_KEY|eleven_api_key|xi_api_key)\s*[=:]\s*['\"]([a-f0-9]{32})['\"]|el_[a-zA-Z0-9]{32,48}",
    "AssemblyAI API Key": r"(?i)(?:assemblyai_api_key|ASSEMBLYAI_API_KEY|assembly_api_key|ASSEMBLY_KEY)\s*[=:]\s*['\"]([a-f0-9]{32})['\"]|aai_[a-zA-Z0-9]{32,48}",
    "Deepgram API Key": r"(?i)(?:deepgram_api_key|DEEPGRAM_API_KEY|deepgram_key|DEEPGRAM_KEY)\s*[=:]\s*['\"]([a-f0-9]{40,64})['\"]|dg_[a-zA-Z0-9]{32,48}",
    "Pinecone API Key": r"(?i)(?:pinecone_api_key|PINECONE_API_KEY|pinecone_key)\s*[=:]\s*['\"]([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})['\"]|pcsk_[a-zA-Z0-9]{40,60}",
    "Weights & Biases API Key": r"(?i)(?:wandb_api_key|WANDB_API_KEY|wandb_key|WANDB_KEY)\s*[=:]\s*['\"]([a-f0-9]{40})['\"]|wandb_[a-f0-9]{40}",
    "RunPod API Key": r"(?i)(?:runpod_api_key|RUNPOD_API_KEY|runpod_key)\s*[=:]\s*['\"]([a-zA-Z0-9]{25,48})['\"]|rpd_[a-zA-Z0-9]{32,48}",
    "Clarifai PAT": r"(?i)(?:clarifai_pat|CLARIFAI_PAT|clarifai_api_key|CLARIFAI_KEY)\s*[=:]\s*['\"]([a-f0-9]{32,40})['\"]|cl_pat_[a-f0-9]{32,40}",
    "Roboflow API Key": r"rf_[a-zA-Z0-9]{20,40}",
    "Scale AI API Key": r"(?i)(?:scale_api_key|SCALE_API_KEY)\s*[=:]\s*['\"](?:live|test)_[a-zA-Z0-9]{24,48}['\"]|live_[a-zA-Z0-9]{40,60}",
    "Baseten API Key": r"(?i)(?:baseten_api_key|BASETEN_API_KEY)\s*[=:]\s*['\"]([a-zA-Z0-9]{32,64})['\"]|bst_[a-zA-Z0-9]{32,48}",
    "Databricks PAT": r"dapi[a-f0-9]{32}",
    "Lepton AI API Key": r"(?i)(?:lepton_api_key|LEPTON_API_KEY|lepton_key)\s*[=:]\s*['\"]([a-zA-Z0-9]{32,64})['\"]|lpt_[a-zA-Z0-9]{32,48}",
    "Anyscale API Key": r"(?i)(?:anyscale_api_key|ANYSCALE_API_KEY)\s*[=:]\s*['\"]([a-zA-Z0-9_-]{32,64})['\"]|esecret_[a-zA-Z0-9]{32,48}",
    "SambaNova API Key": r"(?i)(?:sambanova_api_key|SAMBANOVA_API_KEY|sambanova_key)\s*[=:]\s*['\"]([a-zA-Z0-9_-]{32,80})['\"]|snova_[a-zA-Z0-9]{32,48}",
    "Writer AI API Key": r"(?i)(?:writer_api_key|WRITER_API_KEY)\s*[=:]\s*['\"]([a-zA-Z0-9_-]{32,64})['\"]|wai_[a-zA-Z0-9]{32,48}",
    "Cohere V2 API Key": r"co_[a-zA-Z0-9]{40,64}",
    "Google Gemini API Key": r"(?i)(?:gemini_api_key|GEMINI_API_KEY|google_ai_key|GOOGLE_AI_KEY)\s*[=:]\s*['\"]([a-zA-Z0-9_-]{39})['\"]|aist_[a-zA-Z0-9]{32,60}",
    "Claude API Key (New)": r"sk-ant-[a-zA-Z0-9-_]{80,200}",
    # ===== Database & Vector DB =====
    "MongoDB Connection String": r"mongodb(?:\+srv)?://[a-zA-Z0-9_.%-]+:[a-zA-Z0-9_.%-]+@[a-zA-Z0-9_.-]+",
    "Redis Connection URL": r"redis(?:s)?://(?:[a-zA-Z0-9_.%-]+:)?[a-zA-Z0-9_.%-]+@[a-zA-Z0-9_.-]+:[0-9]+",
    "MySQL Connection String": r"mysql(?:\+pymysql)?://[a-zA-Z0-9_.%-]+:[a-zA-Z0-9_.%-]+@[a-zA-Z0-9_.-]+:[0-9]+",
    "Weaviate API Key": r"(?i)(?:weaviate_api_key|WEAVIATE_API_KEY|weaviate_key)\s*[=:]\s*['\"]([a-zA-Z0-9]{32,64})['\"]|wvt_[a-zA-Z0-9]{32,48}",
    "Qdrant API Key": r"(?i)(?:qdrant_api_key|QDRANT_API_KEY|qdrant_key)\s*[=:]\s*['\"]([a-zA-Z0-9_-]{32,64})['\"]|qdr_[a-zA-Z0-9]{32,48}",
    # ===== Payment / Finance =====
    "Braintree Access Token": r"access_token\$(?:sandbox|production)\$[a-z0-9]{16}\$[a-f0-9]{32}",
    "Razorpay API Key": r"rzp_(?:test|live)_[a-zA-Z0-9]{14,20}",
    "PayPal Client Secret": r"(?i)(?:paypal_secret|paypal_client_secret|PAYPAL_SECRET)\s*[=:]\s*['\"]([a-zA-Z0-9_-]{40,80})['\"]|ELRA[a-zA-Z0-9_-]{40,80}",
    "Coinbase API Secret": r"(?i)(?:coinbase_api_secret|coinbase_secret|COINBASE_SECRET)\s*[=:]\s*['\"]([a-zA-Z0-9+/=]{40,88})['\"]|cb_[a-zA-Z0-9_-]{40,64}",
    # ===== DevOps / Cloud =====
    "Vercel Token": r"(?i)(?:vercel_token|VERCEL_TOKEN)\s*[=:]\s*['\"]([a-zA-Z0-9]{24,})['\"]|verc_[a-zA-Z0-9]{32,48}",
    "Netlify Token": r"(?i)(?:netlify_auth_token|NETLIFY_TOKEN|netlify_token)\s*[=:]\s*['\"]([a-zA-Z0-9-]{36,60})['\"]|nf_[a-zA-Z0-9]{32,48}",
    "Render API Key": r"rnd_[a-zA-Z0-9]{32,60}",
    "Fly.io Token": r"FlyV1\s+fm[12]_[a-zA-Z0-9_-]{40,}",
    "Railway Token": r"(?i)(?:railway_token|RAILWAY_TOKEN)\s*[=:]\s*['\"]([a-f0-9-]{36})['\"]|railway_[a-f0-9]{36}",
    "Notion Integration Token": r"(?:secret_[a-zA-Z0-9]{43}|ntn_[a-zA-Z0-9]{44,})",
    "Airtable PAT": r"pat[a-zA-Z0-9]{14}\.[a-f0-9]{64}",
    "Terraform Cloud Token": r"(?i)(?:terraform_token|TFE_TOKEN|tfc_token)\s*[=:]\s*['\"]([a-zA-Z0-9.]{14,170})['\"]|atlasv1\.[a-zA-Z0-9-_]{64,}",
    "Doppler Token": r"dp\.(?:ct|pt|sa|stg|prd)\.[a-zA-Z0-9]{32,48}",
    "Vault Token": r"hvs\.[a-zA-Z0-9_-]{24,}",
    "Pulumi Access Token": r"pul-[a-f0-9]{40}",
    "LaunchDarkly SDK Key": r"sdk-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
    "Cloudflare API Token": r"(?i)(?:cloudflare_api_token|CF_API_TOKEN)\s*[=:]\s*['\"]([a-zA-Z0-9_-]{40})['\"]|cf_[a-zA-Z0-9_-]{37}",
    "AWS Cognito ID": r"(?i)(?:cognito_identity_pool_id|identity_pool_id)\s*[=:]\s*['\"]([a-z]{2}-[a-z]+-[0-9]:[a-f0-9-]{36})['\"]|[a-z]{2}-[a-z]+-[0-9]:[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
    # ===== Communication Platforms =====
    "Intercom Access Token": r"(?i)(?:intercom_access_token|INTERCOM_TOKEN|intercom_token)\s*[=:]\s*['\"]([a-zA-Z0-9=]{44,120})['\"]|icm_[a-zA-Z0-9]{32,48}",
    "Zendesk API Token": r"(?i)(?:zendesk_api_token|ZENDESK_TOKEN|zendesk_key)\s*[=:]\s*['\"]([a-zA-Z0-9]{40})['\"]|zd_[a-zA-Z0-9]{32,48}",
    "Twitch Client Secret": r"(?i)(?:twitch_client_secret|TWITCH_SECRET)\s*[=:]\s*['\"]([a-z0-9]{30})['\"]|tw_[a-z0-9]{30}",
    "Twitter Bearer Token": r"AAAAAAAAA[a-zA-Z0-9%-]+",
    "Instagram Token": r"IGQV[a-zA-Z0-9_-]{100,}",
    # ===== Catch-All Generic =====
    "Generic High Entropy Key": r"['\"]([a-zA-Z0-9_-]{32,64})['\"]"
}

# Compile patterns for high performance
COMPILED_PATTERNS = {k: re.compile(v) for k, v in PATTERNS.items()}

# Helper to calculate Shannon Entropy
def calculate_entropy(data: str) -> float:
    if not data:
        return 0.0
    
    entropy = 0.0
    length = len(data)
    frequencies = {}
    
    for char in data:
        frequencies[char] = frequencies.get(char, 0) + 1
        
    for count in frequencies.values():
        p = count / length
        entropy -= p * math.log2(p)
        
    return entropy

def mask_secret(secret: str) -> str:
    return secret

def analyze_context(line: str, secret: str) -> Tuple[str, float]:
    """
    Given a line and the secret within it, return a confidence modifier or classification.
    Helps distinguish actual keys from placeholders (e.g. 'YOUR_KEY_HERE', 'dummy', 'xxxx')
    """
    lowercase_line = line.lower()
    lowercase_secret = secret.lower()
    
    # Check if the secret matches known test or example placeholders
    placeholders = [
        "your_key", "your_token", "example", "dummy", "placeholder", 
        "test_key", "secret_here", "xxxx", "12345", "abcdef", "your-api-key",
        "replace_me", "changeme", "fixme", "todo", "insert_", "put_your",
        "your_api", "enter_your", "add_your", "fill_in", "sample", "mock",
        "fake_key", "fakekey", "testtoken", "demokey", "demo_key",
        "sk-xxx", "sk-your", "sk-test", "sk-fake", "xxx_xxx",
        "000000", "111111", "aaaaaa", "eeeeee", "ffffff",
        "no_key", "none", "null", "undefined", "not_set", "unset",
        "key_goes_here", "token_goes_here", "api_key_here",
        "my_secret", "my_key", "my_token", "some_key", "some_token",
        "xxxxxxxx", "yyyyyyyy", "zzzzzzzz", "testtest", "foobar",
        "lorem", "ipsum", "temp_key", "temporary", "default_key",
        "change_this", "update_this", "replace_this"
    ]
    
    for placeholder in placeholders:
        if placeholder in lowercase_secret or placeholder in lowercase_line:
            return "Low (Potential Placeholder/Test Key)", 0.2
            
    # Calculate entropy
    entropy = calculate_entropy(secret)
    
    # High entropy strings are more likely to be real keys
    if entropy > 4.5:
        return "High (High Entropy Key)", 0.95
    elif entropy > 3.5:
        return "Medium (Medium Entropy Secret)", 0.70
    else:
        return "Low (Low Entropy String)", 0.40

def scan_content(content: str, file_path: str = "unknown") -> List[Dict[str, Any]]:
    findings = []
    lines = content.splitlines()
    
    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1
        
        # Check against compile patterns
        for key_type, regex in COMPILED_PATTERNS.items():
            matches = regex.findall(line)
            for match in matches:
                # regex findall might return tuples if there are capturing groups
                secret_str = match[0] if isinstance(match, tuple) else match
                
                # Make sure the match has substantial content and isn't empty
                if not secret_str or len(secret_str.strip()) < 5:
                    continue
                
                # Filter out generic high-entropy strings or keys that look like code variables
                if key_type in {"Datadog API Key", "Shodan API Key", "Generic High Entropy Key"}:
                    lowercase_line = line.lower()
                    context_keywords = {"key", "token", "secret", "auth", "api", "password", "pass", "credential", "private", "passwd", "jwt", "connect", "credentials", "apikey", "access_key", "client_secret", "session_token"}
                    
                    # 1. Require at least one security context keyword on the same line
                    if not any(kw in lowercase_line for kw in context_keywords):
                        continue
                        
                    # 2. Filter out standard camelCase/snake_case programming variables/method names (only letters/underscores, no digits)
                    if re.match(r"^[a-zA-Z_]{12,64}$", secret_str) and not any(c.isdigit() for c in secret_str):
                        continue
                        
                    # 3. Filter out git commit SHAs, package lock references, or action actions (uses:, @ hashes)
                    if "uses:" in lowercase_line or "@" in lowercase_line:
                        continue
                
                classification, confidence = analyze_context(line, secret_str)
                
                # Severity categorization
                severity = "INFO"
                # CRITICAL: Financial, infrastructure, and high-privilege access
                if any(kw in key_type for kw in ["AWS", "Stripe", "SSH", "GitHub PAT", "MongoDB", "MySQL", "Redis Connection", "Braintree", "PayPal", "Coinbase", "Razorpay", "Azure", "Vault Token", "Terraform"]):
                    severity = "CRITICAL"
                # HIGH: All AI platform keys, communication bots, databases
                elif any(kw in key_type for kw in ["OpenAI", "Anthropic", "Claude", "Google", "Gemini", "Mistral", "Groq", "Grok", "DeepSeek", "Together", "Cohere", "Stability", "AI21", "Perplexity", "Fireworks", "Cerebras", "OpenRouter", "ElevenLabs", "AssemblyAI", "Deepgram", "Pinecone", "Weights", "RunPod", "Clarifai", "Roboflow", "Baseten", "HuggingFace", "Replicate", "LangSmith", "Voyage", "Lepton", "Anyscale", "SambaNova", "Writer AI", "Databricks", "Scale AI", "Cursor", "Discord", "Telegram", "Slack", "Twitch", "Twitter", "Instagram", "GitLab", "Weaviate", "Qdrant", "SendGrid", "Notion", "Airtable"]):
                    severity = "HIGH"
                # MEDIUM: DevOps, monitoring, and generic
                elif any(kw in key_type for kw in ["Firebase", "Generic", "Cloudflare", "Vercel", "Netlify", "Render", "Fly.io", "Railway", "DigitalOcean", "Heroku", "Doppler", "Pulumi", "LaunchDarkly", "Datadog", "PagerDuty", "Shopify", "NPM", "PyPI", "Mapbox", "Mailgun", "HubSpot", "Algolia", "Grafana", "Linear", "Supabase", "CircleCI", "Postman", "New Relic", "Sentry", "Intercom", "Zendesk", "Mailchimp", "Cognito"]):
                    severity = "MEDIUM"
                else:
                    severity = "LOW"
                    
                # Extract snippet (line before, line of leak, line after)
                start_snippet = max(0, line_idx - 1)
                end_snippet = min(len(lines), line_idx + 2)
                snippet_lines = []
                for i in range(start_snippet, end_snippet):
                    prefix = "--> " if i == line_idx else "    "
                    snippet_lines.append(f"{prefix}{i+1}: {lines[i]}")
                snippet = "\n".join(snippet_lines)
                
                findings.append({
                    "secret_type": key_type,
                    "secret_value": mask_secret(secret_str),
                    "raw_secret": secret_str, # used for notifications/AI, will not be saved directly to DB
                    "severity": severity,
                    "confidence": confidence,
                    "file_path": file_path,
                    "line_number": line_num,
                    "snippet": snippet,
                    "classification": classification
                })
                
    return findings
