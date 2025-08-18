"""Integration tests for database functionality with SQLite and PostgreSQL."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.runs import Run
from src.repositories.runs import RunRepository
from src.schemas.runs import RunCreate


@pytest.mark.database
@pytest.mark.sqlite
class TestSQLiteDatabaseIntegration:
    """Test database integration with SQLite."""

    @pytest.mark.asyncio
    async def test_sqlite_connection(self, test_session: AsyncSession):
        """Test SQLite database connection and basic operations."""
        # Test that we can create a simple run
        run_id = str(uuid4())
        run_data = {
            "id": run_id,
            "name": "Test Run",
            "run_type": "chain",
            "start_time": datetime(2024, 1, 1, 0, 0, 0),
            "inputs": {"test": "data"},
            "project_name": "test-project",
        }

        run = Run(**run_data)
        test_session.add(run)
        await test_session.commit()

        # Test that we can query the run
        result = await test_session.execute(select(Run).where(Run.id == run_id))
        retrieved_run = result.scalar_one()

        assert str(retrieved_run.id) == run_id
        assert retrieved_run.name == "Test Run"
        assert retrieved_run.run_type == "chain"

    @pytest.mark.asyncio
    async def test_sqlite_repository_operations(self, test_session: AsyncSession):
        """Test repository operations with SQLite."""
        repository = RunRepository(test_session)

        # Test creating a run through repository
        run_data = RunCreate(
            id=str(uuid4()),
            name="Repository Test",
            run_type="llm",
            start_time=datetime(2024, 1, 1, 0, 0, 0),
            inputs={"prompt": "Hello world"},
            project_name="test-project",
        )

        created_run = await repository.create(run_data)
        assert str(created_run.id) == str(run_data.id)
        assert created_run.name == "Repository Test"

        # Test retrieving the run
        retrieved_run = await repository.get_by_id(created_run.id)
        assert retrieved_run is not None
        assert retrieved_run.run_type == "llm"


@pytest.mark.database
@pytest.mark.postgresql
class TestPostgreSQLDatabaseIntegration:
    """Test database integration with PostgreSQL."""

    @pytest.mark.asyncio
    async def test_postgresql_connection(self, test_session: AsyncSession):
        """Test PostgreSQL database connection and basic operations."""
        # Test that we can create a simple run
        run_id = str(uuid4())
        run_data = {
            "id": run_id,
            "name": "PostgreSQL Test Run",
            "run_type": "chain",
            "start_time": datetime(2024, 1, 1, 0, 0, 0),
            "inputs": {"test": "postgresql-data"},
            "project_name": "test-project",
        }

        run = Run(**run_data)
        test_session.add(run)
        await test_session.commit()

        # Test that we can query the run
        result = await test_session.execute(select(Run).where(Run.id == run_id))
        retrieved_run = result.scalar_one()

        assert str(retrieved_run.id) == run_id
        assert retrieved_run.name == "PostgreSQL Test Run"
        assert retrieved_run.run_type == "chain"

    @pytest.mark.asyncio
    async def test_postgresql_repository_operations(self, test_session: AsyncSession):
        """Test repository operations with PostgreSQL."""
        repository = RunRepository(test_session)

        # Test creating a run through repository
        run_data = RunCreate(
            id=str(uuid4()),
            name="PostgreSQL Repository Test",
            run_type="tool",
            start_time=datetime(2024, 1, 1, 0, 0, 0),
            inputs={"tool_name": "calculator"},
            project_name="test-project",
        )

        created_run = await repository.create(run_data)
        assert str(created_run.id) == str(run_data.id)
        assert created_run.name == "PostgreSQL Repository Test"

        # Test retrieving the run
        retrieved_run = await repository.get_by_id(created_run.id)
        assert retrieved_run is not None
        assert retrieved_run.run_type == "tool"


@pytest.mark.database
class TestCrossDatabaseCompatibility:
    """Test that database operations work consistently across both database types."""

    @pytest.mark.asyncio
    async def test_run_creation_consistency(self, test_session: AsyncSession):
        """Test that run creation works consistently across database types."""
        repository = RunRepository(test_session)

        # Create multiple runs with different types
        run_types = ["chain", "llm", "tool", "retrieval"]
        created_runs = []

        for i, run_type in enumerate(run_types):
            run_data = RunCreate(
                id=str(uuid4()),
                name=f"Consistency Test {i}",
                run_type=run_type,
                start_time=datetime(2024, 1, 1, 0, 0, 0),
                inputs={"test": f"data-{i}"},
                project_name="consistency-test",
            )
            run = await repository.create(run_data)
            created_runs.append(run)

        # Verify all runs were created
        assert len(created_runs) == 4

        # Test retrieving all runs
        all_runs = await repository.list_runs(project_name="consistency-test")
        assert len(all_runs) == 4

        # Verify run types
        run_types_found = [run.run_type for run in all_runs]
        assert "chain" in run_types_found
        assert "llm" in run_types_found
        assert "tool" in run_types_found
        assert "retrieval" in run_types_found

    @pytest.mark.asyncio
    async def test_hierarchical_relationships(self, test_session: AsyncSession):
        """Test that hierarchical relationships work across database types."""
        repository = RunRepository(test_session)

        # Create parent run
        parent_id = str(uuid4())
        parent_data = RunCreate(
            id=parent_id,
            name="Parent Run",
            run_type="chain",
            start_time=datetime(2024, 1, 1, 0, 0, 0),
            inputs={"parent": "data"},
            project_name="hierarchy-test",
        )
        parent_run = await repository.create(parent_data)

        # Create child runs
        child_runs = []
        for i in range(3):
            child_data = RunCreate(
                id=str(uuid4()),
                name=f"Child Run {i}",
                run_type="llm",
                start_time=datetime(2024, 1, 1, 0, 0, 0),
                inputs={"child": f"data-{i}"},
                project_name="hierarchy-test",
                parent_run_id=parent_id,
            )
            child_run = await repository.create(child_data)
            child_runs.append(child_run)

        # Verify parent-child relationships
        assert len(child_runs) == 3

        # Test getting children of parent
        children = await repository.list_runs(parent_run_id=parent_id)
        assert len(children) == 3

        # Test getting parent of children
        for child in children:
            parent = await repository.get_by_id(child.parent_run_id)
            assert parent is not None
            assert str(parent.id) == parent_id
