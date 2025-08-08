"""Transcript Summarizer Package."""

__version__ = "0.1.0"
__author__ = "kstv364"
__email__ = "kstv364@example.com"

from .core.summarizer import TranscriptSummarizer
from .models.schemas import SummarizationRequest, SummarizationResponse

__all__ = [
    "TranscriptSummarizer",
    "SummarizationRequest",
    "SummarizationResponse",
]
