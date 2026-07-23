# API Gateway Runbook

## Service Overview
- **Service**: api-gateway (svc-007)
- **Owner**: team-platform
- **Criticality**: Critical
- **Language**: Go (Kong)

## Common Issues

### Issue: High Latency / Timeouts
**Symptoms**: All downstream services reporting slow responses
**Steps**:
1. Check gateway CPU/memory usage
2. Verify upstream service health
3. Check rate limiting configuration
4. Review Kong plugin execution times
5. Scale up gateway pods if needed

### Issue: Authentication Failures
**Symptoms**: 401 errors across all routes
**Steps**:
1. Verify user-service (svc-002) health
2. Check auth-service (svc-018) token validation
3. Review JWT secret rotation
4. Check OIDC provider status

## Health Checks
- GET /health
- GET /status

## Scaling
- Minimum: 3 pods
- Maximum: 10 pods
- Metric: Connections > 10000

## Rate Limiting
- Default: 100 req/s per client
- Premium: 500 req/s per client
- Burst: 1.5x limit for 10 seconds

