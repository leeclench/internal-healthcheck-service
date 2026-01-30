from fastapi.testclient import TestClient
import app.main

client = TestClient(app)

def test_metrics_endpoint_exposed():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"peer_up" in response.content