from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "OpenMail Verify" in data["service"]

def test_verify_endpoint_valid():
    response = client.post("/api/v1/verify", json={"email": "contact@gmail.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "contact@gmail.com"
    assert data["domain"] == "gmail.com"
    assert "checks" in data
    assert "score" in data
    assert "status" in data
    assert data["checks"]["syntax"]["passed"] is True

def test_verify_endpoint_invalid_syntax():
    response = client.post("/api/v1/verify", json={"email": "not-an-email"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INVALID"
    assert data["checks"]["syntax"]["passed"] is False

def test_batch_verify_endpoint():
    payload = {
        "emails": [
            "valid.user@gmail.com",
            "support@gmail.com",
            "invalid-email-format"
        ]
    }
    response = client.post("/api/v1/verify/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["results"]) == 3
    assert "average_score" in data

def test_history_and_stats_endpoints():
    # Verify an email to ensure data exists
    client.post("/api/v1/verify", json={"email": "tester@gmail.com"})
    
    # Get stats
    stats_res = client.get("/api/v1/stats")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["total_verified"] >= 1

    # Get history
    hist_res = client.get("/api/v1/history?page=1&page_size=10")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["total"] >= 1
    assert len(hist_data["items"]) >= 1

def test_clear_history_endpoint():
    del_res = client.delete("/api/v1/history")
    assert del_res.status_code == 200
    data = del_res.json()
    assert "deleted" in data

    # Verify history is now 0
    stats_res = client.get("/api/v1/stats")
    assert stats_res.json()["total_verified"] == 0
