# Fraud Detection Runbook

## Service Overview
- **Service**: fraud-detection (svc-008)
- **Owner**: team-risk
- **Criticality**: Critical
- **Language**: Python (FastAPI)

## Common Issues

### Issue: High False Positive Rate
**Symptoms**: Legitimate transactions being declined
**Steps**:
1. Check ML model version and last training date
2. Review feature distribution drift
3. Verify ml-inference (svc-013) feature computation
4. Check if new fraud patterns need model retraining
5. Adjust risk thresholds temporarily

### Issue: Scoring Service Unavailable
**Symptoms**: /api/fraud/score returning 503
**Steps**:
1. Verify ml-inference service health
2. Check fraud-db-redis cache
3. Verify Redis connection pool
4. Scale up fraud-detection pods

## Health Checks
- GET /health
- GET /api/fraud/health

## Scaling
- Minimum: 2 pods
- Maximum: 5 pods
- Metric: Request latency > 500ms

## Model Information
- Current: fraud-detection-v3
- Last trained: 2024-06-15
- Training frequency: Weekly
- Features: 128
- AUC: 0.94

