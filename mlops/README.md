# MLOPS README

Comprehensive MLOps infrastructure for the LLM Chatbot system with containerization, monitoring, logging, and observability.

## TABLE OF CONTENTS

- [1. Docker Infrastructure](#1-docker-infrastructure)
- [2. CI-CD Github Action](#2-ci-cd-github-action)
- [3. Infrastructure as Code (IaC)](#3-infrastructure-as-code-iac)
- [4. Kubernetes Deployment](#4-kubernetes-deployment)

---
## STRUCTURE 
```bash
mlops/
├── docker/                          # Docker Compose infrastructure
│   ├── docker-compose.yml           # Main services (backend, frontend, ELK, monitoring)
│   ├── docker-compose.prod.yml      # Production overrides
│   ├── .env                         # Environment variables
│   ├── .dockerignore                # Files to exclude from build context
│   │
│   ├── elk/                         # Elasticsearch Stack (ELK)
│   │   ├── elasticsearch/
│   │   │   ├── Dockerfile
│   │   │   ├── config/
│   │   │   │   └── elasticsearch.yml
│   │   │   └── .dockerignore
│   │   ├── kibana/
│   │   │   ├── Dockerfile
│   │   │   ├── config/
│   │   │   │   └── kibana.yml
│   │   │   └── .dockerignore
│   │   ├── filebeat/                # Log collection agent
│   │   │   ├── Dockerfile
│   │   │   ├── README.md
│   │   │   └── config/
│   │   │       └── filebeat.yml
│   │   └── setup/                   # ELK initialization
│   │       ├── Dockerfile
│   │       ├── entrypoint.sh
│   │       ├── helpers.sh
│   │       └── roles/
│   │           └── logstash_writer.json
│   │
│   ├── prometheus/                  # Prometheus metrics collection
│   │   ├── prometheus.yml           # Scrape configs
│   │   └── alert-rules.yml          # Alert rules
│   │
│   ├── grafana/                     # Grafana dashboards
│   │   ├── config/
│   │   │   ├── datasources.yaml     # Prometheus datasource config
│   │   │   └── dashboards.yaml      # Dashboard provisioning
│   │   └── dashboards/
│   │       └── chatbot-dashboard.json
│   │
│   ├── redis/                       # Redis cache
│   │   └── redis.conf               # Redis configuration
│   │
│   └── custom_jenkins/              # Jenkins CI/CD
│       └── Dockerfile               # Jenkins with custom plugins
│
├── iac/                             # Infrastructure as Code (Terraform)
│   ├── main.tf                      # Provider and module definitions
│   ├── variables.tf                 # Input variables
│   ├── outputs.tf                   # Output values
│   ├── terraform.tfvars             # Variable values
│   ├── terraform.tfstate            # Current state (local)
│   ├── terraform.tfstate.backup     # State backup
│   ├── .terraform.lock.hcl          # Dependency lock
│   ├── .terraform/                  # Downloaded providers and modules
│   │   ├── modules/
│   │   │   └── modules.json
│   │   └── providers/
│   │       └── registry.terraform.io/
│   │           ├── hashicorp/helm/
│   │           ├── hashicorp/kubernetes/
│   │           └── hashicorp/time/
│   │
│   └── modules/                     # Terraform modules
│       ├── ingress-nginx/           # Nginx Ingress Controller
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   ├── outputs.tf
│       │   ├── README.md
│       │   └── templates/
│       │       ├── ingress-app.yaml
│       │       ├── ingress-jaeger.yaml
│       │       └── ingress-phoenix.yaml
│       │
│       ├── monitoring/              # Prometheus & Grafana
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   ├── outputs.tf
│       │   └── monitoring-values.yaml
│       │
│       ├── logging/                 # ELK Stack
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       │
│       ├── jaeger/                  # Distributed Tracing
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   ├── outputs.tf
│       │   └── jaeger-values.yaml
│       │
│       └── phoenix/                 # Phoenix Observability
│           ├── main.tf
│           ├── variables.tf
│           └── outputs.tf
│
├── k8s/                             # Kubernetes configurations
│   ├── README.md                    # K8s deployment guide
│   ├── ingress-nginx.yaml           # Nginx Ingress setup
│   ├── monitoring-values.yaml       # Prometheus values override
│   │
│   └── charts/                      # Helm charts
│       ├── backend/                 # Backend service chart
│       │   ├── Chart.yaml           # Chart metadata
│       │   ├── values.yaml          # Default configuration
│       │   └── templates/
│       │       ├── deployment.yaml  # Pod deployment
│       │       ├── service.yaml     # Service definition
│       │       ├── configmap.yaml   # Configuration
│       │       ├── secret.yaml      # Secrets
│       │       ├── hpa.yaml         # Horizontal Pod Autoscaler
│       │       └── _helpers.tpl     # Template helpers
│       │
│       └── frontend/                # Frontend service chart
│           ├── Chart.yaml
│           ├── values.yaml
│           └── templates/
│               ├── deployment.yaml
│               ├── service.yaml
│               ├── configmap.yaml
│               └── _helpers.tpl
│
├── docs/                            # Documentation
│   └── troubleshooting.md           # Troubleshooting guide

```

**Key Directory Purposes:**

| Directory | Purpose |
|-----------|---------|
| `docker/` | Docker Compose setup for development/local testing |
| `iac/` | Terraform infrastructure code for cloud deployment |
| `k8s/` | Kubernetes manifests and Helm charts for production |
| `docs/` | Documentation and troubleshooting guides |


## 1. Docker Infrastructure

### 1.1 Overview

The Docker infrastructure provides a complete development and production environment with all required services containerized and orchestrated using Docker Compose.

**Key Services:**
- **Backend API** - FastAPI application
- **Frontend** - Streamlit web interface
- **Elasticsearch Stack (ELK)** - Logging and search
- **Prometheus & Grafana** - Metrics and monitoring
- **Redis** - Caching and session management
- **Neo4j** - Graph database
- **Jenkins** - CI/CD pipeline

### 1.2 Docker Services Configuration

#### Elasticsearch Stack (ELK)

**Purpose:** Centralized logging and full-text search on application logs

**Components:**
- **Elasticsearch:** Search engine and database for logs
  - Port: 9200
  - Data persistence via named volume
- **Kibana:** Visualization and analysis interface
  - Port: 5601
  - Access logs and create dashboards
- **Filebeat:** Log collection and shipping
  - Collects application logs from backend
  - Forwards to Elasticsearch
- **Setup Service:** Initialize indices and security

**Configuration:**
```yaml
# elasticsearch/config/elasticsearch.yml
- Cluster name: elastic
- Node name: es01
- Bootstrap memory lock enabled
- Discovery type: single-node
```

**Access:**
- Elasticsearch: `http://localhost:9200`
- Kibana: `http://localhost:5601`

#### Prometheus & Grafana

**Purpose:** Metrics collection, aggregation, and visualization

**Prometheus:**
- Port: 9090
- Scrapes metrics from backend at `/metrics` endpoint
- Retention: 15 days (configurable)
- Config: `prometheus/prometheus.yml`

**Grafana:**
- Port: 3000
- Default credentials: `admin` / `admin`
- Pre-configured datasources and dashboards
- Custom chatbot dashboard for API metrics

**Dashboards:**
```
/grafana/dashboards/chatbot-dashboard.json
- Request rate and latency
- Error rates and exceptions
- Tool execution metrics
- Token usage tracking
```

#### Redis

**Purpose:** High-performance caching and session management

- Port: 6379
- Configuration: `redis/redis.conf`
- Persistence: RDB snapshots and AOF
- Used for: Chat history, conversation memory, rate limiting
- Volume: `/var/lib/redis`

#### Jenkins

**Purpose:** CI/CD pipeline orchestration

- Port: 8080
- Custom Docker image with pre-configured plugins
- SSH access for remote build execution
- Jenkinsfile-based pipeline definitions

#### Neo4j Graph Database

**Purpose:** Hospital operational data and relationships

- Configured in separate docker-compose
- Port: 7687 (bolt), 7474 (browser)
- Data volume: Neo4j data persistence

### 1.3 Docker Compose Setup

**Main File:** `docker/docker-compose.yml`

**Quick Start:**
```bash
cd mlops/docker

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Remove volumes (cleanup)
docker-compose down -v
```

**Environment Configuration:**
```bash
# .env file contains:
ELASTIC_PASSWORD=changeme
KIBANA_PASSWORD=changeme
STACK_VERSION=8.5.0
REDIS_PASSWORD=your_password
```

### 1.5 Volumes & Persistence

| Service | Volume | Purpose |
|---------|--------|---------|
| Elasticsearch | `elasticsearch-data` | Index and document storage |
| Prometheus | `prometheus-data` | Metrics time-series data |
| Redis | `redis-data` | Cache and session persistence |
| Filebeat | (host mount) | Log collection from backend |

**Volume Management:**
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect elasticsearch-data

# Remove unused volumes
docker volume prune
```

### 1.6 Network Configuration

- **Network Name:** `mlops_network`
- **Driver:** bridge (default)
- **Service Discovery:** Services communicate by name (e.g., `elasticsearch:9200`)

**DNS Resolution:**
```
backend:8000
elasticsearch:9200
kibana:5601
prometheus:9090
grafana:3000
redis:6379
jenkins:8080
```

### 1.7 Common Commands

**Build Services:**
```bash
# Build all images
docker-compose build

# Rebuild specific service
docker-compose build --no-cache elasticsearch
```

**Monitoring:**
```bash
# Real-time logs
docker-compose logs -f [service_name]

# Get service status
docker-compose ps

# Execute command in container
docker-compose exec backend bash
```

**Troubleshooting:**
```bash
# Check network connectivity
docker-compose exec backend ping elasticsearch

# Verify port availability
docker-compose port [service_name]

# Inspect service configuration
docker-compose config
```

### 1.8 Environment Variables

**Backend Configuration:**
```
NEO4J_URI=bolt://neo4j:7687
ELASTICSEARCH_URL=http://elasticsearch:9200
REDIS_URL=redis://redis:6379/0
JAEGER_ENDPOINT=http://localhost:6831/api/traces
```

**ELK Stack:**
```
ELASTICSEARCH_PASSWORD=changeme
KIBANA_PASSWORD=changeme
LOGSTASH_INTERNAL_PASSWORD=changeme
```

### 1.9 Health Checks

Each service includes health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:9200/_cluster/health"]
  interval: 30s
  timeout: 10s
  retries: 5
```

**Monitor Health:**
```bash
docker-compose ps  # Shows health status
```

### 1.10 Scaling & Performance

**Resource Limits:**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

**Scaling Replicas:**
```bash
# Scale backend service to 3 replicas (Docker Swarm/Kubernetes)
docker-compose up -d --scale backend=3
```

### 1.11 Development vs Production

**Development:**
```bash
docker-compose -f docker-compose.yml up
```

**Production:**
```bash
docker-compose -f docker-compose.yml \
               -f docker-compose.prod.yml up -d
```

**Production Overrides** (docker-compose.prod.yml):
- Removed ports for non-public services
- Increased resource limits
- Health check strictness
- Log rotation policies

---

## 2. CI/CD with GitHub Actions

### 2.1 Overview

GitHub Actions provides automated CI/CD pipelines for continuous integration, testing, building, and deployment. The workflow automatically triggers on code push, pull requests, and scheduled events.

**Key Features:**
- Automated testing on every commit
- Code quality checks and linting
- Docker image building and pushing
- Automated deployment to staging/production
- Slack notifications for build status

### 2.2 Workflow Structure

**Workflow File Location:** `.github/workflows/`

**Main Workflows:**
- `test.yaml` - Unit tests and integration tests
- `build.yaml` - Docker image build and push
- `deploy.yaml` - Deployment to Kubernetes
- `quality.yaml` - Code quality and security checks

### 2.3 Test Workflow

**Trigger Events:**
```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

**Test Pipeline:**
```
1. Checkout code
   ↓
2. Setup Python environment
   ↓
3. Install dependencies
   ↓
4. Run linting (flake8, black)
   ↓
5. Run unit tests (pytest)
   ↓
6. Run integration tests
   ↓
7. Generate coverage report
   ↓
8. Upload to Codecov
```

**Sample Test Job:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      elasticsearch:
        image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
        env:
          ELASTIC_PASSWORD: ${{ secrets.ELASTIC_PASSWORD }}
      redis:
        image: redis:7
        
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests
        run: pytest backend/tests --cov=backend
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### 2.4 Build & Push Workflow

**Trigger:** On successful test completion

**Build Pipeline:**
```
1. Checkout code
   ↓
2. Login to Docker Registry
   ↓
3. Build Docker images
   - Backend
   - Frontend
   ↓
4. Push to Docker Hub / ECR
   ↓
5. Update image tags
   ↓
6. Notify Slack
```

**Docker Build Job:**
```yaml
jobs:
  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push backend
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: |
            ${{ secrets.DOCKER_REGISTRY }}/backend:latest
            ${{ secrets.DOCKER_REGISTRY }}/backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Build and push frontend
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ secrets.DOCKER_REGISTRY }}/frontend:latest
            ${{ secrets.DOCKER_REGISTRY }}/frontend:${{ github.sha }}
```

### 2.5 Deploy Workflow

**Trigger:** Manual dispatch or on push to main branch

**Deployment Pipeline:**
```
1. Checkout code
   ↓
2. Configure Kubernetes
   ↓
3. Update image tags in manifests
   ↓
4. Apply Kubernetes manifests
   ↓
5. Wait for rollout
   ↓
6. Run smoke tests
   ↓
7. Notify Slack
```

**Deploy Job:**
```yaml
jobs:
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure kubectl
        run: |
          mkdir -p $HOME/.kube
          echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > $HOME/.kube/config
          chmod 600 $HOME/.kube/config
      
      - name: Update deployment image
        run: |
          kubectl set image deployment/backend \
            backend=${{ secrets.DOCKER_REGISTRY }}/backend:${{ github.sha }} \
            -n production
      
      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/backend \
            -n production --timeout=5m
      
      - name: Run smoke tests
        run: |
          python tests/smoke_tests.py
      
      - name: Notify Slack
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployment ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 2.6 Code Quality Workflow

**Tools:**
- **Linting:** flake8, black
- **Type checking:** mypy
- **Security:** bandit, safety
- **Documentation:** docstring checks

**Quality Job:**
```yaml
jobs:
  quality:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install tools
        run: |
          pip install flake8 black mypy bandit safety
      
      - name: Lint with flake8
        run: flake8 backend --count --select=E9,F63,F7,F82 --show-source
      
      - name: Format check with black
        run: black --check backend
      
      - name: Type check with mypy
        run: mypy backend --ignore-missing-imports
      
      - name: Security check with bandit
        run: bandit -r backend -f json -o bandit-report.json
```

### 2.7 Secrets Management

**Required GitHub Secrets:**
```
DOCKER_USERNAME          # Docker Hub username
DOCKER_PASSWORD          # Docker Hub token
DOCKER_REGISTRY          # Docker registry URL
KUBE_CONFIG              # Kubernetes config (base64 encoded)
SLACK_WEBHOOK            # Slack webhook for notifications
ELASTIC_PASSWORD         # Elasticsearch password
REDIS_PASSWORD           # Redis password
```

**Setting Secrets:**
```bash
# GitHub CLI
gh secret set DOCKER_USERNAME -b "your_username"

# Or via GitHub UI: Settings → Secrets and variables → Actions
```

### 2.8 Workflow Status & Monitoring

**Viewing Runs:**
- GitHub UI: `Actions` tab shows all workflow runs
- Status badge in README:
```markdown
[![Tests](https://github.com/user/repo/actions/workflows/test.yaml/badge.svg)](https://github.com/user/repo/actions)
```

**Notifications:**
- Email on workflow failure
- Slack channel notifications (via webhook)
- Pull request comments with status

### 2.9 Matrix Testing

**Test Multiple Configurations:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
        elasticsearch-version: ['8.5.0', '8.6.0']
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      # ... rest of steps
```

### 2.10 Performance Optimization

**Caching:**
```yaml
- name: Cache pip packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

**Conditional Steps:**
```yaml
- name: Deploy only on main
  if: github.ref == 'refs/heads/main'
  run: kubectl apply -f k8s/
```

### 2.11 Troubleshooting

**Common Issues:**

| Issue | Solution |
|-------|----------|
| Docker push fails | Check Docker credentials in secrets |
| Kubernetes deploy fails | Verify kubeconfig and permissions |
| Tests timeout | Increase timeout or optimize tests |
| Missing dependencies | Update requirements.txt and cache |
| Slack notification fails | Check webhook URL format |

### 2.12 Workflow Best Practices

- ✅ Keep workflows DRY using reusable workflows
- ✅ Use job dependencies (`needs:`) for ordering
- ✅ Cache dependencies to speed up runs
- ✅ Run tests before building images
- ✅ Use branch protection rules to enforce checks
- ✅ Monitor workflow run times and optimize
- ✅ Add meaningful commit messages for tracking
- ✅ Use concurrency to prevent duplicate runs

### 2.13 Scheduling Workflows

**Nightly Tests:**
```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
```

**Weekly Dependency Updates:**
```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Sunday midnight
```

---

## 3. Infrastructure as Code (IaC)

### 3.1 Overview

Infrastructure as Code (IaC) using Terraform enables version-controlled, reproducible infrastructure deployment on cloud platforms (AWS, GCP, Azure).

**Benefits:**
- Infrastructure documented in code
- Version control and code review
- Reproducible environments
- Easy scaling and modifications
- Disaster recovery and automation

### 3.2 Terraform Structure

**Directory Layout:**
```
mlops/iac/
├── main.tf                 # Main infrastructure definition
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── terraform.tfvars        # Variable values
├── terraform.tfstate       # State file (version controlled)
└── modules/                # Reusable modules
    ├── ingress-nginx/      # Ingress controller
    ├── monitoring/         # Prometheus & Grafana
    ├── logging/            # ELK stack
    ├── jaeger/             # Distributed tracing
    └── phoenix/            # Phoenix observability
```

### 3.3 Core Terraform Files

**main.tf - Provider Configuration:**
```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.38"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.17"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}
```

**variables.tf - Input Configuration:**
```hcl
variable "kubeconfig_path" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "enable_monitoring" {
  description = "Enable Prometheus and Grafana"
  type        = bool
  default     = true
}

variable "enable_jaeger" {
  description = "Enable distributed tracing"
  type        = bool
  default     = true
}
```

**terraform.tfvars - Variable Values:**
```hcl
kubeconfig_path     = "~/.kube/config"
namespace           = "production"
enable_monitoring   = true
enable_jaeger       = true
```

### 3.4 Terraform Modules

**Module: Monitoring**
```hcl
module "monitoring" {
  source = "./modules/monitoring"
  
  namespace           = var.namespace
  enable_monitoring   = var.enable_monitoring
  prometheus_storage  = "10Gi"
  grafana_admin_pass  = var.grafana_password
  
  dashboards = {
    chatbot = file("${path.module}/dashboards/chatbot-dashboard.json")
  }
}
```

**Module: Ingress-Nginx**
```hcl
module "ingress_nginx" {
  source = "./modules/ingress-nginx"
  
  namespace          = var.namespace
  ingress_class      = "nginx"
  replicas           = 3
  enable_metrics     = true
  
  # TLS configuration
  cert_issuer        = "letsencrypt-prod"
}
```

**Module: Jaeger Tracing**
```hcl
module "jaeger" {
  source = "./modules/jaeger"
  
  namespace     = var.namespace
  storage_type  = "elasticsearch"
  retention_days = 7
  
  elasticsearch_url = module.logging.elasticsearch_url
}
```

**Module: Logging**
```hcl
module "logging" {
  source = "./modules/logging"
  
  namespace       = var.namespace
  elasticsearch_version = "8.5.0"
  kibana_enabled  = true
  storage_size    = "20Gi"
  retention_days  = 30
}
```

### 3.5 Terraform Commands

**Initialize Terraform:**
```bash
cd mlops/iac
terraform init
```

**Plan Infrastructure:**
```bash
terraform plan -out=tfplan
```

**Apply Configuration:**
```bash
terraform apply tfplan
```

**Destroy Infrastructure:**
```bash
terraform destroy -auto-approve
```

**View State:**
```bash
terraform show
terraform state list
```

### 3.6 State Management

**State File Configuration:**
```hcl
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
```

**Remote State (S3):**
```hcl
terraform {
  backend "s3" {
    bucket         = "chatbot-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}
```

### 3.7 Best Practices

- ✅ Keep tfstate in version control (for dev)
- ✅ Use remote state for production
- ✅ Enable state locking with DynamoDB
- ✅ Encrypt sensitive values
- ✅ Use modules for code reuse
- ✅ Plan before applying
- ✅ Tag resources for cost tracking
- ✅ Document variable purposes

---

## 4. Kubernetes Deployment

### 4.1 Overview

Kubernetes orchestrates containerized applications with automated deployment, scaling, and management. The system uses Helm charts for templated deployments.

**Kubernetes Architecture:**
```
┌─────────────────────────────────────────────────┐
│              Kubernetes Cluster                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  Ingress (Nginx)                                │
│  ├── example.com → backend service              │
│  ├── grafana.example.com → grafana              │
│  └── jaeger.example.com → jaeger UI             │
│                                                 │
│  Services:                                      │
│  ├── Backend (Deployment: 3 replicas)           │
│  ├── Frontend (Deployment: 2 replicas)          │
│  ├── Redis (StatefulSet)                        │
│  ├── Elasticsearch (StatefulSet)                │
│  └── Prometheus (StatefulSet)                   │
│                                                 │
│  ConfigMaps & Secrets (Configuration)           │
│  HPA (Auto-scaling)                             │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 4.2 Helm Charts Structure

**Backend Chart:**
```
mlops/k8s/charts/backend/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default configuration
├── templates/
│   ├── deployment.yaml     # Pod deployment
│   ├── service.yaml        # Service definition
│   ├── configmap.yaml      # Configuration
│   ├── secret.yaml         # Secrets
│   ├── hpa.yaml            # Auto-scaling
│   └── _helpers.tpl        # Templates
```

### 4.3 Helm Values Configuration

**Backend values.yaml:**
```yaml
replicaCount: 3

image:
  repository: myregistry/backend
  tag: "1.0.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8000
  targetPort: 8000

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

env:
  NEO4J_URI: "bolt://neo4j:7687"
  ELASTICSEARCH_URL: "http://elasticsearch:9200"
  REDIS_URL: "redis://redis:6379/0"

livenessProbe:
  httpGet:
    path: /health/liveness
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/readiness
    port: 8000
  initialDelaySeconds: 20
  periodSeconds: 5
```

### 4.4 Kubernetes Manifests

**Direct Manifests (Non-Helm):**
```bash
mlops/k8s/
├── ingress-nginx.yaml      # Ingress controller setup
├── monitoring-values.yaml  # Prometheus setup
```

### 4.5 Deployment Commands

**Install Helm Charts:**
```bash
# Install backend
helm install backend ./k8s/charts/backend \
  -n production --create-namespace

# Install frontend
helm install frontend ./k8s/charts/frontend \
  -n production

# List releases
helm list -n production

# Upgrade release
helm upgrade backend ./k8s/charts/backend \
  -n production --values custom-values.yaml
```

**Apply Kubernetes Manifests:**
```bash
# Apply ingress
kubectl apply -f mlops/k8s/ingress-nginx.yaml

# Port forward to access locally
kubectl port-forward svc/backend 8000:8000 -n production
```

### 4.6 Namespace & RBAC

**Create Namespace:**
```bash
kubectl create namespace production
kubectl label namespace production environment=prod
```

**RBAC Service Account:**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backend-sa
  namespace: production

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: backend-role
  namespace: production
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: backend-rolebinding
  namespace: production
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: backend-role
subjects:
- kind: ServiceAccount
  name: backend-sa
  namespace: production
```

### 4.7 Monitoring & Logging

**Prometheus ServiceMonitor:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-monitor
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: metrics
    interval: 30s
```

**View Logs:**
```bash
# Stream logs from pod
kubectl logs -f deployment/backend -n production

# Previous pod logs (after crash)
kubectl logs deployment/backend -n production --previous

# Logs from all backend pods
kubectl logs -l app=backend -n production --all-containers=true
```

### 4.8 Auto-Scaling (HPA)

**Horizontal Pod Autoscaler:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 85
```

### 4.9 Network Policies

**Restrict Traffic:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
```

### 4.10 Troubleshooting

**Common Issues & Fixes:**

| Issue | Command | Fix |
|-------|---------|-----|
| Pod stuck pending | `kubectl describe pod <pod>` | Check resource requests/limits |
| Service unreachable | `kubectl get endpoints` | Verify pod selector matches labels |
| High memory usage | `kubectl top pods` | Increase memory limit, optimize app |
| Image pull errors | `kubectl describe pod` | Check registry credentials |
| Deployment not updating | `kubectl rollout status` | Check image tag, push new image |

### 4.11 Best Practices

- ✅ Set resource requests and limits
- ✅ Use health checks (liveness, readiness)
- ✅ Implement graceful shutdown
- ✅ Use secrets for sensitive data
- ✅ Enable pod autoscaling
- ✅ Use network policies for security
- ✅ Monitor metrics and logs
- ✅ Regular backup of PersistentVolumes
- ✅ Use rolling updates for zero downtime

### 4.12 Useful kubectl Commands

**Cluster Information:**
```bash
kubectl cluster-info
kubectl get nodes
kubectl describe node <node-name>
```

**Deployments:**
```bash
kubectl get deployments -n production
kubectl rollout history deployment/backend -n production
kubectl rollout undo deployment/backend -n production
```

**Debugging:**
```bash
kubectl exec -it pod/backend-xxx -n production -- bash
kubectl cp production/backend-xxx:/logs ./logs
```




