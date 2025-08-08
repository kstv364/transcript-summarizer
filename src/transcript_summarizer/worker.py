"""Celery worker for background summarization tasks."""

import time
import asyncio
from datetime import datetime
from celery import Celery
import structlog

from .config.settings import get_settings
from .core.summarizer import create_summarizer
from .storage.vector_store import get_vector_store
from .models.schemas import SummarizationResult

logger = structlog.get_logger(__name__)

# Initialize settings
settings = get_settings()

# Create Celery app
app = Celery(
    "transcript_summarizer",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["transcript_summarizer.worker"]
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "transcript_summarizer.worker.summarize_transcript_task": {"queue": "summarization"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
)


@app.task(bind=True, name="summarize_transcript_task")
def summarize_transcript_task(self, text: str, summary_type: str = "comprehensive"):
    """
    Celery task for summarizing transcripts.
    
    Args:
        text: The transcript text to summarize
        summary_type: Type of summary to generate
        
    Returns:
        Dictionary containing the summarization result
    """
    task_id = self.request.id
    start_time = time.time()
    
    logger.info("Starting summarization task", task_id=task_id, 
                text_length=len(text), summary_type=summary_type)
    
    try:
        # Update task state to processing
        self.update_state(
            state="PROCESSING",
            meta={"progress": 0, "message": "Initializing summarization..."}
        )
        
        # Run the summarization in the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _run_summarization(text, summary_type, task_id, self.update_state)
            )
        finally:
            loop.close()
        
        # Calculate processing time
        processing_time = time.time() - start_time
        result.processing_time = processing_time
        
        logger.info("Summarization task completed", 
                   task_id=task_id, processing_time=processing_time)
        
        # Return the result as a dictionary
        return {
            "summary": result.summary,
            "original_length": result.original_length,
            "summary_length": result.summary_length,
            "compression_ratio": result.compression_ratio,
            "chunk_count": result.chunk_count,
            "summary_type": result.summary_type,
            "processing_time": result.processing_time,
            "created_at": result.created_at.isoformat(),
        }
        
    except Exception as e:
        logger.error("Summarization task failed", task_id=task_id, error=str(e))
        
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "message": "Summarization failed"}
        )
        
        # Re-raise the exception so Celery marks the task as failed
        raise


async def _run_summarization(
    text: str, 
    summary_type: str, 
    task_id: str, 
    update_state_func
) -> SummarizationResult:
    """
    Internal function to run the summarization process.
    
    Args:
        text: Text to summarize
        summary_type: Type of summary
        task_id: Task identifier
        update_state_func: Function to update task state
        
    Returns:
        SummarizationResult
    """
    # Create summarizer
    update_state_func(
        state="PROCESSING",
        meta={"progress": 10, "message": "Creating summarizer..."}
    )
    
    summarizer = await create_summarizer()
    
    # Run summarization
    update_state_func(
        state="PROCESSING", 
        meta={"progress": 20, "message": "Processing transcript..."}
    )
    
    result = await summarizer.summarize_transcript(text, summary_type)
    
    # Store result in vector database
    update_state_func(
        state="PROCESSING",
        meta={"progress": 90, "message": "Storing result..."}
    )
    
    try:
        vector_store = await get_vector_store()
        await vector_store.store_summary(task_id, text, result)
    except Exception as e:
        logger.warning("Failed to store result in vector database", 
                      task_id=task_id, error=str(e))
        # Don't fail the task if vector storage fails
    
    update_state_func(
        state="PROCESSING",
        meta={"progress": 100, "message": "Summarization completed"}
    )
    
    return result


# Health check task
@app.task(name="health_check_task")
def health_check_task():
    """Health check task for monitoring worker status."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "worker_id": app.control.inspect().active()
    }


if __name__ == "__main__":
    # Run worker directly
    app.start()
