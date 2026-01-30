# internal-healthcheck-service MVP
This repository contains a MVP for a lightweight FastAPI-based internal health-check service that is designed for early-stage platform teams.

The solution intentionally demonstrates:
- Cloud-native configuration
- Operational clarity
- Observability-first design
- Explicit tradeoff documention
- Clear growth paths toward production grade reliability alerting and scale

## Architecture Overview
- Language: Python 3.12
- Framework: FastAPI (lightweight, async-friendly, production-ready)
- Execution model:
  - One HTTP server per instance
  - Background peer-check loop
  - Logs and metrics are emitted for centralized continuous observability
- Target runtimes:
  - Docker (local / VMs)
  - AWS ECS
  - Kubernetes

## Project structure
```
internal-healthcheck-service/
├── app/
│ └── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── k8s/
│ ├── deployment.yaml
│ ├── service.yaml
│ └── servicemonitor.yaml
└── README.md
```

## How to run locally
### Prerequisites
- Python 3.12+
- Docker (optional but recommended)

### First step
Clone this repository
```
git clone https://github.com/leeclench/internal-healthcheck-service.git
cd internal-healthcheck-service
```

### Run locally without Docker
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PEER_URL=http://localhost:8080/health
export CHECK_INTERVAL=5

uvicorn app.main:app --host 0.0.0.0 --port 8080
```
### Run two instances locally
Terminal 1:
```
export PEER_URL=http://localhost:8081/health
uvicorn app.main:app --port 8080
```
Terminal 2:
```
export PEER_URL=http://localhost:8080/health
uvicorn app.main:app --port 8081
```

### Run with Docker Compose (the recommended option)
```
docker compose up --build
```

Test the health check services
```
# Access service A
curl http://localhost:8001/health
# Access service B
curl http://localhost:8002/health
# Toggle service A’s health
curl -X POST http://localhost:8001/toggle
``` 

### Kubernetes and Prometheus example
In Kubernetes, the `ServiceMonitor` resource tells Prometheus where and how to scrape metrics:
```
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: healthcheck
spec:
  selector:
  matchLabels:
    app: healthcheck
  endpoints:
  - path: /metrics
    port: http
    interval: 15s
```
Prometheus automatically discovers the service and begins scraping `/metrics`.

**Why this matters?**
- Applications do **not** send alerts
- Applications emit **telemetry**
- Alerting logic evolves independently of deployments
This keeps alerting flexible, auditable, and SLO-driven.

### Prometheus alterting examples
```
groups:
- name: healthcheck-alerts
  rules:
  - alert: PeerDown
    expr: peer_up == 0
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "Peer service unavailable"

  - alert: PeerCheckErrorsHigh
    expr: rate(peer_check_errors_total[5m]) > 0
    for: 2m
    labels:
      severity: critical
```

### Metrics endpoint usage
The `/metrics` endpoint exposes **Prometheus-formatted metrics**. It is *not* intended for human use and should never be polled by application code.
Instead, it is consumed by a metrics collector such as:
- Prometheus
- AWS Managed Prometheus
- Grafana Agent
- OpenTelemetry Collector (Prometheus receiver)
Prometheus periodically **scrapes** this endpoint and stores time-series data.

### How metrics flow through the system
1. Application exposes `/metrics`
2. Prometheus scrapes `/metrics` every N seconds
3. Metrics are stored as time-series
4. Alert rules evaluate those time-series
5. Alertmanager routes notifications (Slack, PagerDuty, Opsgenie, etc.)

This decoupling is intentional:
- The app emits *signals*
- The platform decides *what matters*

### Metrics exposed
| Metric                    | Type    | Description                                  |
| ------                    | ------  | ------                                       |
| `peer_up`                 | Gauge   | `1` when peer is healthy, `0` when unhealthy |
| `peer_check_errors_total` | Counter | Total errors when attempting to contact peer |

### Configuration Options

All configuration is environment-variable based.

| Variable            | Required | Description                                        | Default                        |
| -------             | -------- | -------                                            | -------                        |
| `PEER_URL`          | Yes      | URL of peer instance health endpoint               | `http://localhost:8080/health` |
| `CHECK_INTERVAL`    | No       | Interval between peer health checks (seconds)      | `5`                            |
| `LOG_LEVEL`         | No       | Logging verbosity (future extension)               | `INFO`                         |
| `REQUEST_TIMEOUT`   | No       | Peer request timeout in seconds (future extension) | `8000`                         |

**Why environment variables?**
- Works across VMs, containers, ECS and Kubernetes
- No baked-in config files
- Safe to override per-environment

### Design notes and future considerations
**Service Level Objectives (SLOs) & error budgets**
- Should aim to have SLO availability be around 99.9%
- The error budget should drive the alert sensitivity
- Alerts should fire on the overall error budget burn rather than on single failures.
**Leader election vs mesh checking**
- Current design uses mesh-style peer checks
- At scale, replace with:
  - Leader election (using something like the kubernetes lease API)
  - Centralized probing
**Threat model considerations**
- `/toggle` endpoint must be protected in production
- There is potential Server-Side Request Forgery (SSRF) risk if `PEER_URL` is user-controlled
- Recommended actions:
  - Implement or adapt NetworkPolicy restrictions for input validation
  - Enhance AuthN/Z via the use of RBAC/ABAC/IAM policies
**Graceful shutdown**
- SIGTERM handling for rolling deploys
- Prevents false alerts during pod termination
**Tracing (possible areas for future considerations)**
- Implement OpenTelemetry spans around peer checks
- Correlate failures across services