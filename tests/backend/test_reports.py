"""
Tests for reports API endpoints (quarterly performance and monthly trends).
"""
import pytest


class TestReportsEndpoints:
    """Test suite for /api/reports/* endpoints, including global filter support."""

    def test_get_quarterly_reports(self, client):
        """Test getting all quarterly reports."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for quarter in data:
            for field in ("quarter", "total_orders", "total_revenue",
                          "delivered_orders", "avg_order_value", "fulfillment_rate"):
                assert field in quarter
            assert quarter["quarter"].startswith("Q")
            assert 0 <= quarter["fulfillment_rate"] <= 100

    def test_quarterly_reports_sorted_chronologically(self, client):
        """Test that quarters are ordered by year then quarter number."""
        data = client.get("/api/reports/quarterly").json()

        def sort_key(label):
            q, year = label[1:].split("-")
            return int(year), int(q)

        labels = [q["quarter"] for q in data]
        assert labels == sorted(labels, key=sort_key)

    def test_quarterly_totals_match_orders(self, client):
        """Test that quarterly order counts and revenue add up to the raw orders."""
        orders = client.get("/api/orders").json()
        data = client.get("/api/reports/quarterly").json()

        assert sum(q["total_orders"] for q in data) == len(orders)
        assert abs(sum(q["total_revenue"] for q in data)
                   - sum(o["total_value"] for o in orders)) < 1

    def test_quarterly_avg_order_value_calculation(self, client):
        """Test that average order value is revenue divided by order count."""
        for quarter in client.get("/api/reports/quarterly").json():
            expected = quarter["total_revenue"] / quarter["total_orders"]
            assert abs(quarter["avg_order_value"] - expected) < 0.01

    def test_get_monthly_trends(self, client):
        """Test getting monthly trends."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for month in data:
            assert "month" in month
            assert "order_count" in month
            assert "revenue" in month
            assert "delivered_count" in month
            assert len(month["month"]) == 7  # YYYY-MM

        months = [m["month"] for m in data]
        assert months == sorted(months)

    @pytest.mark.parametrize("endpoint", ["/api/reports/quarterly", "/api/reports/monthly-trends"])
    def test_reports_by_warehouse(self, client, endpoint):
        """Test that the warehouse filter narrows report data to that warehouse's orders."""
        all_data = client.get(endpoint).json()
        response = client.get(f"{endpoint}?warehouse=Tokyo")
        assert response.status_code == 200
        tokyo_data = response.json()

        count_key = "total_orders" if "quarterly" in endpoint else "order_count"
        tokyo_orders = client.get("/api/orders?warehouse=Tokyo").json()

        assert sum(r[count_key] for r in tokyo_data) == len(tokyo_orders)
        assert sum(r[count_key] for r in tokyo_data) < sum(r[count_key] for r in all_data)

    def test_monthly_trends_by_month(self, client):
        """Test that a month filter returns only that month."""
        data = client.get("/api/reports/monthly-trends?month=2025-01").json()
        assert [m["month"] for m in data] == ["2025-01"]

        orders = client.get("/api/orders?month=2025-01").json()
        assert data[0]["order_count"] == len(orders)

    def test_quarterly_reports_by_quarter(self, client):
        """Test that a quarter filter returns only that quarter."""
        data = client.get("/api/reports/quarterly?month=Q2-2025").json()
        assert [q["quarter"] for q in data] == ["Q2-2025"]

    def test_quarterly_reports_by_status(self, client):
        """Test that the status filter is applied (Delivered-only means 100% fulfillment)."""
        data = client.get("/api/reports/quarterly?status=Delivered").json()
        assert len(data) > 0
        for quarter in data:
            assert quarter["fulfillment_rate"] == 100.0

    def test_reports_multiple_filters(self, client):
        """Test combined warehouse, category and month filters."""
        params = "warehouse=London&category=Sensors&month=2025-03"
        orders = client.get(f"/api/orders?{params}").json()
        data = client.get(f"/api/reports/monthly-trends?{params}").json()

        assert sum(m["order_count"] for m in data) == len(orders)

    def test_reports_no_matches_returns_empty_list(self, client):
        """Test that filters matching nothing return an empty list, not an error."""
        for endpoint in ("/api/reports/quarterly", "/api/reports/monthly-trends"):
            response = client.get(f"{endpoint}?warehouse=Nowhere")
            assert response.status_code == 200
            assert response.json() == []
