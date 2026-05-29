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
    
    html_message = f"""🛡️ <b>[SOC ALERT] REPOLEAK WATCHER X</b>
{divider}
⚠️ <b>Threat:</b> {severity_badge}

🏷️ <b>Signature:</b>
<blockquote>{esc_secret_type}</blockquote>

🔑 <b>Exposed Secret:</b>
<blockquote><code>{esc_secret_val}</code></blockquote>

📂 <b>Asset:</b> <code>{esc_owner}/{esc_repo}</code>
📄 <b>Path:</b> <code>{esc_path}:{finding_data.get('line_number')}</code>
🎯 <b>Certainty:</b> <code>{finding_data.get('confidence', 0.5) * 100:.1f}% Confidence</code>
{divider}

🛠️ <b>LEAK EVIDENCE CONTEXT:</b>
<pre><code>{esc_snippet}</code></pre>

🧠 <b>AI ASSESSMENT:</b>
<blockquote>{esc_analysis}</blockquote>
{divider}
<i>System telemetry by RepoLeak Watcher X</i>"""

    from app.services.validator import verify_secret_validity
    
    # Check if this exposed secret is actually valid programmatically
    is_valid = verify_secret_validity(finding_data.get("secret_type", ""), finding_data.get("secret_value", ""))
    
    # Setup status badge
    validity_badge = "✅ <b>ACTIVE (VALIDATED KEY)</b>" if is_valid else "❌ <b>INACTIVE / REVOKED KEY</b>"
    
    html_message = f"""🛡️ <b>[SOC ALERT] REPOLEAK WATCHER X</b>
{divider}
⚠️ <b>Threat:</b> {severity_badge}
🔍 <b>Status:</b> {validity_badge}

🏷️ <b>Signature:</b>
<blockquote>{esc_secret_type}</blockquote>

🔑 <b>Exposed Secret:</b>
<blockquote><code>{esc_secret_val}</code></blockquote>

📂 <b>Asset:</b> <code>{esc_owner}/{esc_repo}</code>
📄 <b>Path:</b> <code>{esc_path}:{finding_data.get('line_number')}</code>
🎯 <b>Certainty:</b> <code>{finding_data.get('confidence', 0.5) * 100:.1f}% Confidence</code>
{divider}

🛠️ <b>LEAK EVIDENCE CONTEXT:</b>
<pre><code>{esc_snippet}</code></pre>

🧠 <b>AI ASSESSMENT:</b>
<blockquote>{esc_analysis}</blockquote>
{divider}
<i>System telemetry by RepoLeak Watcher X</i>"""

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🌐 View Git Repo", "url": repository_data.get("url")},
                {"text": "🛡️ Open SOC HUD", "url": "https://github.com"}
            ]
        ]
    }
    
    def dispatch_msg(target_id: str) -> Optional[int]:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": target_id,
            "text": html_message,
            "parse_mode": "HTML",
            "reply_markup": reply_markup
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                return res.json().get("result", {}).get("message_id")
        except Exception as e:
            logger.error(f"Error sending message to {target_id}: {str(e)}")
        return None

    def pin_msg(target_chat_id: str, msg_id: int):
        url = f"https://api.telegram.org/bot{bot_token}/pinChatMessage"
        try:
            requests.post(url, json={"chat_id": target_chat_id, "message_id": msg_id, "disable_notification": False}, timeout=5)
        except Exception as e:
            logger.error(f"Error pinning message {msg_id} in {target_chat_id}: {str(e)}")

    personal_chat_id = settings.TELEGRAM_PERSONAL_CHAT_ID
    
    try:
        sent_any = False
        
        # Scenario 1: Valid key -> Send to group, send to personal, and PIN in personal
        if is_valid:
            # 1. Send to public group
            if chat_id:
                dispatch_msg(chat_id)
            # 2. Send to personal chat
            if personal_chat_id:
                p_msg_id = dispatch_msg(personal_chat_id)
                # 3. Pin in personal chat
                if p_msg_id:
                    pin_msg(personal_chat_id, p_msg_id)
            sent_any = True
        else:
            # Scenario 2: Inactive/Invalid key -> Send ONLY in personal (no group spam)
            if personal_chat_id:
                dispatch_msg(personal_chat_id)
                sent_any = True
                
        if sent_any:
            _sent_alerts.add(dup_key)
            return True
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
                    update_id = update.get("update_id")
                    if not update_id:
                        continue
                    
                    # Deduplicate update processing using Redis to handle multiple active containers
                    if settings.REDIS_URL:
                        try:
                            import redis
                            r = redis.Redis.from_url(settings.REDIS_URL)
                            redis_key = f"processed_tg_update:{update_id}"
                            is_new = r.set(redis_key, "1", ex=60, nx=True)
                            if not is_new:
                                # Already processed by another process, update last_update_id and skip
                                last_update_id = max(last_update_id, update_id)
                                continue
                        except Exception as redis_err:
                            logger.debug(f"Redis TG deduplication error: {str(redis_err)}")
                            
                    last_update_id = max(last_update_id, update_id)
                    
                    message = update.get("message", {})
                    text = message.get("text", "").strip()
                    chat = message.get("chat", {})
                    chat_id = chat.get("id")
                    
                    if chat_id:
                        if text == "/status":
                            logger.info(f"Received /status command from chat_id {chat_id}")
                            handle_status_command(chat_id, bot_token, db_session_factory)
                        elif text == "/findings":
                            logger.info(f"Received /findings command from chat_id {chat_id}")
                            handle_findings_command(chat_id, bot_token, db_session_factory)
                        elif text.startswith("/scan"):
                            logger.info(f"Received /scan command from chat_id {chat_id}")
                            handle_scan_command(chat_id, text, bot_token, db_session_factory)
                        elif text.startswith("/resolve"):
                            logger.info(f"Received /resolve command from chat_id {chat_id}")
                            handle_resolve_command(chat_id, text, bot_token, db_session_factory)
                        
            elif res.status_code == 401:
                logger.error("Telegram bot token unauthorized. Disabling updates listener.")
                break
                
        except Exception as e:
            logger.error(f"Error in Telegram getUpdates polling loop: {str(e)}")
            
        time.sleep(2)

def handle_findings_command(chat_id: int, bot_token: str, db_session_factory) -> None:
    db = db_session_factory()
    try:
        active_findings = db.query(Finding).filter(Finding.is_resolved == False).order_by(Finding.created_at.desc()).limit(8).all()
        divider = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        if not active_findings:
            text = f"🛡️ <b>[SOC HUB]</b>\n{divider}\nNo active unresolved leaks detected in any asset."
        else:
            list_lines = []
            for f in active_findings:
                list_lines.append(f"🚨 ID: <code>{f.id}</code> | <b>{f.secret_type}</b>\n📄 Path: <code>{f.file_path}:{f.line_number}</code>\n")
            list_str = "\n".join(list_lines)
            text = f"🛡️ <b>[SOC HUB] ACTIVE INCIDENTS (Last 8)</b>\n{divider}\n{list_str}"
            
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        logger.error(f"Error executing findings telemetry: {str(e)}")
    finally:
        db.close()

def handle_scan_command(chat_id: int, command_text: str, bot_token: str, db_session_factory) -> None:
    parts = command_text.split()
    if len(parts) < 2:
        text = "⚠️ Usage: <code>/scan &lt;repo_id_or_github_url&gt;</code>"
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
        return
        
    target = parts[1]
    db = db_session_factory()
    try:
        repo = None
        if target.isdigit():
            repo = db.query(Repository).filter(Repository.id == int(target)).first()
        else:
            repo = db.query(Repository).filter(Repository.url == target).first()
            
        if not repo:
            # Attempt to clean url
            if "github.com/" in target:
                from app.api.endpoints.scans import parse_github_url
                owner, name = parse_github_url(target)
                repo = Repository(name=name, owner=owner, url=target, is_monitored=1)
                db.add(repo)
                db.commit()
                db.refresh(repo)
                
        if not repo:
            text = "❌ Error: Target repository not found in database or invalid GitHub URL."
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
            return
            
        # Spawn scanner
        from app.api.endpoints.scans import execute_repository_scan
        from fastapi import BackgroundTasks
        # Run synchronous within background thread to return response
        import threading
        thread = threading.Thread(target=execute_repository_scan, args=(repo.id, db_session_factory))
        thread.start()
        
        text = f"🚀 Scan queued successfully for <b>{repo.owner}/{repo.name}</b> [ID: {repo.id}]."
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        logger.error(f"Error routing /scan command: {str(e)}")
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": f"❌ Error: {str(e)}", "parse_mode": "HTML"}, timeout=10)
    finally:
        db.close()

def handle_resolve_command(chat_id: int, command_text: str, bot_token: str, db_session_factory) -> None:
    parts = command_text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        text = "⚠️ Usage: <code>/resolve &lt;finding_id&gt;</code>"
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
        return
        
    finding_id = int(parts[1])
    db = db_session_factory()
    try:
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            text = f"❌ Error: Finding with ID <code>{finding_id}</code> not found."
        else:
            finding.is_resolved = True
            db.commit()
            text = f"✅ Incident ID <code>{finding_id}</code> has been marked as <b>RESOLVED</b>."
            
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        logger.error(f"Error updating finding status: {str(e)}")
    finally:
        db.close()

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
