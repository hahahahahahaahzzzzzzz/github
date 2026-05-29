import re
import math
from typing import Dict, Any, List, Tuple

# Pre-defined high fidelity patterns
PATTERNS = {
    "AWS Access Key": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|ASCA|ASIA)[A-Z0-9]{16}",
    "AWS Secret Key": r"(?i)aws_(?:secret|key|access)?_?(?:key)?['\"]\s*:\s*['\"]([A-Za-z0-9/+=]{40})['\"]",
    "OpenAI API Key": r"sk-[a-zA-Z0-9]{48}|sk-proj-[a-zA-Z0-9]{80,120}",
    "Stripe API Key": r"sk_(?:test|live)_[0-9a-zA-Z]{24,99}",
    "Google API Key": r"AIza[0-9A-Za-z-_]{35}",
    "Firebase Config": r"apiKey['\"]\s*:\s*['\"](AIza[0-9A-Za-z-_]{35})['\"]",
    "Slack Webhook": r"https://hooks\.slack\.com/services/T[A-Z0-9]{8}/B[A-Z0-9]{8,10}/[A-Za-z0-9]{24}",
    "Discord Bot Token": r"[MN][A-Za-z0-9]{23}\.[A-Za-z0-9-_]{6}\.[A-Za-z0-9-_]{27}",
    "Telegram Bot Token": r"[0-9]{8,10}:[A-Za-z0-9_-]{35}",
    "GitHub PAT": r"gh[oprs]_[A-Za-z0-9]{36,251}",
    "SSH Private Key": r"-----BEGIN\s+RSA\s+PRIVATE\s+KEY-----|-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----",
    "Generic Credentials URL": r"[a-zA-Z0-9]{3,20}://[a-zA-Z0-9_.-]{3,30}:[a-zA-Z0-9_.-]{3,30}@[a-zA-Z0-9_.-]{3,50}:[0-9]{2,5}",
    "JWT HS256 Secret": r"jwt_secret|jwt-secret|token_secret\s*=\s*['\"]([a-zA-Z0-9!@#$%^&*()_+]{32,})['\"]"
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
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"

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
