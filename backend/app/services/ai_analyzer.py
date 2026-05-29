import json
import logging
import requests
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

def evaluate_finding_context(finding: Dict[str, Any], file_content_context: str = "") -> str:
    """
    Evaluates secret leakage context using the Gemini 1.5 Flash API if configured,
    or falls back to a rules-based cybersecurity engine.
    """
    secret_type = finding.get("secret_type", "API Key")
    severity = finding.get("severity", "HIGH")
    snippet = finding.get("snippet", "")
    
    if not settings.AI_API_KEY:
        # Rules-based explanation engine
        threat_info = {
            "AWS Access Key": "This AWS Access Key allows programmatic API calls. If leaked, bad actors can deploy compute resources or access sensitive data assets.",
            "AWS Secret Key": "Pairs with AWS Access Key. Grants full account access or role privileges depending on IAM configurations.",
            "OpenAI API Key": "Grants complete access to OpenAI account credits and custom models, exposing usage quotas to theft.",
            "Stripe API Key": "Allows card charging, customer modification, and chargeback queries. High threat to processing assets.",
            "Google API Key": "Allows usage of Google Maps, Youtube, or Cloud APIs. Vulnerable to quota exhaustion and financial spikes.",
            "SSH Private Key": "Enables remote SSH shell execution. High risk of server takeover and lateral network movement.",
            "GitHub PAT": "Grants access to code repositories, pipelines, and releases. Risk of source code theft and supply chain compromise."
        }.get(secret_type, "A credential was exposed in code. Exposes account access and API usage depending on privileges.")
        
        return f"[Cyber Engine Ruleset] THREAT ASSESSMENT: {threat_info} CONFIDENCE: {finding.get('confidence', 0.5)*100}%"
        
    # Calling Gemini API directly using requests (Zero SDK dependency)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.AI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
As an enterprise cyber-security threat analyst, review this exposed secret finding:
Secret Type: {secret_type}
Severity: {severity}
Code Snippet:
{snippet}

Assess if this is a real active leak or a placeholder/example (e.g. YOUR_KEY, dummy_value).
Provide a 2-sentence summary explaining:
1. The immediate threat level and what actions an attacker can perform if they exploit this leak.
Do not output HTML or markdown tags. Just pure text. Do NOT include any remediation instructions, steps, or recommendations on how to rotate, revoke, or delete the key.
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            analysis_text = res_data['candidates'][0]['content']['parts'][0]['text']
            return f"[AI Security Analyst] {analysis_text.strip()}"
        else:
            logger.error(f"Gemini API returned error: {response.text}")
            return f"[Local Engine] System found an exposed {secret_type}. Exposes account access and API usage depending on privileges."
    except Exception as e:
        logger.error(f"Gemini API calling failed: {str(e)}")
        return f"[Local Engine] System found an exposed {secret_type}. Exposes account access and API usage depending on privileges."
