"""Unit tests for dashboard schemas."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from src.schemas.dashboard import (
    DashboardStats,
    DashboardSummary,
    ProjectInfo,
    RootRunsResponse,
    RunHierarchyNode,
    RunHierarchyResponse,
)
from src.schemas.runs import RunResponse


class TestDashboardSchemas:
    """Test dashboard Pydantic schemas."""

    def test_run_hierarchy_node_from_run(self):
        """Test creating RunHierarchyNode from a Run model."""
        # Create mock run
        mock_run = MagicMock()
        mock_run.id = uuid4()
        mock_run.name = "Test Run"
        mock_run.run_type = "llm"
        mock_run.status = "completed"
        mock_run.start_time = datetime.now()
        mock_run.end_time = datetime.now() + timedelta(seconds=30)
        mock_run.parent_run_id = None
        mock_run.inputs = {"query": "test"}
        mock_run.outputs = {"response": "result"}
        mock_run.error = None
        mock_run.extra = {"model": "gpt-4"}
        mock_run.tags = ["test"]

        # Create node
        node = RunHierarchyNode.from_run(mock_run)

        # Verify
        assert node.id == mock_run.id
        assert node.name == mock_run.name
        assert node.run_type == mock_run.run_type
        assert node.status == mock_run.status
        assert node.start_time == mock_run.start_time
        assert node.end_time == mock_run.end_time
        assert node.parent_run_id == mock_run.parent_run_id
        assert node.inputs == mock_run.inputs
        assert node.outputs == mock_run.outputs
        assert node.error == mock_run.error
        assert node.extra == mock_run.extra
        assert node.tags == mock_run.tags
        assert node.duration_ms == 30000  # 30 seconds in milliseconds
        assert node.children == []

    def test_run_hierarchy_node_duration_calculation(self):
        """Test duration calculation in RunHierarchyNode."""
        # Test with both start and end times
        mock_run = MagicMock()
        mock_run.id = uuid4()
        mock_run.name = "Test"
        mock_run.run_type = "llm"
        mock_run.status = "completed"
        mock_run.parent_run_id = None
        mock_run.inputs = {}
        mock_run.outputs = {}
        mock_run.error = None
        mock_run.extra = {}
        mock_run.tags = []

        start = datetime.now()
        mock_run.start_time = start
        mock_run.end_time = start + timedelta(milliseconds=1500)  # 1.5 seconds

        node = RunHierarchyNode.from_run(mock_run)
        assert node.duration_ms == 1500

        # Test with no end time
        mock_run.end_time = None
        node = RunHierarchyNode.from_run(mock_run)
        assert node.duration_ms is None

        # Test with no start time
        mock_run.start_time = None
        mock_run.end_time = datetime.now()
        node = RunHierarchyNode.from_run(mock_run)
        assert node.duration_ms is None

    def test_run_hierarchy_response_validation(self):
        """Test RunHierarchyResponse validation."""
        root_id = uuid4()

        # Create a simple hierarchy node
        hierarchy = RunHierarchyNode(
            id=root_id,
            name="Root",
            run_type="chain",
            status="completed",
            start_time=datetime.now(),
            parent_run_id=None,
            children=[],
        )

        # Create response
        response = RunHierarchyResponse(root_run_id=root_id, hierarchy=hierarchy, total_runs=1, max_depth=1)

        assert response.root_run_id == root_id
        assert response.hierarchy == hierarchy
        assert response.total_runs == 1
        assert response.max_depth == 1

    def test_root_runs_response_validation(self):
        """Test RootRunsResponse validation."""
        # Create mock runs
        runs = []
        for i in range(3):
            run_data = {
                "id": str(uuid4()),
                "name": f"Run {i}",
                "run_type": "chain",
                "status": "completed",
                "start_time": datetime.now().isoformat(),
                "parent_run_id": None,
                "project_name": "test",
            }
            runs.append(RunResponse(**run_data))

        response = RootRunsResponse(runs=runs, total=10, limit=50, offset=0, has_more=True)

        assert len(response.runs) == 3
        assert response.total == 10
        assert response.limit == 50
        assert response.offset == 0
        assert response.has_more is True

    def test_dashboard_stats_validation(self):
        """Test DashboardStats validation."""
        stats = DashboardStats(
            total_runs=100,
            total_traces=25,
            recent_runs_24h=15,
            status_distribution={"completed": 80, "failed": 15, "running": 5},
            run_type_distribution={"llm": 60, "chain": 25, "tool": 15},
            project_distribution={"project1": 70, "project2": 30},
        )

        assert stats.total_runs == 100
        assert stats.total_traces == 25
        assert stats.recent_runs_24h == 15
        assert stats.status_distribution["completed"] == 80
        assert stats.run_type_distribution["llm"] == 60
        assert stats.project_distribution["project1"] == 70

    def test_project_info_validation(self):
        """Test ProjectInfo validation."""
        now = datetime.now()

        project = ProjectInfo(name="test-project", total_runs=50, total_traces=12, last_activity=now)

        assert project.name == "test-project"
        assert project.total_runs == 50
        assert project.total_traces == 12
        assert project.last_activity == now

        # Test with None last_activity
        project_no_activity = ProjectInfo(name="inactive-project", total_runs=0, total_traces=0, last_activity=None)

        assert project_no_activity.last_activity is None

    def test_dashboard_summary_validation(self):
        """Test DashboardSummary validation."""
        stats = DashboardStats(
            total_runs=100,
            total_traces=25,
            recent_runs_24h=15,
            status_distribution={"completed": 80, "failed": 20},
            run_type_distribution={"llm": 60, "chain": 40},
            project_distribution={"project1": 100},
        )

        projects = [
            ProjectInfo(
                name="project1",
                total_runs=100,
                total_traces=25,
                last_activity=datetime.now(),
            )
        ]

        timestamp = datetime.now()

        summary = DashboardSummary(stats=stats, recent_projects=projects, timestamp=timestamp)

        assert summary.stats == stats
        assert summary.recent_projects == projects
        assert summary.timestamp == timestamp

    def test_run_hierarchy_node_recursive_structure(self):
        """Test that RunHierarchyNode supports recursive children."""
        # Create parent node
        parent_id = uuid4()
        parent = RunHierarchyNode(
            id=parent_id,
            name="Parent",
            run_type="chain",
            status="completed",
            start_time=datetime.now(),
            parent_run_id=None,
            children=[],
        )

        # Create child node
        child_id = uuid4()
        child = RunHierarchyNode(
            id=child_id,
            name="Child",
            run_type="llm",
            status="completed",
            start_time=datetime.now(),
            parent_run_id=parent_id,
            children=[],
        )

        # Add child to parent
        parent.children.append(child)

        # Verify structure
        assert len(parent.children) == 1
        assert parent.children[0] == child
        assert child.parent_run_id == parent_id

        # Test serialization works
        parent_dict = parent.model_dump()
        assert len(parent_dict["children"]) == 1
        assert parent_dict["children"][0]["id"] == child_id  # UUID is preserved in model_dump

    def test_schema_json_serialization(self):
        """Test that all schemas can be JSON serialized."""
        import json

        # Test RunHierarchyNode
        node = RunHierarchyNode(
            id=uuid4(),
            name="Test",
            run_type="llm",
            status="completed",
            start_time=datetime.now(),
            parent_run_id=None,
            children=[],
        )

        node_json = json.dumps(node.model_dump(), default=str)
        assert node_json is not None

        # Test DashboardStats
        stats = DashboardStats(
            total_runs=100,
            total_traces=25,
            recent_runs_24h=15,
            status_distribution={"completed": 80},
            run_type_distribution={"llm": 60},
            project_distribution={"project1": 100},
        )

        stats_json = json.dumps(stats.model_dump(), default=str)
        assert stats_json is not None
