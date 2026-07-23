# Verification Checklist

## Pre-Deployment Verification

### 1. Docker Build
- [ ] `docker-compose build` completes successfully
- [ ] All three services build without errors

### 2. AI Service
- [ ] `GET /health` returns `{"status": "healthy"}`
- [ ] Data counts show: 19 services, 50 incidents, 70 CRs
- [ ] `/api/v1/change-types` returns 8 types
- [ ] `/api/v1/components` returns 19 components
- [ ] Mock mode analysis returns all required fields

### 3. Backend
- [ ] Starts on port 8081
- [ ] Proxies `/api/v1/change-impact/analyze` to AI service
- [ ] Persists analysis to H2
- [ ] `/api/v1/analyses/history` returns JSON array
- [ ] H2 console available at `/h2-console`

### 4. Frontend
- [ ] Serves on port 3000
- [ ] Hero banner with animations displays
- [ ] Chat mode: sends message -> receives reply
- [ ] Form mode: submits analysis -> shows report
- [ ] Report tabs: Overview, Understanding, Evidence, Incidents, Mitigation, Trace
- [ ] Risk gauge shows correct score/level
- [ ] Typing indicator appears during loading
- [ ] Suggestion chips are clickable

### 5. Report Fields Verification
Every analysis response must include:
- [ ] analysisId (string)
- [ ] riskScore (0.0 - 1.0)
- [ ] riskLevel (low/medium/high/critical)
- [ ] confidence (0.0 - 1.0)
- [ ] impactedServices (array)
- [ ] teamsToNotify (array)
- [ ] potentialRisks (array)
- [ ] recommendedTests (array)
- [ ] similarIncidents (array)
- [ ] mitigationPlan (array)
- [ ] executiveSummary (string)
- [ ] agentTraces (array of 7)
- [ ] interpretedIntent (string)
- [ ] retrievedEvidence (array)
- [ ] dataSourcesUsed (array)
- [ ] processingTimeMs (number)
- [ ] mockMode (boolean)

### 6. Multi-Agent Pipeline
Agent execution order:
- [ ] 1. intake -> completed
- [ ] 2. dependency -> completed
- [ ] 3. knowledge -> completed
- [ ] 4. incident -> completed
- [ ] 5. risk -> completed
- [ ] 6. notification -> completed
- [ ] 7. summary -> completed

### 7. Tests
- [ ] AI service tests pass: `pytest ai-service/tests/ -v`
- [ ] Backend tests pass: `mvn test`
- [ ] Frontend tests pass: `npm test`

## Assumptions

1. **Mock mode is default**: No API keys needed for basic functionality
2. **All data is synthetic**: CMDB, incidents, CRs, and runbooks are sample data
3. **H2 in-memory**: Data resets on backend restart
4. **Single-node**: Designed for development/demo, not production
5. **No auth**: API endpoints are unauthenticated
6. **Docker networking**: Services communicate via Docker compose network
7. **Direct AI mode**: Frontend can optionally skip backend proxy

## Production Considerations
- Replace H2 with PostgreSQL for persistence
- Add authentication/authorization
- Use dedicated vector DB (Pinecone, Weaviate) for production RAG
- Add rate limiting and API key management
- Configure HTTPS/TLS
- Set up monitoring and alerting
- Add data backup and disaster recovery

