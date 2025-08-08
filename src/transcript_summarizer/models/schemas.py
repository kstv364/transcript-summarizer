"""Pydantic models for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class SummaryType(str, Enum):
    """Types of summaries that can be generated."""
    COMPREHENSIVE = "comprehensive"
    BRIEF = "brief"
    KEY_POINTS = "key_points"


class TaskStatus(str, Enum):
    """Status of a summarization task."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SummarizationRequest(BaseModel):
    """Request model for transcript summarization."""
    
    text: str = Field(
        ...,
        min_length=10,
        max_length=1000000,
        description="The transcript text to summarize"
    )
    
    summary_type: SummaryType = Field(
        default=SummaryType.COMPREHENSIVE,
        description="Type of summary to generate"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional metadata about the transcript"
    )

    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty or only whitespace")
        return v.strip()


class SummarizationResponse(BaseModel):
    """Response model for summarization request."""
    
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    message: str = Field(..., description="Status message")
    estimated_completion_time: Optional[int] = Field(
        None, 
        description="Estimated completion time in seconds"
    )


class SummarizationResult(BaseModel):
    """Result model containing the summary and metadata."""
    
    summary: str = Field(..., description="The generated summary")
    original_length: int = Field(..., description="Length of original text")
    summary_length: int = Field(..., description="Length of summary")
    compression_ratio: float = Field(..., description="Compression ratio (original/summary)")
    chunk_count: int = Field(..., description="Number of chunks processed")
    summary_type: str = Field(..., description="Type of summary generated")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskStatusResponse(BaseModel):
    """Response model for task status check."""
    
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    result: Optional[SummarizationResult] = Field(None, description="Result if completed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="Application version")
    services: Dict[str, str] = Field(..., description="Service status")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
