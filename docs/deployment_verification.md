# Deployment Verification Checklist

## Pre-Deployment Verification
- [ ] All CI pipeline tests passing
- [ ] Kubernetes manifests validated with `kubectl --dry-run`
- [ ] Database migration scripts prepared
- [ ] Secrets configured in the target environment
- [ ] Rollback plan documented

## Deployment Verification
- [ ] Apply Kubernetes configurations in sequence:
  - [ ] Namespace
  - [ ] Database
  - [ ] Application
  - [ ] Monitoring
- [ ] Verify pod status (`kubectl get pods -n sequential-questioning`)
- [ ] Check application logs for errors
- [ ] Verify database connection
- [ ] Confirm monitoring dashboards are operational

## Post-Deployment Verification
- [ ] Test API endpoints
- [ ] Verify MCP interface functionality
- [ ] Confirm metrics collection
- [ ] Execute performance tests against production
- [ ] Verify application scaling under load

## Security Verification
- [ ] Confirm secrets are properly secured
- [ ] Verify network policies
- [ ] Run security scan on deployed containers
- [ ] Check RBAC permissions

## Availability Testing
- [ ] Test pod disruption and recovery
- [ ] Verify database failover
- [ ] Simulate zone failure recovery

## Production Readiness
- [ ] Documentation updated with production deployment details
- [ ] Support contact information provided
- [ ] Monitoring alerts properly configured
- [ ] On-call rotation established
- [ ] User acceptance testing complete

## Sign-off
- [ ] DevOps team sign-off
- [ ] Development team sign-off
- [ ] Product owner sign-off 