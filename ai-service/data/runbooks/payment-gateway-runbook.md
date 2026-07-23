# Payment Gateway Runbook

## Service Overview
- **Service**: payment-gateway (svc-001)
- **Owner**: team-payments
- **Criticality**: Critical
- **Language**: Java (Spring Boot 3.2)

## Common Issues

### Issue: Payment Processing Failures
**Symptoms**: 5xx errors on /api/payments/process, transaction failures in logs
**Steps**:
1. Check payment-db-mysql connection pool
2. Verify downstream fraud-detection service health
3. Check Kafka payment-events topic lag
4. Review recent deployments for breaking changes
5. Escalate to team-payments on-call if needed

### Issue: Refund Timeout
**Symptoms**: /api/payments/refund returning 504
**Steps**:
1. Check if refund endpoint is under load
2. Verify third-party payment processor status
3. Scale up payment-gateway pods if needed
4. Check database connection pool size

## Health Checks
- GET /actuator/health
- GET /api/payments/health

## Scaling
- Minimum: 3 pods
- Maximum: 10 pods
- Metric: Requests per second > 1000

## Backup / Restore
- Payment DB backed up every 6 hours
- Point-in-time recovery available for 7 days

