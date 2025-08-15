#!/usr/bin/env python3
"""Test script to debug the hierarchy fetching issue."""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.core.database import get_db_session, init_database
from src.repositories.runs import RunRepository


async def test_hierarchy():
    """Test the get_run_hierarchy method directly."""
    trace_id = UUID("3ef1cd29-2f07-4a28-b3ac-76cf204d73ba")

    # Initialize database first
    await init_database()

    async with get_db_session() as session:
        repo = RunRepository(session)

        print(f"Testing hierarchy for trace: {trace_id}")
        runs = await repo.get_run_hierarchy(trace_id)

        print(f"\nFound {len(runs)} runs:")
        for i, run in enumerate(runs, 1):
            parent = run.parent_run_id or "None"
            if parent != "None":
                parent = str(parent)[:8] + "..."
            print(f"  {i:2d}. {run.name} (id: {str(run.id)[:8]}..., parent: {parent})")

        # Test if we can find children manually
        print("\nTesting manual child lookup:")
        content_analyzer_id = None
        for run in runs:
            if run.name == "content_analyzer":
                content_analyzer_id = run.id
                break

        if content_analyzer_id:
            print(f"Found content_analyzer: {content_analyzer_id}")
            # Check if any runs have this as parent
            children = [r for r in runs if r.parent_run_id == content_analyzer_id]
            print(f"Children of content_analyzer: {len(children)}")
            for child in children:
                print(f"  - {child.name}")
        else:
            print("content_analyzer not found in results")


if __name__ == "__main__":
    asyncio.run(test_hierarchy())
