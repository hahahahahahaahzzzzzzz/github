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
    "DeepSeek API Key": r"(?i)(?:deepseek_api_key|deepseek_key\s*=\s*['\"]([a-zA-Z0-9]{32,64})['\"]|sk-[a-f0-9]{32})",
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
        "test_key", "secret_here", "xxxx", "12345", "abcdef", "your-api-key"
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
                if "AWS" in key_type or "Stripe" in key_type or "SSH" in key_type or "GitHub" in key_type:
                    severity = "CRITICAL"
                elif "OpenAI" in key_type or "Google" in key_type or "Discord" in key_type or "Telegram" in key_type:
                    severity = "HIGH"
                elif "Firebase" in key_type or "Generic" in key_type:
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
