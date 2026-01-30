from fastapi.testclient import TestClient
import app.main

client = TestClient(app)

def test_health_healthy():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}