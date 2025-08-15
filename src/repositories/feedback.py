"""Repository for feedback data access."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models.feedback import Feedback
from src.schemas.feedback import FeedbackCreate

logger = get_logger(__name__)


class FeedbackRepository:
    """Repository for feedback data access operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session."""
        self.session = session
    
    async def create(self, run_id: UUID, feedback_data: FeedbackCreate) -> Feedback:
        """Create new feedback for a run."""
        logger.debug(f"Creating feedback for run: {run_id}")
        
        feedback = Feedback(
            id=feedback_data.feedback_id or UUID(),
            run_id=run_id,
            score=feedback_data.score,
            value=feedback_data.value,
            comment=feedback_data.comment,
            correction=feedback_data.correction,
            source_info=feedback_data.source_info,
            feedback_source_type=feedback_data.feedback_source_type,
        )
        
        self.session.add(feedback)
        await self.session.flush()
        
        logger.info(f"Created feedback: {feedback.id} for run: {run_id}")
        return feedback
    
    async def get_by_id(self, feedback_id: UUID) -> Feedback | None:
        """Get feedback by its ID."""
        logger.debug(f"Getting feedback by ID: {feedback_id}")
        
        stmt = select(Feedback).where(Feedback.id == feedback_id)
        result = await self.session.execute(stmt)
        feedback = result.scalar_one_or_none()
        
        if feedback:
            logger.debug(f"Found feedback: {feedback_id}")
        else:
            logger.debug(f"Feedback not found: {feedback_id}")
        
        return feedback
    
    async def list_by_run_id(self, run_id: UUID) -> list[Feedback]:
        """Get all feedback for a specific run."""
        logger.debug(f"Getting feedback for run: {run_id}")
        
        stmt = select(Feedback).where(Feedback.run_id == run_id).order_by(desc(Feedback.created_at))
        result = await self.session.execute(stmt)
        feedback_list = result.scalars().all()
        
        logger.debug(f"Found {len(feedback_list)} feedback entries for run: {run_id}")
        return list(feedback_list)
    
    async def delete(self, feedback_id: UUID) -> bool:
        """Delete feedback by ID."""
        logger.debug(f"Deleting feedback: {feedback_id}")
        
        stmt = select(Feedback).where(Feedback.id == feedback_id)
        result = await self.session.execute(stmt)
        feedback = result.scalar_one_or_none()
        
        if not feedback:
            logger.warning(f"Feedback not found for deletion: {feedback_id}")
            return False
        
        await self.session.delete(feedback)
        await self.session.flush()
        
        logger.info(f"Deleted feedback: {feedback_id}")
        return True

