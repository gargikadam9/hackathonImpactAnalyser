# AI Change Impact Analyzer - Build Plan

## Project Structure
```
ai-change-impact-analyzer/
├── frontend/                    # React 18 + TypeScript + Vite (port 3000)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   ├── Form/
│   │   │   ├── Report/
│   │   │   ├── RiskGauge.tsx
│   │   │   ├── TypingIndicator.tsx
│   │   │   └── SuggestionChips.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── backend/                     # Spring Boot 3.3 + Java 21 + H2 (port 8081)
│   ├── src/main/java/com/changeanalyzer/
│   │   ├── controller/
│   │   ├── service/
│   │   ├── model/
│   │   ├── repository/
│   │   └── config/
│   ├── src/main/resources/
│   │   ├── application.yml
│   │   └── data/
│   ├── pom.xml
│   └── Dockerfile
├── ai-service/                  # FastAPI + Python (port 8000)
│   ├── app/
│   │   ├── agents/
│   │   ├── rag/
│   │   ├── routes/
│   │   ├── models/
│   │   └── main.py
│   ├── data/
│   │   ├── cmdb.json
│   │   ├── incidents.json
│   │   ├── change_requests.json
│   │   ├── source_registry.json
│   │   ├── architecture.md
│   │   └── runbooks/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── start.sh
├── stop.sh
├── README.md
├── TROUBLESHOOTING.md
└── VERIFICATION.md
```

## Build Order
1. **Root files**: docker-compose, .env.example, scripts, README
2. **Seed data**: All JSON/MD seed files for RAG
3. **AI Service**: FastAPI app with agents, RAG, routes
4. **Backend**: Spring Boot with proxying, H2 persistence
5. **Frontend**: React app with all UI components
6. **Dockerfiles**: Container definitions
7. **Tests**: Test files for all layers

## Key Design Decisions
- Mock mode is default - no API keys required to run
- Backend proxies /api/v1/* to AI service
- Frontend can optionally connect directly to AI service
- FAISS for vector similarity, deterministic fallback in mock mode
- H2 for analysis history persistence

