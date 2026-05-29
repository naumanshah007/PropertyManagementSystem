from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.demo_data import WORKUP_ID
from app.main import app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_demo_workup_endpoint() -> None:
    response = client.get(f"/workups/{WORKUP_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["client_name"] == "Tauraroa Area School"
    assert data["survey_type"] == "Asbestos Demolition Survey"
    assert data["export_status"] == "blocked"


def test_demo_register_items_include_review_required_risks() -> None:
    response = client.get(f"/workups/{WORKUP_ID}/register-items")
    assert response.status_code == 200
    items = response.json()
    assert any(item["friability_class"] == "Class A" and item["review_status"] == "review_required" for item in items)
    assert any(item["access_status"] == "No Access" and item["review_status"] == "review_required" for item in items)


def test_demo_quote_lines_all_have_evidence() -> None:
    response = client.get(f"/workups/{WORKUP_ID}/quote-lines")
    assert response.status_code == 200
    lines = response.json()
    assert len(lines) >= 5
    assert all(line["source_evidence_ids"] for line in lines)
    assert any(line["review_status"] == "review_required" for line in lines)
    for line in lines:
        if line["base_cost"] is not None:
            ex_gst = line["base_cost"] * line["risk_multiplier"] * (1 + line["margin"])
            assert line["gst"] == round(ex_gst * 0.15, 2)
            assert line["total"] == round(ex_gst + line["gst"], 2)


def test_demo_audit_events_endpoint() -> None:
    response = client.get(f"/workups/{WORKUP_ID}/audit-events")
    assert response.status_code == 200
    events = response.json()
    assert any(event["event_type"] == "extraction.generated" for event in events)
