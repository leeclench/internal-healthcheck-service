# internal-healthcheck-service
This is an MVP internal health-check microservice that can periodically perform HTTP health checks on another application (peer node), uses configurable env variables, exposes a /health endpoint for self-checking, includes configurable logging, can simulate up/down states for testing mutual checks, supports scalable deployment via DC/K8s
