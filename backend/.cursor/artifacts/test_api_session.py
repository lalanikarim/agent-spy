#!/usr/bin/env python3
"""Test script using the exact same session as the FastAPI API."""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.core.database import get_db
from src.repositories.runs import RunRepository
from src.schemas.dashboard import RunHierarchyNode


async def test_with_api_session():
    """Test using the exact same get_db dependency as the API."""
    trace_id = UUID("3ef1cd29-2f07-4a28-b3ac-76cf204d73ba")

    print(f"Testing with FastAPI get_db dependency for trace: {trace_id}")

    # Use the exact same dependency as the API
    async for db in get_db():
        repo = RunRepository(db)

        runs = await repo.get_run_hierarchy(trace_id)
        print(f"\nRepository returned {len(runs)} runs")

        # Build hierarchical structure (exact same logic as API)
        runs_by_id = {run.id: RunHierarchyNode.from_run(run) for run in runs}
        root_node = None

        # First pass: find root and build parent-child relationships
        for run in runs:
            node = runs_by_id[run.id]

            if run.parent_run_id is None:
                root_node = node
            else:
                parent_node = runs_by_id.get(run.parent_run_id)
                if parent_node:
                    parent_node.children.append(node)

        def count_total_nodes(node):
            """Count total nodes in hierarchy."""
            count = 1
            for child in node.children:
                count += count_total_nodes(child)
            return count

        if root_node:
            total_nodes = count_total_nodes(root_node)
            print(f"Root node: {root_node.name}")
            print(f"Direct children: {len(root_node.children)}")
            print(f"Total nodes in hierarchy: {total_nodes}")

            def print_hierarchy(node, level=0):
                indent = "  " * level
                print(f"{indent}- {node.name} - children: {len(node.children)}")
                for child in node.children:
                    print_hierarchy(child, level + 1)

            print("\nHierarchy structure:")
            print_hierarchy(root_node)
        else:
            print("No root node found!")

        break  # Only use the first session


if __name__ == "__main__":
    asyncio.run(test_with_api_session())
