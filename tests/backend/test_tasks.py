"""
Tests for task API endpoints.
"""
from datetime import date, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def reset_tasks():
    """Clear in-memory tasks around each test.

    Tasks live in a module-level list in main.py, so without this they would
    leak between tests.
    """
    main.tasks.clear()
    yield
    main.tasks.clear()


@pytest.fixture
def task_request():
    """Valid create-task payload, shaped like the one TasksModal sends."""
    return {
        "title": "Review Q4 inventory",
        "priority": "high",
        "dueDate": (date.today() + timedelta(days=7)).isoformat(),
    }


class TestTaskEndpoints:
    """Test suite for task-related endpoints."""

    def test_get_tasks_empty(self, client):
        """Test that no API tasks exist initially."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client, task_request):
        """Test creating a task returns it as pending."""
        response = client.post("/api/tasks", json=task_request)
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Review Q4 inventory"
        assert task["priority"] == "high"
        assert task["dueDate"] == task_request["dueDate"]
        assert task["status"] == "pending"
        # IDs must not collide with the client's built-in mock tasks (1-4)
        assert task["id"] >= 1000

    def test_created_task_is_listed_newest_first(self, client, task_request):
        """Test that created tasks appear in GET, newest first."""
        first = client.post("/api/tasks", json=task_request).json()
        second = client.post("/api/tasks", json={**task_request, "title": "Second"}).json()

        data = client.get("/api/tasks").json()
        assert [t["id"] for t in data] == [second["id"], first["id"]]

    def test_toggle_task(self, client, task_request):
        """Test that PATCH flips status pending -> completed -> pending."""
        task_id = client.post("/api/tasks", json=task_request).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_delete_task(self, client, task_request):
        """Test deleting a task removes it."""
        task_id = client.post("/api/tasks", json=task_request).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_deleted_task_id_is_not_reused(self, client, task_request):
        """Test that IDs keep increasing after the newest task is deleted."""
        task_id = client.post("/api/tasks", json=task_request).json()["id"]
        client.delete(f"/api/tasks/{task_id}")

        new_id = client.post("/api/tasks", json=task_request).json()["id"]
        assert new_id > task_id

    @pytest.mark.parametrize("method", ["patch", "delete"])
    def test_nonexistent_task(self, client, method):
        """Test toggling or deleting a task that doesn't exist."""
        response = getattr(client, method)("/api/tasks/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "field,value",
        [
            ("title", "   "),
            ("title", "x" * 201),
            ("priority", "urgent"),
            ("dueDate", "tomorrow"),
        ],
    )
    def test_create_task_invalid_values(self, client, task_request, field, value):
        """Test that invalid task values are rejected with 400."""
        response = client.post("/api/tasks", json={**task_request, field: value})
        assert response.status_code == 400

    def test_create_task_missing_title(self, client, task_request):
        """Test that a missing required field fails Pydantic validation."""
        payload = {k: v for k, v in task_request.items() if k != "title"}
        assert client.post("/api/tasks", json=payload).status_code == 422


class TestCorsPolicy:
    """The API should only be readable from the frontend's origin."""

    def test_frontend_origin_allowed(self, client):
        response = client.get("/api/inventory", headers={"Origin": "http://localhost:3000"})
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_other_origin_not_allowed(self, client):
        response = client.get("/api/inventory", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in response.headers
        assert "access-control-allow-credentials" not in response.headers


class TestCompression:
    """Large responses should be gzip-compressed when the client accepts it."""

    def test_orders_response_is_gzipped(self, client):
        response = client.get("/api/orders", headers={"Accept-Encoding": "gzip"})
        assert response.status_code == 200
        assert response.headers.get("content-encoding") == "gzip"
        assert len(response.json()) > 0  # httpx transparently decompresses
