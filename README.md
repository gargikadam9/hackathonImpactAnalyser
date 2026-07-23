# AI Change Impact Analyzer

A full-stack monorepo application for analyzing the impact of system changes using a multi-agent AI pipeline.

## Architecture

```
Frontend (React 18 + TS + Vite :3000)
    ↓
Backend (Spring Boot 3.3 + Java 21 :8081)
    ↓  (proxies /api/v1/*)
AI Service (FastAPI + Python 3.11 :8000)
    ↓
[RAG Sources: cmdb, incidents, change_requests, architecture, runbooks, source_registry]
```

### Multi-Agent Pipeline
1. **Intake Agent** - Analyzes change request scope
2. **Dependency Agent** - Maps service dependencies
3. **Knowledge Agent** - Retrieves relevant documentation (RAG)
4. **Incident Agent** - Finds similar past incidents
5. **Risk Agent** - Calculates risk score & mitigation plan
6. **Notification Agent** - Determines teams to notify
7. **Summary Agent** - Generates comprehensive report

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local AI service dev)
- Java 21+ (for local backend dev)
- Maven 3.9+ (for local backend build)

### Run with Docker (Recommended)

```bash
# Clone and enter the project
cd ai-change-impact-analyzer

# Make start script executable (if not already)
chmod +x start.sh

# Start all services (mock mode - no API keys needed)
./start.sh

# Or manually:
docker-compose up --build -d
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8081
- **AI Service**: http://localhost:8000
- **API Docs** (AI Service): http://localhost:8000/docs

### Run Locally (Development)

#### 1. AI Service
```bash
cd ai-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
```

#### 2. Backend
```bash
cd backend
mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

#### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

## Configuration

Copy `.env.example` to `.env` and configure:

```env
# Provider: mock, openai, groq, openrouter, ollama
AI_PROVIDER=mock

# Optional: Set your API keys for live AI
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
```

## Provider Modes

| Provider | Chat | Embeddings | API Key Required |
|----------|------|------------|------------------|
| **mock** | Rule-based | Deterministic | No |
| **openai** | GPT-4 | text-embedding-3-small | Yes |
| **groq** | Llama3 70B | Local fallback | Yes |
| **openrouter** | Claude-3 | Local fallback | Yes |
| **ollama** | Local model | Local fallback | No (local model) |

## API Endpoints

### AI Service (`/health`)
- `GET /health` - Health check
- `POST /api/v1/chat/general` - General chat
- `POST /api/v1/assistant/respond` - Unified assistant (classifies intent)
- `POST /api/v1/change-impact/analyze` - Full change impact analysis
- `POST /api/v1/change-impact/analyze-prompt` - Analysis from prompt
- `GET /api/v1/change-types` - Available change types
- `GET /api/v1/components` - System components
- `GET /api/v1/system/technical-details` - Architecture overview

### Backend (proxies to AI Service)
All `/api/v1/*` routes proxied to AI service, plus:
- `GET /api/v1/analyses/history` - Latest 20 analyses
- `GET /api/v1/analyses/{analysisId}` - Single analysis by ID

## Seed Data
- **cmdb.json**: 19 microservices with dependencies
- **incidents.json**: 50 historical incidents
- **change_requests.json**: 70 change requests
- **source_registry.json**: 23 source code repositories
- **architecture.md**: System architecture documentation
- **runbooks/**: Operational runbooks for key services

## Testing

### AI Service
```bash
cd ai-service
pip install pytest pytest-asyncio
pytest tests/ -v
```

### Backend
```bash
cd backend
mvn test
```

### Frontend
```bash
cd frontend
npm test
```

## Project Structure

```
ai-change-impact-analyzer/
├── frontend/          # React 18 + TypeScript + Vite
├── backend/           # Spring Boot 3.3 + Java 21 + H2
├── ai-service/        # FastAPI + Python 3.11 + Multi-agent RAG
├── docker-compose.yml
├── .env.example
├── start.sh / stop.sh
└── README.md
```

