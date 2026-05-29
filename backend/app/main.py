import asyncio
import random
import logging
import threading
import time
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api.endpoints import auth, findings, scans, metrics
from app.models.repository import Repository
from app.models.finding import Finding
from app.models.scan_history import ScanHistory
from app.api.endpoints.auth import get_password_hash
from app.models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DB tables automatically
Base.metadata.create_all(bind=engine)

# Seed an initial user if not present (admin@repoleak.io / password123)
def seed_admin_user():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@repoleak.io").first()
        if not admin:
            hashed_pwd = get_password_hash("password123")
            user = User(
                email="admin@repoleak.io",
                hashed_password=hashed_pwd,
                role="admin"
            )
            db.add(user)
            db.commit()
            logger.info("Admin user seeded: admin@repoleak.io / password123")
    except Exception as e:
        logger.error(f"Error seeding user: {str(e)}")
    finally:
        db.close()

seed_admin_user()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Cybersecurity intelligence engine scanning repositories for exposed credentials",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    from app.services.telegram import start_telegram_polling
    start_telegram_polling(SessionLocal)
    
    from app.services.auto_scanner import start_auto_scan_daemon
    start_auto_scan_daemon(SessionLocal)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(findings.router, prefix=settings.API_V1_STR)
app.include_router(scans.router, prefix=settings.API_V1_STR)
app.include_router(metrics.router, prefix=settings.API_V1_STR)

# Health check endpoint (no auth required)
@app.get("/health")
def health_check():
    """System health check for Docker, load balancers, and monitoring."""
    status = {"status": "ok", "service": settings.PROJECT_NAME}
    
    # Check DB connectivity
    try:
        db = SessionLocal()
        db.execute(
            __import__('sqlalchemy').text("SELECT 1")
        )
        db.close()
        status["database"] = "connected"
    except Exception as e:
        status["database"] = f"error: {str(e)}"
        status["status"] = "degraded"
    
    # Check Redis connectivity
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2)
        r.ping()
        status["redis"] = "connected"
    except Exception:
        status["redis"] = "unavailable"
    
    # Report scanner config
    status["simulation_mode"] = settings.SIMULATION_MODE
    status["auto_scan_enabled"] = True
    status["public_crawler_enabled"] = settings.SCAN_PUBLIC_REPOS
    status["github_tokens_configured"] = len(settings.github_token_list)
    status["telegram_configured"] = bool(settings.TELEGRAM_BOT_TOKEN)
    
    return status

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Connection might be dead
                logger.error(f"Broadcast error: {str(e)}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive by waiting for client messages
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Cyber Threat Intelligence Simulator Thread
MOCK_REPOS = [
    {"name": "finance-ledger-v4", "owner": "GlobalBankCorp", "url": "https://github.com/GlobalBankCorp/finance-ledger-v4", "stars": 1240},
    {"name": "auth-microservice", "owner": "AuthFlow", "url": "https://github.com/AuthFlow/auth-microservice", "stars": 85},
    {"name": "kubernetes-deployments", "owner": "DevOpsSystem", "url": "https://github.com/DevOpsSystem/kubernetes-deployments", "stars": 512},
    {"name": "nextjs-saas-template", "owner": "SaaSBuilders", "url": "https://github.com/SaaSBuilders/nextjs-saas-template", "stars": 3442},
    {"name": "trading-bot", "owner": "AlgoTradingHQ", "url": "https://github.com/AlgoTradingHQ/trading-bot", "stars": 922}
]

MOCK_FINDINGS = [
    {
        "secret_type": "AWS Access Key",
        "secret_value": "AKIAIOSFODNN7EXAMPLE",
        "severity": "CRITICAL",
        "confidence": 0.98,
        "file_path": "infra/terraform/providers.tf",
        "line_number": 14,
        "snippet": "--> 14:   access_key = \"AKIAIOSFODNN7EXAMPLE\"\n    15:   secret_key = \"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\"\n    16:   region     = \"us-east-1\"",
        "ai_analysis": "[AI Security Analyst] The AWS Access Key exposed in terraform configurations allows immediate programmatic infrastructure modifications. An attacker could deploy compute resources for cryptomining, leading to high financial charges.",
        "disclosure_status": "Pending"
    },
    {
        "secret_type": "Stripe API Key",
        "secret_value": "sk_live_51NABC123XYZ789",
        "severity": "CRITICAL",
        "confidence": 0.96,
        "file_path": "backend/payments/stripe.js",
        "line_number": 8,
        "snippet": "     7: const stripe = require('stripe');\n-->  8: const client = stripe('sk_live_51NABC123XYZ789');\n     9: \n    10: exports.charge = async (amount) => {",
        "ai_analysis": "[AI Security Analyst] This is a Stripe Production secret key. Exposing it grants absolute programmatic control over customer cards, transaction processing, refunds, and bank account configurations.",
        "disclosure_status": "Pending"
    },
    {
        "secret_type": "OpenAI API Key",
        "secret_value": "sk-proj-7YF8H9K8D7F6S5D4E3W2Q1A0S9D8F7G6H5J4K3L2",
        "severity": "HIGH",
        "confidence": 0.92,
        "file_path": "src/components/chat/GeminiModel.ts",
        "line_number": 22,
        "snippet": "    21:     headers: {\n--> 22:         'Authorization': 'Bearer sk-proj-7YF8H9K8D7F6S5D4E3W2Q1A0S9D8F7G6H5J4K3L2',\n    23:         'Content-Type': 'application/json'\n    24:     }",
        "ai_analysis": "[AI Security Analyst] Exposed OpenAI key allows unauthenticated API access. An attacker could abuse your quota, leading to immediate billing exhaustion.",
        "disclosure_status": "Pending"
    },
    {
        "secret_type": "Google API Key",
        "secret_value": "AIzaSyD7F6S5D4E3W2Q1A0S9D8F7G6H5J4K3L2",
        "severity": "HIGH",
        "confidence": 0.88,
        "file_path": "android/app/src/main/res/values/strings.xml",
        "line_number": 4,
        "snippet": "    3:     <string name=\"app_name\">MyMapApp</string>\n--> 4:     <string name=\"google_maps_key\">AIzaSyD7F6S5D4E3W2Q1A0S9D8F7G6H5J4K3L2</string>\n    5: </resources>",
        "ai_analysis": "[AI Security Analyst] This Google Maps API key is embedded in Android application configurations. Exposing it without API restrictions in Google Cloud Console allows attackers to query Geocoding and Maps APIs, driving up usage costs.",
        "disclosure_status": "Pending"
    },
    {
        "secret_type": "Generic Credentials URL",
        "secret_value": "postgresql://db_admin:AdminSecureP@ss123@prod-db.cloud.net:5432/finance",
        "severity": "HIGH",
        "confidence": 0.90,
        "file_path": "docker-compose.yml",
        "line_number": 19,
        "snippet": "    18:     environment:\n--> 19:       - DATABASE_URL=postgresql://db_admin:AdminSecureP@ss123@prod-db.cloud.net:5432/finance\n    20:       - PORT=8080",
        "ai_analysis": "[AI Security Analyst] Postgres database credentials leaked in plaintext inside docker-compose environment setups. Exposes internal database configurations to unauthorized remote connections.",
        "disclosure_status": "Pending"
    },
    {
        "secret_type": "HuggingFace Token",
        "secret_value": "hf_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7",
        "severity": "HIGH",
        "confidence": 0.94,
        "file_path": "scripts/download_model.py",
        "line_number": 10,
        "snippet": "     9: from huggingface_hub import login\n--> 10: login(token=\"hf_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7\")\n    11: ",
        "ai_analysis": "[AI Security Analyst] HuggingFace token exposed in model download scripts. Allows programmatic model downloads, user space uploads, and modification of repository assets.",
        "disclosure_status": "Pending"
    },
    {
        "secret_type": "Groq API Key",
        "secret_value": "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",
        "severity": "HIGH",
        "confidence": 0.92,
        "file_path": "src/llm/client.ts",
        "line_number": 5,
        "snippet": "    4: const client = new Groq({\n--> 5:   apiKey: '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'\n    6: });",
        "ai_analysis": "[AI Security Analyst] Groq API key leaked in LLM client configurations. Bad actors can hijack compute quota and deplete query credits.",
        "disclosure_status": "Pending"
    }
]

def run_simulation():
    """
    Simulation engine running in a separate daemon thread to simulate real-time
    intelligence scanning and findings discovery.
    Pushes events dynamically through WebSocket connections.
    """
    # Sleep to allow FastAPI server to start
    time.sleep(2)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    logger.info("Threat Intelligence Simulator started.")
    
    while True:
        if not settings.SIMULATION_MODE:
            time.sleep(5)
            continue
            
        db = SessionLocal()
        try:
            # Pick a random mock repo
            repo_meta = random.choice(MOCK_REPOS)
            
            # Find or insert repo
            repo = db.query(Repository).filter(Repository.url == repo_meta["url"]).first()
            if not repo:
                repo = Repository(
                    name=repo_meta["name"],
                    owner=repo_meta["owner"],
                    stars=repo_meta["stars"],
                    url=repo_meta["url"],
                    is_monitored=1
                )
                db.add(repo)
                db.commit()
                db.refresh(repo)
                
            # Log scan history
            duration = random.randint(1500, 4800)
            scan_log = ScanHistory(
                repository_id=repo.id,
                status="completed",
                findings_count=1,
                scan_duration_ms=duration
            )
            db.add(scan_log)
            
            # Select finding template
            finding_tpl = random.choice(MOCK_FINDINGS).copy()
            
            # Randomize file path / line slightly to look real
            finding_tpl["line_number"] = random.randint(5, 120)
            
            # Write leak finding with raw unmasked secrets
            raw_secret = finding_tpl["secret_value"]
            
            new_finding = Finding(
                secret_type=finding_tpl["secret_type"],
                secret_value=raw_secret,
                severity=finding_tpl["severity"],
                confidence=finding_tpl["confidence"],
                file_path=finding_tpl["file_path"],
                line_number=finding_tpl["line_number"],
                snippet=finding_tpl["snippet"],
                ai_analysis=finding_tpl["ai_analysis"],
                disclosure_status=finding_tpl["disclosure_status"],
                repository_id=repo.id
            )
            
            db.add(new_finding)
            db.commit()
            db.refresh(new_finding)
            
            # Send Telegram alert for simulated leak
            try:
                from app.services.telegram import send_telegram_alert
                repo_data = {
                    "name": repo.name,
                    "owner": repo.owner,
                    "url": repo.url
                }
                finding_data = {
                    "id": new_finding.id,
                    "secret_type": new_finding.secret_type,
                    "secret_value": finding_tpl["secret_value"],
                    "severity": new_finding.severity,
                    "confidence": new_finding.confidence,
                    "file_path": new_finding.file_path,
                    "line_number": new_finding.line_number,
                    "snippet": new_finding.snippet,
                    "ai_analysis": new_finding.ai_analysis
                }
                send_telegram_alert(finding_data, repo_data)
            except Exception as tg_err:
                logger.error(f"Simulator failed to send Telegram alert: {str(tg_err)}")

            # Construct broadcast message
            event = {
                "event": "new_finding",
                "finding": {
                    "id": new_finding.id,
                    "secret_type": new_finding.secret_type,
                    "secret_value": new_finding.secret_value,
                    "severity": new_finding.severity,
                    "confidence": new_finding.confidence,
                    "file_path": new_finding.file_path,
                    "line_number": new_finding.line_number,
                    "snippet": new_finding.snippet,
                    "ai_analysis": new_finding.ai_analysis,
                    "disclosure_status": new_finding.disclosure_status,
                    "created_at": new_finding.created_at.isoformat(),
                    "repository": {
                        "name": repo.name,
                        "owner": repo.owner,
                        "url": repo.url,
                        "stars": repo.stars
                    }
                }
            }
            
            # Broadcast to active WebSockets synchronously within the running loop
            loop.run_until_complete(manager.broadcast(event))
            logger.info(f"Simulated finding generated: {new_finding.secret_type} in {repo.owner}/{repo.name}")
            
        except Exception as e:
            logger.error(f"Simulator Error: {str(e)}")
        finally:
            db.close()
            
        time.sleep(settings.SIMULATION_INTERVAL_SECONDS)

# Launch simulator thread
if settings.SIMULATION_MODE:
    sim_thread = threading.Thread(target=run_simulation, daemon=True)
    sim_thread.start()
