# Order Service Runbook

## Service Overview
- **Service**: order-service (svc-005)
- **Owner**: team-orders
- **Criticality**: Critical
- **Language**: Java (Spring Boot 3.2)

## Common Issues

### Issue: Order Creation Failures
**Symptoms**: /api/orders/create returning errors
**Steps**:
1. Verify payment-gateway (svc-001) is healthy
2. Check inventory-service (svc-006) stock availability
3. Verify order-db-postgres connectivity
4. Check Kafka order-events topic

### Issue: Order Status Not Updating
**Symptoms**: Orders stuck in pending state
**Steps**:
1. Check order event consumers
2. Verify Kafka consumer group lag
3. Check for failed database transactions
4. Review order state machine logic

## Health Checks
- GET /actuator/health
- GET /api/orders/health

## Scaling
- Minimum: 3 pods
- Maximum: 8 pods
- Metric: Queue depth > 100

## Dependencies
- user-service (svc-002) for user validation
- fraud-detection (svc-008) for fraud checks
- product-catalog (svc-009) for product data

