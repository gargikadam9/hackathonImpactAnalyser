# Troubleshooting Guide

## Common Issues

### 1. "Connection refused" to AI Service
**Cause**: Backend cannot reach AI service
**Fix**: 
- Ensure AI service is running: `docker-compose ps ai-service`
- Check logs: `docker-compose logs ai-service`
- Verify `AI_SERVICE_URL` in docker-compose.yml matches the service name

### 2. Frontend shows blank page
**Cause**: Build error or missing dependencies
**Fix**:
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### 3. Docker build fails for backend
**Cause**: Maven download failure
**Fix**:
```bash
docker-compose build --no-cache backend
# Or increase Maven memory in pom.xml:
# MAVEN_OPTS: -Xmx1g
```

### 4. AI Service dependency issues
**Cause**: Python package conflicts
**Fix**:
```bash
cd ai-service
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### 5. No seed data loaded
**Cause**: Data files not found
**Fix**: Ensure `ai-service/data/` directory contains all JSON and MD files

### 6. Mock mode not working
**Cause**: Provider not set to mock
**Fix**: Set `AI_PROVIDER=mock` in .env

### 7. Port already in use
**Cause**: Another service using the same port
**Fix**: Change ports in .env or stop conflicting services

### 8. Frontend cannot connect to API
**Cause**: CORS or proxy misconfiguration
**Fix**: 
- Check VITE_API_BASE_URL is correct
- Backend CORS filter allows frontend origin

## Verification Checklist

- [ ] `docker-compose up` starts without errors
- [ ] `GET /health` returns 200 for AI service
- [ ] Backend proxies to AI service successfully
- [ ] Frontend loads and shows hero banner
- [ ] Chat mode sends messages
- [ ] Form mode submits analysis
- [ ] Report displays with all tabs
- [ ] History persists in H2 database
- [ ] Tests pass for all layers

