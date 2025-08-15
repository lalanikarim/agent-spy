#!/usr/bin/env python3
"""Test script to debug the API hierarchy construction issue."""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.core.database import get_db_session, init_database
from src.repositories.runs import RunRepository
from src.schemas.dashboard import RunHierarchyNode


async def test_api_hierarchy():
    """Test the API hierarchy construction logic."""
    trace_id = UUID("3ef1cd29-2f07-4a28-b3ac-76cf204d73ba")

    # Initialize database first
    await init_database()

    async with get_db_session() as session:
        repo = RunRepository(session)

        print(f"Testing API hierarchy construction for trace: {trace_id}")
        runs = await repo.get_run_hierarchy(trace_id)

        print(f"\n1. Repository returned {len(runs)} runs")

        # Build hierarchical structure (same logic as API)
        runs_by_id = {run.id: RunHierarchyNode.from_run(run) for run in runs}
        root_node = None

        print(f"\n2. Created {len(runs_by_id)} RunHierarchyNode objects")

        # First pass: find root and build parent-child relationships
        print("\n3. Building parent-child relationships:")
        for run in runs:
            node = runs_by_id[run.id]

            if run.parent_run_id is None:
                # This is the root
                print(f"   Found root: {run.name}")
                root_node = node
            else:
                # Add to parent's children
                parent_node = runs_by_id.get(run.parent_run_id)
                if parent_node:
                    print(f"   Adding {run.name} as child of {parent_node.name}")
                    parent_node.children.append(node)
                else:
                    print(f"   WARNING: Parent not found for {run.name}: {run.parent_run_id}")

        print("\n4. Final hierarchy:")

        def print_hierarchy(node, level=0):
            indent = "  " * level
            print(f"{indent}- {node.name} - children: {len(node.children)}")
            for child in node.children:
                print_hierarchy(child, level + 1)

        if root_node:
            print_hierarchy(root_node)
        else:
            print("   No root node found!")


if __name__ == "__main__":
    asyncio.run(test_api_hierarchy())
