# User Service Runbook

## Service Overview
- **Service**: user-service (svc-002)
- **Owner**: team-platform
- **Criticality**: Critical
- **Language**: Python (FastAPI)

## Common Issues

### Issue: Authentication Failures
**Symptoms**: Users unable to login, /api/auth/login returning 401
**Steps**:
1. Check user-db-postgres connectivity
2. Verify auth-service (svc-018) token validation
3. Check Redis for session data corruption
4. Review recent auth-related changes

### Issue: User Registration Delays
**Symptoms**: /api/auth/register slow responses
**Steps**:
1. Check database connection pool
2. Verify email verification service
3. Check for rate limiting issues

## Health Checks
- GET /health
- GET /api/users/health

## Scaling
- Minimum: 2 pods
- Maximum: 6 pods
- Metric: CPU > 70%

## Dependencies
- database-proxy (svc-004)
- auth-service (svc-018) for token management

