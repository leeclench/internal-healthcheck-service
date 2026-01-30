import os
import time
import threading
import signal
import sys
import requests
import logging
from fastapi import FastAPI, Response
from prometheus_client import Counter, Gauge, generate_latest


# -----------------
# Configuration
# -----------------
PEER_URL = os.getenv("PEER_URL", "http://localhost:8080/health")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "5"))


# -----------------
# Logging
# -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s level=%(levelname)s msg=%(message)s"
)
logger = logging.getLogger("healthcheck")


# -----------------
# Metrics
# -----------------
peer_up = Gauge("peer_up", "Peer health status (1=up, 0=down)")
peer_check_errors = Counter("peer_check_errors_total", "Errors contacting peer")


# -----------------
# App State
# -----------------
app = FastAPI()
healthy = True
running = True

# -----------------
# Graceful Shutdown
# -----------------
def shutdown_handler(signum, frame):
    global running
    logger.info("shutdown signal received")
    running = False
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# -----------------
# Background Peer Check
# -----------------
def peer_check_loop():
    while running:
        try:
            r = requests.get(PEER_URL, timeout=2)
            if r.status_code == 200:
                peer_up.set(1)
                logger.info("peer healthy")
            else:
                peer_up.set(0)
                logger.warning("peer unhealthy status=%s", r.status_code)
        except Exception as e:
            peer_up.set(0)
            peer_check_errors.inc()
            logger.error("peer check failed error=%s", e)
        time.sleep(CHECK_INTERVAL)

threading.Thread(target=peer_check_loop, daemon=True).start()

# -----------------
# HTTP Endpoints
# -----------------
@app.get("/health")
def health(response: Response):
    if healthy:
        return {"status": "ok"}
    response.status_code = 503
    return {"status": "unhealthy"}

# Toggle health state for demo/testing.
@app.post("/toggle")
def toggle():
    global healthy
    healthy = not healthy
    logger.info("local health toggled=%s", healthy)
    return {"healthy": healthy}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")