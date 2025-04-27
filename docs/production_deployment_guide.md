# Production Deployment Guide for Sequential Questioning MCP Server

This guide outlines the steps required to deploy the Sequential Questioning MCP Server to a production environment using Kubernetes.

## Prerequisites

Before deploying to production, ensure you have the following:

1. **Access to a Kubernetes cluster**
   - Production-grade Kubernetes cluster with at least 3 nodes
   - Kubectl command-line tool configured to access your cluster
   - Helm 3 installed

2. **Container Registry access**
   - GitHub Container Registry (ghcr.io) credentials
   - Docker installed locally (for manual builds if needed)

3. **Required CI/CD access**
   - GitHub Actions access with appropriate secrets configured
   - Required secrets:
     - `KUBECONFIG_PROD`: Base64-encoded kubeconfig for the production cluster
     - `GITHUB_TOKEN`: For container registry access

4. **Database setup**
   - Production PostgreSQL database (can be provisioned by cloud provider)
   - Qdrant vector database instance

## Deployment Architecture

The Sequential Questioning MCP Server follows a microservices architecture in production:

- **Application Tier**: Containerized application deployed as Kubernetes Deployment with auto-scaling
- **Database Tier**: PostgreSQL for relational data (external managed service recommended)
- **Vector Database**: Qdrant for vector storage (external managed service recommended)
- **Monitoring Stack**: Prometheus and Grafana for metrics and monitoring
- **Ingress**: Kubernetes Ingress for routing external traffic to the service

## Deployment Procedure

### 1. Environment Configuration

1. Create a dedicated namespace (if not using CI/CD):
   ```bash
   kubectl apply -f k8s/base/namespace.yaml
   ```

2. Configure environment-specific secrets:
   ```bash
   # Create a new secret.yaml file based on the template
   cp k8s/base/secret.yaml k8s/overlays/prod/secret.yaml
   
   # Edit the secret values with production credentials
   # Important: Never commit real secrets to version control
   ```

### 2. Automated Deployment (Recommended)

1. Tag a release in GitHub:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. Create a GitHub release from the tag to trigger the CI/CD pipeline.

3. Monitor the GitHub Actions workflow for deployment progress.

4. Verify the deployment:
   ```bash
   kubectl get pods -n sequential-questioning
   kubectl rollout status deployment/prod-sequential-questioning -n sequential-questioning
   ```

### 3. Manual Deployment (Alternative)

1. Build and push the Docker image:
   ```bash
   docker build -t ghcr.io/your-org/sequential-questioning:v1.0.0 .
   docker push ghcr.io/your-org/sequential-questioning:v1.0.0
   ```

2. Deploy using Kustomize:
   ```bash
   cd k8s/overlays/prod
   kustomize edit set image ghcr.io/your-org/sequential-questioning=ghcr.io/your-org/sequential-questioning:v1.0.0
   kubectl apply -k .
   ```

## Configuration

### Application Configuration

The application is configured through environment variables defined in ConfigMaps and Secrets:

1. **Database Connection**:
   - `DATABASE_URL`: Connection string for PostgreSQL database

2. **Qdrant Connection**:
   - `QDRANT_URL`: URL to the Qdrant vector database
   - `QDRANT_API_KEY`: API key for Qdrant (stored in Secret)

3. **Application Settings**:
   - `LOG_LEVEL`: Log level (default: INFO for production)
   - `METRICS_ENABLED`: Enable/disable metrics collection
   - `MAX_TOKENS`: Token limit for responses
   - `ASYNC_WORKERS`: Number of async workers for processing

### Resource Management

Production deployments should specify appropriate resource requests and limits:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

Adjust based on your application's actual requirements through load testing.

## Monitoring and Alerting

### Setting up Monitoring

1. Deploy the monitoring stack:
   ```bash
   kubectl apply -k k8s/monitoring
   ```

2. Access Grafana dashboards:
   - Default credentials: admin/change-me-in-prod (change immediately!)
   - URL: https://grafana.your-domain.com (configure Ingress)

3. Configure alerting rules in Prometheus:
   - Edit `k8s/monitoring/prometheus-configmap.yaml` to add custom alerting rules
   - Apply the updated configuration:
     ```bash
     kubectl apply -f k8s/monitoring/prometheus-configmap.yaml
     ```

### Key Metrics to Monitor

- **Application Metrics**:
  - Request rate, error rate, and duration (RED method)
  - Memory usage and CPU utilization
  - Message throughput and processing time
  - Vector search performance

- **Database Metrics**:
  - Connection pool utilization
  - Query performance
  - Transaction volume

## Scaling

The application supports both vertical and horizontal scaling:

1. **Horizontal Pod Autoscaler** (HPA):
   ```bash
   kubectl apply -f k8s/overlays/prod/hpa.yaml
   ```

2. **Vertical Pod Autoscaler** (optional):
   - Install the VPA operator if needed
   - Apply VPA configuration

## High Availability

The production deployment is designed for high availability:

1. **Multiple Replicas**: At least 3 replicas for the application
2. **Pod Anti-Affinity**: Ensures pods are distributed across nodes
3. **Topology Spread Constraints**: Distributes workloads across zones
4. **PDBs (Pod Disruption Budgets)**: Ensures availability during maintenance

## Backup and Recovery

### Database Backup

1. **PostgreSQL**:
   - Schedule regular backups using a cronjob
   - Enable WAL archiving for point-in-time recovery
   - Store backups in a secure, durable location (e.g., object storage)

2. **Qdrant**:
   - Use Qdrant's snapshot feature for regular backups
   - Store snapshots in object storage

### Disaster Recovery

Document and test the disaster recovery procedure:

1. Restore PostgreSQL database from backup
2. Restore Qdrant database from snapshots
3. Redeploy application components
4. Verify data integrity and application functionality

## Maintenance Procedures

### Updates and Upgrades

1. **Application Updates**:
   - Use semantic versioning for releases
   - Test in staging before deploying to production
   - Use canary deployments for major updates

2. **Database Updates**:
   - Schedule maintenance windows for database updates
   - Use connection pooling to minimize impact

### Rollbacks

In case of deployment issues:

```bash
# Rollback to previous deployment
kubectl rollout undo deployment/prod-sequential-questioning -n sequential-questioning

# Rollback to specific revision
kubectl rollout undo deployment/prod-sequential-questioning -n sequential-questioning --to-revision=2
```

## Security Considerations

1. **Network Policies**:
   - Apply restrictive network policies to limit communication between components
   - Use Kubernetes NetworkPolicy objects

2. **Secret Management**:
   - Rotate secrets regularly
   - Consider using a vault solution for secret management

3. **RBAC**:
   - Apply principle of least privilege
   - Use service accounts with minimal permissions

## Troubleshooting

### Common Issues

1. **Pod startup failures**:
   ```bash
   kubectl describe pod <pod-name> -n sequential-questioning
   kubectl logs <pod-name> -n sequential-questioning
   ```

2. **Database connectivity issues**:
   - Check network policies
   - Verify secret configuration
   - Test database connection from a debug pod

3. **Performance issues**:
   - Check resource usage with Prometheus
   - Analyze logs for slow queries or operations
   - Consider adjusting resource allocations

## Support and Escalation

- **Level 1**: DevOps team (response time: 15 minutes)
- **Level 2**: Backend development team (response time: 30 minutes)
- **Level 3**: Database administration team (for database-specific issues)

Contact information:
- DevOps on-call: devops-oncall@example.com
- Slack channel: #sequential-questioning-support

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Operational Runbook](./operational_runbook.md)
- [Architecture Documentation](./architecture.md)
- [API Reference](./api_reference.md) 