"""FastAPI application for the transcript summarizer API."""

import time
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from .config.settings import get_settings
from .models.schemas import (
    SummarizationRequest,
    SummarizationResponse,
    TaskStatusResponse,
    HealthResponse,
    ErrorResponse,
    TaskStatus,
    SummaryType,
)
from .worker import app as celery_app
from .storage.vector_store import get_vector_store
from .utils.vtt_parser import VTTParser, is_valid_vtt

logger = structlog.get_logger(__name__)

# Prometheus metrics
request_count = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
request_duration = Histogram("http_request_duration_seconds", "HTTP request duration")
summarization_count = Counter("summarizations_total", "Total summarizations", ["summary_type"])
summarization_duration = Histogram("summarization_duration_seconds", "Summarization duration")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting transcript summarizer API")
    
    # Initialize vector store on startup
    try:
        vector_store = await get_vector_store()
        health = await vector_store.health_check()
        logger.info("Vector store health check", **health)
    except Exception as e:
        logger.error("Failed to initialize vector store", error=str(e))
    
    yield
    
    logger.info("Shutting down transcript summarizer API")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="API for summarizing transcripts using Ollama and LangChain",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Middleware to collect request metrics."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    request_duration.observe(duration)
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred"
        ).dict()
    )


@app.post("/summarize", response_model=SummarizationResponse)
async def summarize_transcript(request: SummarizationRequest) -> SummarizationResponse:
    """
    Submit a transcript for summarization.
    
    This endpoint accepts a transcript and queues it for processing.
    Use the returned task_id to check status and retrieve the summary.
    """
    try:
        logger.info("Received summarization request", 
                   text_length=len(request.text), 
                   summary_type=request.summary_type)
        
        # Validate text length
        if len(request.text) > settings.max_text_length:
            raise HTTPException(
                status_code=413,
                detail=f"Text too long. Maximum length is {settings.max_text_length} characters."
            )
        
        # Submit task to Celery
        task = celery_app.send_task(
            "summarize_transcript_task",
            args=[request.text, request.summary_type.value],
            queue="summarization"
        )
        
        # Update metrics
        summarization_count.labels(summary_type=request.summary_type.value).inc()
        
        logger.info("Submitted summarization task", task_id=task.id)
        
        # Estimate completion time based on text length
        estimated_time = max(30, len(request.text) // 1000)  # Rough estimate
        
        return SummarizationResponse(
            task_id=task.id,
            status=TaskStatus.PENDING,
            message="Summarization task submitted successfully",
            estimated_completion_time=estimated_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to submit summarization task", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to submit summarization task")


@app.post("/summarize/upload", response_model=SummarizationResponse)
async def summarize_uploaded_file(
    file: UploadFile = File(...),
    summary_type: str = Form(default="concise"),
    custom_prompt: str = Form(default="")
) -> SummarizationResponse:
    """
    Upload a VTT or text file for summarization.
    
    Accepts VTT subtitle files or plain text files and extracts transcript
    for summarization processing.
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in ['vtt', 'txt', 'text']:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload .vtt, .txt, or .text files"
            )
        
        # Read file content
        content = await file.read()
        
        # Check file size (10MB limit)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 10MB"
            )
        
        try:
            # Decode content
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File must be UTF-8 encoded"
            )
        
        # Extract transcript text
        if file_ext == 'vtt':
            try:
                parser = VTTParser()
                transcript_text = parser.parse_vtt_content(text_content)
                
                if not transcript_text.strip():
                    raise HTTPException(
                        status_code=400,
                        detail="No text could be extracted from VTT file"
                    )
                
                logger.info("Processed VTT file", 
                           filename=file.filename,
                           original_size=len(text_content),
                           extracted_size=len(transcript_text))
                           
            except Exception as e:
                logger.error("Failed to parse VTT file", error=str(e))
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to parse VTT file: {str(e)}"
                )
        else:
            # Plain text file
            transcript_text = text_content.strip()
            
        # Validate transcript
        if not transcript_text:
            raise HTTPException(
                status_code=400,
                detail="File appears to be empty or contains no text"
            )
        
        if len(transcript_text) < 50:
            raise HTTPException(
                status_code=400,
                detail="Transcript too short (minimum 50 characters)"
            )
        
        # Validate summary type
        try:
            summary_type_enum = SummaryType(summary_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid summary type: {summary_type}"
            )
        
        # Create summarization request
        request_args = [transcript_text, summary_type_enum.value]
        if custom_prompt.strip():
            request_args.append(custom_prompt.strip())
        
        # Submit task to Celery
        task = celery_app.send_task(
            "summarize_transcript_task",
            args=request_args,
            queue="summarization"
        )
        
        # Update metrics
        summarization_count.labels(summary_type=summary_type).inc()
        
        logger.info("Submitted file-based summarization task", 
                   task_id=task.id,
                   filename=file.filename,
                   file_type=file_ext,
                   text_length=len(transcript_text))
        
        # Estimate completion time
        estimated_time = max(30, len(transcript_text) // 1000)
        
        return SummarizationResponse(
            task_id=task.id,
            status=TaskStatus.PENDING,
            message=f"File '{file.filename}' uploaded and queued for summarization",
            estimated_completion_time=estimated_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process uploaded file", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to process uploaded file"
        )


@app.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get the status of a summarization task.
    
    Returns the current status, progress, and result if completed.
    """
    try:
        # Get task result from Celery
        task_result = celery_app.AsyncResult(task_id)
        
        # Determine status
        if task_result.state == "PENDING":
            status = TaskStatus.PENDING
            progress = None
            result = None
            error_message = None
        elif task_result.state == "PROCESSING":
            status = TaskStatus.PROCESSING
            progress = task_result.info.get("progress", 0) if task_result.info else 0
            result = None
            error_message = None
        elif task_result.state == "SUCCESS":
            status = TaskStatus.COMPLETED
            progress = 100
            # Convert result dict back to SummarizationResult
            if task_result.result:
                from .models.schemas import SummarizationResult
                result = SummarizationResult(**task_result.result)
            else:
                result = None
            error_message = None
        elif task_result.state == "FAILURE":
            status = TaskStatus.FAILED
            progress = None
            result = None
            error_message = str(task_result.info) if task_result.info else "Task failed"
        else:
            status = TaskStatus.PENDING
            progress = None
            result = None
            error_message = None
        
        return TaskStatusResponse(
            task_id=task_id,
            status=status,
            progress=progress,
            result=result,
            error_message=error_message
        )
        
    except Exception as e:
        logger.error("Failed to get task status", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get task status")


@app.get("/summary/{task_id}")
async def get_summary(task_id: str):
    """
    Get the completed summary for a task.
    
    This endpoint returns the summary if the task is completed,
    or an error if the task is still processing or failed.
    """
    try:
        # First check Celery result
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == "SUCCESS" and task_result.result:
            return task_result.result
        
        # If not in Celery, try vector store
        vector_store = await get_vector_store()
        result = await vector_store.get_summary(task_id)
        
        if result:
            return result.dict()
        
        # Check if task exists but is not completed
        if task_result.state in ["PENDING", "PROCESSING"]:
            raise HTTPException(
                status_code=202,
                detail="Task is still processing. Check status endpoint for progress."
            )
        elif task_result.state == "FAILURE":
            raise HTTPException(
                status_code=400,
                detail=f"Task failed: {task_result.info}"
            )
        else:
            raise HTTPException(status_code=404, detail="Summary not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get summary", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve summary")


@app.get("/search")
async def search_summaries(
    query: str,
    limit: int = 5,
    summary_type: str = None
):
    """
    Search for similar summaries using semantic similarity.
    
    Args:
        query: Text to search for
        limit: Maximum number of results (default: 5)
        summary_type: Filter by summary type (optional)
    """
    try:
        vector_store = await get_vector_store()
        results = await vector_store.search_similar_summaries(
            query_text=query,
            limit=limit,
            summary_type=summary_type
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error("Failed to search summaries", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to search summaries")


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns the health status of the application and its dependencies.
    """
    services = {}
    
    # Check Celery
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            services["celery"] = "healthy"
        else:
            services["celery"] = "no_workers"
    except Exception:
        services["celery"] = "unhealthy"
    
    # Check Vector Store
    try:
        vector_store = await get_vector_store()
        health = await vector_store.health_check()
        services["vector_store"] = health.get("status", "unknown")
    except Exception:
        services["vector_store"] = "unhealthy"
    
    # Check Ollama (through a simple health task)
    try:
        # This would require a health check task to be implemented
        services["ollama"] = "unknown"  # Placeholder
    except Exception:
        services["ollama"] = "unhealthy"
    
    # Determine overall status
    unhealthy_services = [k for k, v in services.items() if v == "unhealthy"]
    overall_status = "unhealthy" if unhealthy_services else "healthy"
    
    return HealthResponse(
        status=overall_status,
        version=settings.api_version,
        services=services
    )


@app.get("/stats")
async def get_stats():
    """Get application statistics."""
    try:
        vector_store = await get_vector_store()
        stats = await vector_store.get_collection_stats()
        
        # Add Celery stats
        inspect = celery_app.control.inspect()
        celery_stats = {
            "active_tasks": len(inspect.active() or {}),
            "scheduled_tasks": len(inspect.scheduled() or {}),
            "reserved_tasks": len(inspect.reserved() or {}),
        }
        
        return {
            "vector_store": stats,
            "celery": celery_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "transcript_summarizer.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
