"""Transcript Summarizer Package."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.summarizer import TranscriptSummarizer
from .models.schemas import SummarizationRequest, SummarizationResponse

__all__ = [
    "TranscriptSummarizer",
    "SummarizationRequest",
    "SummarizationResponse",
]
