# RepoLeak Watcher X

**Advanced Real-Time GitHub Secret Exposure & Threat Intelligence Platform**

RepoLeak Watcher X is an enterprise-grade cybersecurity intelligence platform built for blue-team monitoring, DevSecOps automation, and secret exposure research. It monitors public GitHub repositories and scans them in real time for exposed credentials, keys, private configs, and certificates, automatically notifying security response teams.

---

## Key Features

1. **Intrusion Detection Scanner**: Real-time pattern correlation matching with Shannon entropy score mapping to identify high-fidelity credentials.
2. **Context-Aware AI Review**: Explains the impact of leaks and filters out dummy keys or placeholders automatically.
3. **Cyber SOC Dashboard**: Futuristic dark dashboard HUD featuring real-time WebSocket streams, leak distribution graphs, and repository monitoring lists.
4. **HTML Telegram Notifications**: Direct alert dispatching to security channels with quick resolution buttons.
5. **Standalone Compatibility**: Configured to run on SQLite locally without external services, or scale to PostgreSQL, Redis, and Celery workers in production.

---

## Project Structure

```
raven2/
├── backend/
│   ├── app/
│   │   ├── api/             # API Router endpoints (Auth, Findings, Scans, Metrics)
│   │   ├── models/          # SQLAlchemy Database Models
│   │   ├── schemas/         # Pydantic Schemas for validation
│   │   ├── services/        # Scanner, Telegram alerts, AI assessor, GitHub client
│   │   ├── config.py        # Centralized settings loader
│   │   ├── database.py      # SQLAlchemy connection engine
│   │   └── main.py          # FastAPI application & threat simulator
│   ├── requirements.txt     # Python backend requirements
│   ├── run.py               # Local runtime runner
│   └── test_scanner.py      # Scanner tests script
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages (layout, HUD, live-feed, analytics, settings)
│   │   ├── components/      # UI Elements & gauges
│   │   ├── store/           # Zustand state store with WebSocket connection
│   │   └── styles/          # Neon animations and glassmorphism styling
│   ├── package.json         # Node packaging config
│   ├── tailwind.config.js   # Tailwind custom theme definitions
│   └── tsconfig.json        # TypeScript configuration
├── docker-compose.yml       # Production-ready docker compose orchestration
├── .env.example             # Configuration variables blueprint
└── kubernetes/              # Kubernetes deploy manifests
```

---

## Getting Started (Standalone Run)

To run locally without Docker or external databases:

### 1. Backend Setup

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the automated scanner tests to confirm heuristics are functioning:
   ```bash
   python test_scanner.py
   ```
4. Start the FastAPI API server:
   ```bash
   python run.py
   ```
   *The backend will automatically initialize `repoleak.db` (SQLite) and launch a threat simulator thread that pushes mock leaks every 8 seconds.*

### 2. Frontend Setup

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.
   *The frontend automatically authenticates as `admin@repoleak.io` (password: `password123`) and binds the WebSocket listener.*

---

## Docker Compose Setup (PostgreSQL + Redis + Workers)

To test the entire containerized stack:

1. Setup environment values:
   ```bash
   cp .env.example .env
   ```
2. Launch the services:
   ```bash
   docker-compose up --build
   ```

---

## API Documentation

FastAPI interactive OpenAPI Swagger documentation is exposed on:
- [http://localhost:8000/docs](http://localhost:8000/docs)

Key endpoints:
- `/api/v1/auth/token`: Retrieve JWT token.
- `/api/v1/findings/`: Filter, search, and retrieve exposed secrets.
- `/api/v1/findings/{id}/analyze-ai`: Re-evaluate context using AI.
- `/api/v1/scans/repositories`: Register a new repository for monitoring.
- `/api/v1/scans/history`: Fetch scans audit logs.
- `/api/v1/metrics/overview`: Retrieve SOC graph indicators.

---

## Licensing & Ethics
This platform is designed strictly for **defensive operations**, threat auditing, and blue-team monitoring. Use with authorization.
