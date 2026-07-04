from fastapi.testclient import TestClient

from app.main import app


def test_ticket_workflow():
    with TestClient(app) as client:
        r = client.post(
            "/tickets",
            json={"subject": "Refund request", "body": "I need a refund for my last invoice"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["category"] == "billing"
        assert data["draft_response"]

        r2 = client.get(f"/tickets/{data['id']}")
        assert r2.status_code == 200
        assert len(r2.json()["audit_trail"]) >= 4


def test_low_confidence_requires_approval():
    with TestClient(app) as client:
        r = client.post(
            "/tickets",
            json={"subject": "Hello", "body": "Just saying hi"},
        )
        assert r.json()["status"] == "pending_approval"
        tid = r.json()["id"]
        r2 = client.post(f"/tickets/{tid}/approval", json={"action": "approve"})
        assert r2.json()["status"] == "approved"
