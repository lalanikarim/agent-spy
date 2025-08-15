"""End-to-end tests for dashboard functionality."""

import time
from uuid import uuid4

import pytest
import requests


class TestDashboardE2E:
    """End-to-end tests for dashboard API endpoints."""

    BASE_URL = "http://localhost:8000/api/v1"

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test - ensure server is running."""
        # Check if server is running
        try:
            response = requests.get(f"{self.BASE_URL.replace('/api/v1', '')}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Server not running - start with 'PYTHONPATH=. uv run python src/main.py'")
        except requests.ConnectionError:
            pytest.skip("Server not running - start with 'PYTHONPATH=. uv run python src/main.py'")

    def test_dashboard_root_runs_endpoint(self):
        """Test that root runs endpoint returns expected structure."""
        response = requests.get(f"{self.BASE_URL}/dashboard/runs/roots")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "runs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data

        # Check data types
        assert isinstance(data["runs"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["limit"], int)
        assert isinstance(data["offset"], int)
        assert isinstance(data["has_more"], bool)

        # If there are runs, check their structure
        if data["runs"]:
            run = data["runs"][0]
            assert "id" in run
            assert "name" in run
            assert "run_type" in run
            assert "status" in run
            assert "start_time" in run
            assert run["parent_run_id"] is None  # Should be root runs only

    def test_dashboard_root_runs_filtering(self):
        """Test root runs endpoint with various filters."""
        # Test with limit
        response = requests.get(f"{self.BASE_URL}/dashboard/runs/roots?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        if data["runs"]:
            assert len(data["runs"]) <= 2

        # Test with status filter
        response = requests.get(f"{self.BASE_URL}/dashboard/runs/roots?status=completed")
        assert response.status_code == 200
        data = response.json()
        for run in data["runs"]:
            assert run["status"] == "completed"

        # Test with search
        response = requests.get(f"{self.BASE_URL}/dashboard/runs/roots?search=LangGraph")
        assert response.status_code == 200
        # Should not error even if no results

    def test_dashboard_root_runs_pagination(self):
        """Test pagination in root runs endpoint."""
        # Get first page
        response1 = requests.get(f"{self.BASE_URL}/dashboard/runs/roots?limit=1&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()

        # Get second page
        response2 = requests.get(f"{self.BASE_URL}/dashboard/runs/roots?limit=1&offset=1")
        assert response2.status_code == 200
        data2 = response2.json()

        # If both have results, they should be different
        if data1["runs"] and data2["runs"]:
            assert data1["runs"][0]["id"] != data2["runs"][0]["id"]

    def test_dashboard_hierarchy_endpoint_not_found(self):
        """Test hierarchy endpoint with non-existent trace ID."""
        fake_id = str(uuid4())
        response = requests.get(f"{self.BASE_URL}/dashboard/runs/{fake_id}/hierarchy")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_dashboard_stats_summary(self):
        """Test dashboard stats summary endpoint."""
        response = requests.get(f"{self.BASE_URL}/dashboard/stats/summary")

        assert response.status_code == 200
        data = response.json()

        # Check main structure
        assert "stats" in data
        assert "recent_projects" in data
        assert "timestamp" in data

        # Check stats structure
        stats = data["stats"]
        assert "total_runs" in stats
        assert "total_traces" in stats
        assert "recent_runs_24h" in stats
        assert "status_distribution" in stats
        assert "run_type_distribution" in stats
        assert "project_distribution" in stats

        # Check data types
        assert isinstance(stats["total_runs"], int)
        assert isinstance(stats["total_traces"], int)
        assert isinstance(stats["recent_runs_24h"], int)
        assert isinstance(stats["status_distribution"], dict)
        assert isinstance(stats["run_type_distribution"], dict)
        assert isinstance(stats["project_distribution"], dict)

        # Check recent projects
        assert isinstance(data["recent_projects"], list)
        for project in data["recent_projects"]:
            assert "name" in project
            assert "total_runs" in project
            assert "total_traces" in project
            # last_activity can be null

    def test_dashboard_endpoints_cors(self):
        """Test that dashboard endpoints handle CORS properly."""
        # Test preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        }

        response = requests.options(f"{self.BASE_URL}/dashboard/runs/roots", headers=headers)
        # Should not fail with CORS error (exact response depends on server config)
        assert response.status_code in [
            200,
            204,
            405,
        ]  # 405 is OK if OPTIONS not explicitly handled

    def test_dashboard_endpoints_error_handling(self):
        """Test error handling in dashboard endpoints."""
        # Test invalid UUID format
        response = requests.get(f"{self.BASE_URL}/dashboard/runs/invalid-uuid/hierarchy")
        assert response.status_code == 422  # Validation error

        # Test invalid query parameters
        response = requests.get(f"{self.BASE_URL}/dashboard/runs/roots?limit=invalid")
        assert response.status_code == 422  # Validation error

        # Test limit out of range
        response = requests.get(f"{self.BASE_URL}/dashboard/runs/roots?limit=1000")
        assert response.status_code == 422  # Validation error (limit max is 200)

    def test_dashboard_endpoints_performance(self):
        """Test that dashboard endpoints respond within reasonable time."""

        # Test root runs endpoint
        start_time = time.time()
        response = requests.get(f"{self.BASE_URL}/dashboard/runs/roots")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds

        # Test stats endpoint
        start_time = time.time()
        response = requests.get(f"{self.BASE_URL}/dashboard/stats/summary")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds

    def test_dashboard_data_consistency(self):
        """Test that data is consistent between endpoints."""
        # Get root runs count from roots endpoint
        roots_response = requests.get(f"{self.BASE_URL}/dashboard/runs/roots?limit=200")
        assert roots_response.status_code == 200
        roots_data = roots_response.json()

        # Get stats
        stats_response = requests.get(f"{self.BASE_URL}/dashboard/stats/summary")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()

        # The total traces in stats should match or be close to the root runs count
        # (might differ slightly due to timing or filtering)
        roots_count = roots_data["total"]
        traces_count = stats_data["stats"]["total_traces"]

        # They should be reasonably close (allow for some variance due to concurrent operations)
        assert abs(roots_count - traces_count) <= 5
