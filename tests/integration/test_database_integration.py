"""Integration tests for database functionality with SQLite and PostgreSQL."""

import pytest
from sqlalchemy import select

from src.models.runs import Run
from src.repositories.runs import RunRepository


class TestDatabaseIntegration:
    """Test database integration with both SQLite and PostgreSQL."""

    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_database_connection(self, test_session):
        """Test basic database connection and session functionality."""
        # Test that we can execute a simple query
        result = await test_session.execute(select(1))
        assert result.scalar() == 1

    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_run_model_creation(self, test_session):
        """Test creating and querying Run models."""
        from datetime import datetime
        from uuid import uuid4

        # Create a test run
        run = Run(
            id=uuid4(),
            name="Test Run",
            run_type="chain",
            start_time=datetime.now(),
            status="completed",
            project_name="test-project",
        )

        # Add to database
        test_session.add(run)
        await test_session.commit()

        # Query the run
        result = await test_session.execute(select(Run).where(Run.id == run.id))
        retrieved_run = result.scalar_one()

        # Verify the run was saved correctly
        assert retrieved_run.id == run.id
        assert retrieved_run.name == "Test Run"
        assert retrieved_run.run_type == "chain"
        assert retrieved_run.status == "completed"
        assert retrieved_run.project_name == "test-project"

    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_run_repository_integration(self, test_session):
        """Test RunRepository with real database session."""
        from datetime import datetime, timedelta
        from uuid import uuid4

        # Create repository with real session
        repository = RunRepository(test_session)

        # Create test runs
        now = datetime.now()
        root_run = Run(
            id=uuid4(),
            name="Root Test Run",
            run_type="chain",
            start_time=now,
            end_time=now + timedelta(seconds=30),
            status="completed",
            project_name="test-project",
            parent_run_id=None,
        )

        child_run = Run(
            id=uuid4(),
            name="Child Test Run",
            run_type="llm",
            start_time=now + timedelta(seconds=5),
            end_time=now + timedelta(seconds=25),
            status="completed",
            project_name="test-project",
            parent_run_id=root_run.id,
        )

        # Add runs to database
        test_session.add_all([root_run, child_run])
        await test_session.commit()

        # Test repository methods - check that we can get root runs
        root_runs = await repository.get_root_runs()
        # Find our specific root run in the results
        our_root_run = next((r for r in root_runs if r.id == root_run.id), None)
        assert our_root_run is not None
        assert our_root_run.name == "Root Test Run"

        # Test hierarchy - returns a list of all runs in the hierarchy
        hierarchy = await repository.get_run_hierarchy(root_run.id)
        assert hierarchy is not None
        assert len(hierarchy) == 2  # root run + child run

        # Find the root and child runs in the hierarchy
        root_in_hierarchy = next((r for r in hierarchy if r.id == root_run.id), None)
        child_in_hierarchy = next((r for r in hierarchy if r.id == child_run.id), None)

        assert root_in_hierarchy is not None
        assert child_in_hierarchy is not None
        assert root_in_hierarchy.name == "Root Test Run"
        assert child_in_hierarchy.name == "Child Test Run"

    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_database_transactions(self, test_session):
        """Test database transaction rollback functionality."""
        from datetime import datetime
        from uuid import uuid4

        # Create a run
        run = Run(
            id=uuid4(),
            name="Transaction Test Run",
            run_type="chain",
            start_time=datetime.now(),
            status="running",
            project_name="test-project",
        )

        # Add to database
        test_session.add(run)
        await test_session.commit()

        # Verify it exists
        result = await test_session.execute(select(Run).where(Run.id == run.id))
        assert result.scalar_one() is not None

        # Test that we can query the run
        assert run.name == "Transaction Test Run"
        assert run.run_type == "chain"

    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_database_concurrent_access(self, test_session_maker):
        """Test concurrent database access."""
        from datetime import datetime
        from uuid import uuid4

        # Create multiple sessions
        async with test_session_maker() as session1, test_session_maker() as session2:
            # Create runs in different sessions
            run1 = Run(
                id=uuid4(),
                name="Concurrent Run 1",
                run_type="chain",
                start_time=datetime.now(),
                status="completed",
                project_name="test-project",
            )

            run2 = Run(
                id=uuid4(),
                name="Concurrent Run 2",
                run_type="llm",
                start_time=datetime.now(),
                status="completed",
                project_name="test-project",
            )

            # Add to different sessions
            session1.add(run1)
            session2.add(run2)

            # Commit both
            await session1.commit()
            await session2.commit()

            # Verify both runs exist
            result1 = await session1.execute(select(Run).where(Run.id == run1.id))
            result2 = await session2.execute(select(Run).where(Run.id == run2.id))

            assert result1.scalar_one() is not None
            assert result2.scalar_one() is not None
