# Sequential Questioning MCP Server - Operational Runbook

This runbook provides guidance for operating and maintaining the Sequential Questioning MCP Server in production environments.

## Prerequisites

- Access to the Kubernetes cluster
- `kubectl` installed and configured
- Access to monitoring systems (Prometheus/Grafana)

## Deployment

The application is deployed using Kubernetes and can be deployed to three environments:

### Development Environment

```bash
kubectl apply -k k8s/overlays/dev
```

### Staging Environment

```bash
kubectl apply -k k8s/overlays/staging
```

### Production Environment

```bash
kubectl apply -k k8s/overlays/prod
```

## Monitoring

The application metrics are exposed via Prometheus and visualized in Grafana.

### Key Metrics to Monitor

- **Request Rate**: Number of requests per second
- **Error Rate**: Percentage of requests that result in errors
- **Response Time**: Average and p95/p99 response times
- **Resource Usage**: CPU and memory utilization

### Accessing Monitoring Dashboards

- Prometheus: http://prometheus:9090 (internal to cluster)
- Grafana: http://grafana:3000 (internal to cluster)

Use port-forwarding to access these services locally:

```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

## Alerting

The following alerts are configured:

- **High Error Rate**: >5% of requests result in errors for 5 minutes
- **Slow Response Time**: p95 response time >500ms for 10 minutes
- **High Resource Usage**: CPU usage >80% for 5 minutes
- **Instance Down**: Pod not responding for 1 minute

## Common Operations

### Scaling

To manually scale the deployment:

```bash
kubectl scale deployment -n <namespace> sequential-questioning --replicas=<number>
```

### Viewing Logs

```bash
kubectl logs -n <namespace> -l app=sequential-questioning -f
```

### Checking Pod Status

```bash
kubectl get pods -n <namespace> -l app=sequential-questioning
```

### Restarting the Application

```bash
kubectl rollout restart -n <namespace> deployment/sequential-questioning
```

## Troubleshooting

### High Error Rate

1. Check application logs for errors
2. Verify database connectivity
3. Check vector database (Qdrant) connectivity
4. Verify resource utilization is not causing issues

### Slow Response Time

1. Check CPU and memory usage
2. Verify database performance
3. Check vector database query performance
4. Consider scaling up if resource-constrained

### Pod Crash Loop

1. Check logs before crash: `kubectl logs -n <namespace> <pod-name> --previous`
2. Verify environment variables and secrets are properly set
3. Check for resource constraints

### Database Connection Issues

1. If you see errors like `The asyncio extension requires an async driver to be used`, verify that:
   - The `DATABASE_URL` environment variable uses the correct format
   - For async operations, PostgreSQL URLs should use `postgresql+asyncpg://` prefix
   - The asyncpg driver is installed and available
2. Check network connectivity to the database: `kubectl exec -it <pod> -- nc -zv <db-host> 5432`
3. Verify database credentials are correct
4. Check if the database service is healthy

### Vector Database (Qdrant) Connection Issues

1. If you see errors like `Connection refused` or `ResponseHandlingException` related to Qdrant:
   - Verify that the `QDRANT_URL` environment variable is correctly set (e.g., `http://qdrant:6333`)
   - Check if the Qdrant service is running: `kubectl get pods -n <namespace> -l app=qdrant`
   - Verify network connectivity: `kubectl exec -it <pod> -- curl -v <qdrant-url>/collections`
2. If the connection is intermittent:
   - Check for resource constraints on the Qdrant pod
   - Consider scaling up Qdrant resources if needed
   - Verify that readiness probes are configured correctly
3. Restart the Qdrant service if needed: `kubectl rollout restart -n <namespace> deployment/qdrant`

## Backup and Restore

### Database Backup

Backup the PostgreSQL database:

```bash
kubectl exec -n <namespace> <postgres-pod> -- pg_dump -U postgres sequential_questioning > backup.sql
```

### Vector Database Backup

Backup the Qdrant database:

```bash
# TBD based on Qdrant backup mechanism
```

## Maintenance Windows

Schedule maintenance windows for non-peak hours:

- **Weekdays**: 00:00-04:00 UTC
- **Weekends**: 08:00-12:00 UTC

## Version Updates

1. Update the image tag in the CI/CD pipeline
2. Monitor the deployment progress
3. Verify application is functioning correctly
4. Roll back if issues are detected

## Contact Information

- **Primary Contact**: DevOps Team
- **Secondary Contact**: Development Team Lead

## Reference Documentation

- [API Reference](./api_reference.md)
- [Deployment Guide](./deployment.md)
- [Architecture Documentation](./architecture.md) 