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
        remediation = {
            "AWS Access Key": "This AWS Access Key allows programmatic API calls. If leaked, bad actors can deploy cryptominers or steal DB backups.",
            "AWS Secret Key": "Pairs with AWS Access Key. Grants full admin or user role access depending on IAM permissions.",
            "OpenAI API Key": "Grants complete access to OpenAI account credits and custom models. Exposure leads to billing spikes.",
            "Stripe API Key": "Allows payment charging, customer modifications, and chargeback queries. High financial threat.",
            "Google API Key": "Allows usage of Google Maps, Youtube, or Cloud APIs. Vulnerable to quota exhaustion.",
            "SSH Private Key": "Enables remote SSH shell execution. Critical risk of server takeover and lateral network movement.",
            "GitHub PAT": "Grants access to code repositories, pipelines, and releases. Risk of source code theft and supply chain attacks."
        }.get(secret_type, "A credential was exposed in code. Revoke immediately to prevent account takeover and API abuse.")
        
        return f"[Cyber Engine Ruleset] REMEDIATION: {remediation} CONFIDENCE: {finding.get('confidence', 0.5)*100}%"
        
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
1. The immediate threat level and what actions an attacker can perform.
2. Clear action items to resolve.
Do not output HTML or markdown tags. Just pure text.
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
            return f"[Local Engine] System found an exposed {secret_type}. Revoke key immediately and check access logs."
    except Exception as e:
        logger.error(f"Gemini API calling failed: {str(e)}")
        return f"[Local Engine] System found an exposed {secret_type}. Revoke key immediately and check access logs."
