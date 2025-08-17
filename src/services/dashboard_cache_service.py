"""Dashboard-specific caching service."""

from datetime import UTC, datetime, timedelta
from typing import Any

from src.core.database import get_db_session
from src.core.logging import get_logger
from src.repositories.runs import RunRepository
from src.services.cache_service import cache_service, cached

logger = get_logger(__name__)


class DashboardCacheService:
    """Dashboard statistics caching service."""

    def __init__(self):
        self.stats_ttl = 300  # 5 minutes
        self.project_stats_ttl = 600  # 10 minutes

    @cached(ttl=300, key_prefix="dashboard:")
    async def get_dashboard_stats(self) -> dict[str, Any]:
        """Get cached dashboard statistics."""
        async with get_db_session() as session:
            runs_repo = RunRepository(session)

            # Calculate comprehensive dashboard stats
            total_runs = await runs_repo.count_all()
            successful_runs = await runs_repo.count_by_status("success")
            failed_runs = await runs_repo.count_by_status("error")

            # Recent activity (last 24 hours)
            recent_cutoff = datetime.now(UTC) - timedelta(hours=24)
            recent_runs = await runs_repo.count_since(recent_cutoff)

            # Project statistics
            project_stats = await runs_repo.get_project_statistics()

            # Performance metrics
            avg_duration = await runs_repo.get_average_duration()

            stats = {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
                "recent_runs_24h": recent_runs,
                "project_stats": project_stats,
                "average_duration_ms": avg_duration,
                "last_updated": datetime.now(UTC).isoformat(),
            }

            logger.debug("Dashboard stats calculated and cached")
            return stats

    @cached(ttl=600, key_prefix="dashboard:project:")
    async def get_project_stats(self, project_name: str) -> dict[str, Any]:
        """Get cached project-specific statistics."""
        async with get_db_session() as session:
            runs_repo = RunRepository(session)

            stats = await runs_repo.get_project_detailed_stats(project_name)
            stats["last_updated"] = datetime.now(UTC).isoformat()

            logger.debug(f"Project stats calculated and cached for: {project_name}")
            return stats

    async def invalidate_dashboard_cache(self):
        """Invalidate all dashboard-related cache."""
        patterns = [
            "dashboard:*",
            "func:get_dashboard_stats:*",
            "func:get_project_stats:*",
        ]

        for pattern in patterns:
            await cache_service.invalidate_pattern(pattern)

        logger.info("Dashboard cache invalidated")

    async def warm_dashboard_cache(self):
        """Pre-warm dashboard cache with common queries."""
        try:
            # Warm main dashboard stats
            await self.get_dashboard_stats()

            # Warm top project stats
            async with get_db_session() as session:
                runs_repo = RunRepository(session)
                top_projects = await runs_repo.get_top_projects(limit=10)

                for project in top_projects:
                    await self.get_project_stats(project["name"])

            logger.info("Dashboard cache warmed successfully")

        except Exception as e:
            logger.error(f"Failed to warm dashboard cache: {e}")


# Global dashboard cache service
dashboard_cache = DashboardCacheService()
