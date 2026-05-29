import logging
import threading
import time
import requests
from typing import Dict, Any, Optional
from app.config import settings
from app.models.repository import Repository
from app.models.finding import Finding
from app.models.scan_history import ScanHistory

logger = logging.getLogger(__name__)

# Basic duplicate cache in memory
_sent_alerts = set()

def send_telegram_alert(finding_data: Dict[str, Any], repository_data: Dict[str, Any]) -> bool:
    """
    Sends a beautifully formatted HTML alert to the configured Telegram channel/chat.
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    
    if not bot_token or not chat_id:
        logger.warning("Telegram Bot Token or Chat ID not configured. Skipping alert.")
        return False
        
    dup_key = f"{repository_data.get('url')}:{finding_data.get('secret_value')}"
    if dup_key in _sent_alerts:
        logger.info(f"Duplicate alert suppressed for: {dup_key}")
        return True
        
    import html
    
    severity = finding_data.get("severity", "INFO").upper()
    
    # Premium Headers and Badges
    severity_badge = {
        "CRITICAL": "🔴 🔴 <b>CRITICAL SEVERITY INCIDENT</b> 🔴 🔴",
        "HIGH": "🟠 <b>HIGH RISK INCIDENT</b> 🟠",
        "MEDIUM": "🟡 <b>MEDIUM RISK DETECTED</b> 🟡",
        "LOW": "🔵 <b>LOW RISK FINDING</b> 🔵",
        "INFO": "⚪ <b>INFO LOG</b> ⚪"
    }.get(severity, "⚪ <b>SECURITY ALARM</b>")
    
    divider = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Safe HTML escaping for code variables to prevent parsing crashes
    esc_secret_type = html.escape(str(finding_data.get('secret_type', '')))
    esc_secret_val = html.escape(str(finding_data.get('secret_value', '')))
    esc_owner = html.escape(str(repository_data.get('owner', '')))
    esc_repo = html.escape(str(repository_data.get('name', '')))
    esc_path = html.escape(str(finding_data.get('file_path', '')))
    esc_snippet = html.escape(str(finding_data.get('snippet', '')))
    esc_analysis = html.escape(str(finding_data.get('ai_analysis', '')))
    
    html_message = f"""
🛡️ <b>[SOC ALERT] REPOLEAK WATCHER X</b>
{divider}
⚠️ <b>Threat:</b> {severity_badge}
🏷️ <b>Signature:</b> <code>{esc_secret_type}</code>
📂 <b>Asset:</b> <code>{esc_owner}/{esc_repo}</code>

📄 <b>Path:</b> <code>{esc_path}:{finding_data.get('line_number')}</code>
🎯 <b>Certainty:</b> <code>{finding_data.get('confidence', 0.5) * 100:.1f}% Confidence</code>
{divider}

🛠️ <b>LEAK EVIDENCE CONTEXT:</b>
<pre><code>{esc_snippet}</code></pre>

🧠 <b>AI ASSESSMENT:</b>
<i>{esc_analysis}</i>
{divider}

💡 <b>REMEDIATION PLAYBOOK:</b>
1️⃣ Revoke compromised credentials immediately.
2️⃣ Run <code>git-filter-repo</code> to purge history.
3️⃣ Review backend logs for unauthorized actions.

<i>System telemetry by RepoLeak Watcher X</i>
"""

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": html_message,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "🌐 View Git Repo", "url": repository_data.get("url")},
                    {"text": "🛡️ Open SOC HUD", "url": "https://github.com"}
                ]
            ]
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram notification sent successfully.")
            _sent_alerts.add(dup_key)
            return True
        else:
            logger.error(f"Failed to send Telegram alert: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception during Telegram alert dispatch: {str(e)}")
        return False

def handle_status_command(chat_id: int, bot_token: str, db_session_factory) -> None:
    """
    Queries DB and responds with system diagnostics report.
    """
    db = db_session_factory()
    try:
        repos_count = db.query(Repository).filter(Repository.is_monitored == 1).count()
        findings_count = db.query(Finding).count()
        active_count = db.query(Finding).filter(Finding.is_resolved == False).count()
        scans_count = db.query(ScanHistory).count()
        
        divider = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        response_text = f"""
📊 <b>REPOLEAK WATCHER X - TELEMETRY HUD</b>
{divider}
🛰️ <b>System:</b> <code style="color: green">ONLINE</code> [Running]
📦 <b>Monitored Repos:</b> <code>{repos_count} assets</code>
🚨 <b>Total Detections:</b> <code>{findings_count} leaks</code>
🔥 <b>Active Incidents:</b> <code>{active_count} unresolved</code>
🛡️ <b>Completed Scans:</b> <code>{scans_count} sweeps</code>
{divider}
<i>Query processed in real time by bot command interface.</i>
"""
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": response_text,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)
        
    except Exception as e:
        logger.error(f"Error executing telemetry check: {str(e)}")
    finally:
        db.close()

def telegram_polling_worker(bot_token: str, db_session_factory) -> None:
    """
    Background worker thread polling Telegram getUpdates endpoint for bot commands.
    """
    logger.info("Telegram Bot Command polling service started.")
    last_update_id = 0
    
    # Fetch initial updates to avoid processing old backlog
    try:
        init_res = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates", timeout=5)
        if init_res.status_code == 200:
            results = init_res.json().get("result", [])
            if results:
                last_update_id = results[-1]["update_id"]
    except Exception:
        pass

    while True:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates?offset={last_update_id + 1}&timeout=15"
            res = requests.get(url, timeout=20)
            
            if res.status_code == 200:
                updates = res.json().get("result", [])
                for update in updates:
                    last_update_id = update["update_id"]
                    
                    message = update.get("message", {})
                    text = message.get("text", "").strip()
                    chat = message.get("chat", {})
                    chat_id = chat.get("id")
                    
                    if text == "/status" and chat_id:
                        logger.info(f"Received /status command from chat_id {chat_id}")
                        handle_status_command(chat_id, bot_token, db_session_factory)
                        
            elif res.status_code == 401:
                logger.error("Telegram bot token unauthorized. Disabling updates listener.")
                break
                
        except Exception as e:
            logger.error(f"Error in Telegram getUpdates polling loop: {str(e)}")
            
        time.sleep(2)

def start_telegram_polling(db_session_factory) -> None:
    """
    Triggers Telegram updates listener thread if credentials exist.
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        logger.warning("Telegram Bot Token is not configured. Telemetry polling will not run.")
        return
        
    polling_thread = threading.Thread(
        target=telegram_polling_worker,
        args=(bot_token, db_session_factory),
        daemon=True
    )
    polling_thread.start()
    logger.info("Telegram Polling daemon spawned successfully.")
