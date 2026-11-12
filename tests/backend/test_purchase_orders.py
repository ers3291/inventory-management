"""
Tests for purchase order API endpoints.
"""
from datetime import date, timedelta

import pytest

import mock_data


@pytest.fixture(autouse=True)
def reset_purchase_orders():
    """Clear the in-memory purchase orders around each test.

    Created POs are appended to a module-level list shared by the whole app,
    so without this they would leak between tests and trigger 409 conflicts.
    """
    mock_data.purchase_orders.clear()
    yield
    mock_data.purchase_orders.clear()


@pytest.fixture
def po_request():
    """Valid create-PO payload for backlog item 1."""
    return {
        "backlog_item_id": "1",
        "supplier_name": "Acme Supply Co",
        "quantity": 350,
        "unit_cost": 8.25,
        "expected_delivery_date": (date.today() + timedelta(days=14)).isoformat(),
        "notes": "Rush order",
    }


class TestPurchaseOrderEndpoints:
    """Test suite for purchase-order-related endpoints."""

    def test_create_purchase_order(self, client, po_request):
        """Test creating a purchase order returns the stored PO."""
        response = client.post("/api/purchase-orders", json=po_request)
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == "1"
        assert po["supplier_name"] == "Acme Supply Co"
        assert po["quantity"] == 350
        assert abs(po["unit_cost"] - 8.25) < 0.01
        assert po["status"] == "Pending"
        assert po["created_date"]
        assert po["notes"] == "Rush order"

    def test_get_purchase_order_by_backlog_item(self, client, po_request):
        """Test fetching a created PO by its backlog item ID."""
        created = client.post("/api/purchase-orders", json=po_request).json()

        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_nonexistent_purchase_order(self, client):
        """Test getting a PO for a backlog item that has none."""
        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_backlog_reflects_created_purchase_order(self, client, po_request):
        """Test that backlog items expose the PO flag and ID after creation."""
        before = {i["id"]: i for i in client.get("/api/backlog").json()}
        assert before["1"]["has_purchase_order"] is False
        assert before["1"]["purchase_order_id"] is None

        created = client.post("/api/purchase-orders", json=po_request).json()

        after = {i["id"]: i for i in client.get("/api/backlog").json()}
        assert after["1"]["has_purchase_order"] is True
        assert after["1"]["purchase_order_id"] == created["id"]
        # Other backlog items are unaffected
        assert after["2"]["purchase_order_id"] is None

    def test_create_duplicate_purchase_order(self, client, po_request):
        """Test that a second PO for the same backlog item is rejected."""
        assert client.post("/api/purchase-orders", json=po_request).status_code == 201

        response = client.post("/api/purchase-orders", json=po_request)
        assert response.status_code == 409

    def test_create_purchase_order_unknown_backlog_item(self, client, po_request):
        """Test creating a PO for a backlog item that doesn't exist."""
        response = client.post(
            "/api/purchase-orders", json={**po_request, "backlog_item_id": "nonexistent-999"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "field,value",
        [
            ("quantity", 0),
            ("quantity", -5),
            ("quantity", 1_000_001),
            ("unit_cost", -1.0),
            ("unit_cost", 1_000_001.0),
            ("supplier_name", "   "),
            ("supplier_name", "x" * 201),
            ("notes", "x" * 2001),
            ("expected_delivery_date", "next tuesday"),
            ("expected_delivery_date", "2020-01-01"),
        ],
    )
    def test_create_purchase_order_invalid_values(self, client, po_request, field, value):
        """Test that invalid business values are rejected with 400."""
        response = client.post("/api/purchase-orders", json={**po_request, field: value})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_purchase_order_missing_field(self, client, po_request):
        """Test that a missing required field fails Pydantic validation."""
        payload = {k: v for k, v in po_request.items() if k != "supplier_name"}
        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 422

    def test_invalid_body_reported_before_conflict(self, client, po_request):
        """Test that validation errors win over the duplicate-PO conflict."""
        assert client.post("/api/purchase-orders", json=po_request).status_code == 201

        response = client.post("/api/purchase-orders", json={**po_request, "quantity": 0})
        assert response.status_code == 400

    def test_create_purchase_order_strips_and_normalizes(self, client, po_request):
        """Test that supplier and notes are trimmed and blank notes become null."""
        response = client.post(
            "/api/purchase-orders",
            json={**po_request, "supplier_name": "  Acme  ", "notes": "   "},
        )
        assert response.status_code == 201
        po = response.json()
        assert po["supplier_name"] == "Acme"
        assert po["notes"] is None

    def test_concurrent_creates_make_one_purchase_order(self, client, po_request):
        """Test that simultaneous requests for one backlog item create exactly one PO."""
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=8) as pool:
            codes = list(pool.map(lambda _: client.post("/api/purchase-orders", json=po_request).status_code, range(8)))

        assert codes.count(201) == 1
        assert codes.count(409) == 7
        assert len([po for po in mock_data.purchase_orders if po["backlog_item_id"] == "1"]) == 1

    @pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
    def test_create_purchase_order_non_finite_unit_cost(self, client, po_request, literal):
        """Test that NaN/Infinity unit costs are rejected.

        Python's JSON parser accepts these non-standard literals, so they must be checked
        explicitly. They're sent as raw text because httpx refuses to encode them.
        """
        import json

        body = json.dumps({**po_request, "unit_cost": 0}).replace('"unit_cost": 0', f'"unit_cost": {literal}')
        response = client.post(
            "/api/purchase-orders", content=body, headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        assert mock_data.purchase_orders == []
