from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_toggle_flips_health_state():
    # Toggle once -> unhealthy
    r1 = client.post("/toggle")
    assert r1.status_code == 200
    assert r1.json()["healthy"] is False

    # Health should now return 503
    health = client.get("/health")
    assert health.status_code == 503

    # Toggle again -> healthy
    r2 = client.post("/toggle")
    assert r2.json()["healthy"] is True