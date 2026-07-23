# Setup Guide — AI Change Impact Analyzer

This guide walks you through setting up all **three modules** of the application:

| # | Module | Tech Stack | Default Port |
|---|--------|-----------|---------------|
| 1 | `frontend/` | React 18 + TypeScript + Vite | `3000` |
| 2 | `backend/`  | Spring Boot 3.3 + Java 21/17 + H2 | `8081` |
| 3 | `ai-service/` | FastAPI + Python 3.11 (multi-agent RAG pipeline) | `8000` |

There are **two ways** to run the project:

- **Option A — Docker Compose (recommended)**: builds and runs all three modules together with one command. Best for a quick demo / judging.
- **Option B — Run each module locally**: useful for active development, debugging, and hot-reload.

---

## 0. Prerequisites

Install these before you start:

| Tool | Required For | Version |
|------|--------------|---------|
| [Git](https://git-scm.com/) | Cloning the repo | any recent |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) + Docker Compose | Option A (containerized run) | Compose v3.8+ |
| [Node.js](https://nodejs.org/) + npm | `frontend/` local dev | 20+ |
| [Java JDK](https://adoptium.net/) | `backend/` local dev | 21 (repo also builds on 17) |
| [Maven](https://maven.apache.org/) | `backend/` local build | 3.9+ |
| [Python](https://www.python.org/) | `ai-service/` local dev | 3.11+ |

> 💡 If you only want to run via Docker (Option A), you technically only need **Docker Desktop** — Node/Java/Python are not required on the host since everything builds inside containers.

---

## 1. Clone the Repository

```bash
git clone https://github.com/<your-fork-or-origin>/hackathonImpactAnalyser.git
cd hackathonImpactAnalyser
```

---

## 2. Configure Environment Variables

The project ships with a single root-level `.env.example` that configures **all three modules** at once (Docker Compose reads it and forwards the relevant variables to each container).

```bash
cp .env.example .env
```

Open `.env` and review the key settings:

```env
# Controls ONLY the conversational /chat and /assistant endpoints.
AI_PROVIDER=mock

# Controls the deterministic multi-agent risk-analysis pipeline.
# Keep as "mock" unless you want live-LLM narrative text and have
# raised the backend's ai-service timeout to match.
PIPELINE_AI_PROVIDER=mock

# Optional live-LLM providers (only needed if AI_PROVIDER != mock)
OPENAI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Ports
AI_SERVICE_PORT=8000
BACKEND_PORT=8081
```

> ✅ **No API keys are required to run the app.** The default `mock` provider uses deterministic, rule-based logic so the whole pipeline works out of the box (great for demos and grading).
>
> If you want live LLM responses, set `AI_PROVIDER` (and optionally `PIPELINE_AI_PROVIDER`) to one of `openai`, `groq`, `openrouter`, or `ollama` and fill in the matching API key.

---

## Option A — Run Everything with Docker Compose (Recommended)

### A.1 One-command start (Linux/macOS)

```bash
chmod +x start.sh
./start.sh
```

This script:
1. Copies `.env.example` → `.env` if missing
2. Runs `docker-compose up --build -d`
3. Polls `/health` on the AI service and `/actuator/health` on the backend
4. Prints the URLs for all three services

### A.2 One-command start (Windows / PowerShell)

`start.sh` is a bash script, so on native Windows PowerShell use Docker Compose directly:

```powershell
Copy-Item .env.example .env -ErrorAction SilentlyContinue
docker-compose up --build -d
docker-compose ps
```

(Alternatively, run `./start.sh` inside WSL or Git Bash.)

### A.3 Verify it's running

```bash
docker-compose ps
docker-compose logs -f          # tail all logs
docker-compose logs -f ai-service   # tail a single service
```

Once healthy, open:
- **Frontend** → http://localhost:3000
- **Backend** → http://localhost:8081 (health: `/actuator/health`)
- **AI Service** → http://localhost:8000 (health: `/health`, interactive docs: `/docs`)

### A.4 Stop everything

```bash
./stop.sh
# or
docker-compose down
```

### How the containers connect
Docker Compose creates a bridge network (`analyzer-net`) so containers can resolve each other by service name:

```
frontend  --(nginx/vite proxy /api)-->  backend:8081  --(WebClient)-->  ai-service:8000
```

The `backend` container waits for `ai-service` to report healthy (`depends_on: condition: service_healthy`) before starting, and `frontend` waits for `backend`.

---

## Option B — Run Each Module Locally (Development Mode)

Run these in **three separate terminals**, in this order (AI service → Backend → Frontend), since the backend proxies to the AI service and the frontend proxies to the backend.

### B.1 AI Service (FastAPI + Python 3.11)

```bash
cd ai-service

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) create ai-service/.env for provider keys — same variables as
# the root .env: AI_PROVIDER, OPENAI_API_KEY, GROQ_API_KEY, etc.

# Start the dev server with hot reload
uvicorn app.main:app --port 8000 --reload
```

Verify: open http://localhost:8000/docs (Swagger UI) or `curl http://localhost:8000/health`.

**Seed data** used by the RAG pipeline lives in `ai-service/data/`:
- `cmdb.json` — 19 microservices + dependency graph
- `incidents.json` — 50 historical incidents
- `change_requests.json` — 70 historical change requests
- `source_registry.json` — 23 source code repositories
- `architecture.md` — system architecture reference doc
- `runbooks/*.md` — operational runbooks for key services

No extra setup is needed — this data is loaded automatically at startup.

### B.2 Backend (Spring Boot 3.3 + Java 21)

```bash
cd backend

# Run with the "dev" profile (points at http://localhost:8000 for the AI service)
mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

Or build + run the jar directly:

```bash
mvn clean package -DskipTests
java -jar target/change-impact-analyzer-backend-1.0.0.jar
```

Verify: `curl http://localhost:8081/actuator/health`

**H2 console** (in-memory DB, resets on restart): http://localhost:8081/h2-console
- JDBC URL: `jdbc:h2:mem:analysisdb`
- User: `sa` / Password: *(blank)*

By default the backend expects the AI service at `http://localhost:8000` (see `backend/src/main/resources/application.yml` → `ai-service.url`, overridable via the `AI_SERVICE_URL` env var).

### B.3 Frontend (React 18 + TypeScript + Vite)

```bash
cd frontend
npm install
npm run dev
```

Verify: open http://localhost:3000

The Vite dev server proxies `/api/*` requests to `http://backend:8081` by default (see `frontend/vite.config.ts`). When running the backend locally (not in Docker), you may need to either:
- Run the frontend via Docker Compose too so container DNS (`backend`) resolves, **or**
- Set `VITE_API_BASE_URL=http://localhost:8081` (e.g. in `frontend/.env.local`) so the frontend talks directly to your locally-running backend.

**Useful env vars** (frontend `.env.local`):
```env
VITE_API_BASE_URL=http://localhost:8081
VITE_DIRECT_AI_MODE=false        # true = skip backend, call AI service directly
VITE_AI_SERVICE_URL=http://localhost:8000
```

---

## 3. Running Tests

Each module has its own test suite:

```bash
# AI Service
cd ai-service
pip install pytest pytest-asyncio
pytest tests/ -v

# Backend
cd backend
mvn test

# Frontend
cd frontend
npm test
```

---

## 4. Quick Smoke Test (after startup)

1. `GET http://localhost:8000/health` → `{"status": "healthy", ...}`
2. `GET http://localhost:8081/actuator/health` → `{"status": "UP"}`
3. Open http://localhost:3000 → the hero banner should render
4. In the UI, switch to **Form mode**, submit a sample change request → a full risk report should render across all tabs (Overview, Understanding, Evidence, Incidents, Mitigation, Trace)
5. `GET http://localhost:8081/api/v1/analyses/history` → should return the analysis you just ran

See `TROUBLESHOOTING.md` and `VERIFICATION.md` in the repo root for a full checklist and common-issue fixes.

---

## 5. Common Issues (Quick Reference)

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Connection refused` from backend to AI service | AI service not running / wrong URL | `docker-compose logs ai-service`; check `AI_SERVICE_URL` |
| Frontend blank page | Stale `node_modules` / build error | `rm -rf node_modules && npm install` |
| Backend Docker build fails | Maven dependency download failure | `docker-compose build --no-cache backend` |
| AI service `pip install` conflicts | Corrupted venv / cached wheels | `pip install -r requirements.txt --force-reinstall` |
| Port already in use | Another process bound to 3000/8000/8081 | Change the port in `.env` or stop the conflicting process |
| CORS / API errors in browser | Wrong `VITE_API_BASE_URL` | Confirm it matches your backend's actual URL/port |

Full details: see `TROUBLESHOOTING.md`.

---

## 6. Project Structure Reference

```
hackathonImpactAnalyser/
├── frontend/          # React 18 + TypeScript + Vite        (port 3000)
├── backend/           # Spring Boot 3.3 + Java 21 + H2       (port 8081)
├── ai-service/        # FastAPI + Python 3.11 + Multi-agent RAG (port 8000)
├── docker-compose.yml
├── .env.example
├── start.sh / stop.sh
├── README.md
├── TECHNICAL_ARCHITECTURE.md   # Deep architecture reference (this repo)
├── SETUP_GUIDE.md              # You are here
├── TROUBLESHOOTING.md
└── VERIFICATION.md
```

For a deep dive into how each module works internally (agents, RAG, sanitization, data flow, API contracts), see **`TECHNICAL_ARCHITECTURE.md`**.
