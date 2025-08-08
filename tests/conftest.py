"""Test configuration and fixtures."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from transcript_summarizer.config.settings import get_settings
from transcript_summarizer.api import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings():
    """Get test settings."""
    test_settings = get_settings()
    test_settings.testing = True
    test_settings.redis_url = "redis://localhost:6379/1"  # Test database
    test_settings.chroma_host = "localhost"
    test_settings.chroma_port = 8001  # Test port
    test_settings.ollama_base_url = "http://localhost:11434"
    test_settings.log_level = "DEBUG"
    return test_settings


@pytest.fixture
def client():
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_ollama_llm():
    """Mock Ollama LLM for testing."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "This is a test summary of the transcript."
    return mock_llm


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    mock_store = AsyncMock()
    mock_store.store_summary.return_value = "doc_123"
    mock_store.get_summary.return_value = None
    mock_store.search_similar_summaries.return_value = []
    mock_store.health_check.return_value = {"status": "healthy"}
    return mock_store


@pytest.fixture
def sample_transcript():
    """Sample transcript for testing."""
    return """
    Welcome to today's meeting. We'll be discussing the quarterly results and future plans.
    
    First, let's look at our revenue numbers. This quarter we achieved $2.5 million in revenue,
    which represents a 15% increase from the previous quarter. Our main growth drivers were
    the new product line and expanded market presence.
    
    Looking at expenses, we managed to keep operational costs stable while investing heavily
    in R&D. The R&D investment of $500,000 this quarter will help us launch three new
    products next quarter.
    
    Our customer satisfaction scores improved to 4.2 out of 5, up from 3.8 last quarter.
    This improvement is attributed to better customer service and product quality enhancements.
    
    For next quarter, we're planning to expand into two new markets and hire 10 additional
    team members. We expect this expansion to drive another 20% revenue growth.
    
    Any questions about these results?
    """


@pytest.fixture
def sample_long_transcript():
    """Long transcript for testing chunking."""
    base_text = """
    This is a section of a very long transcript that needs to be processed in chunks.
    It contains important information about various topics including business operations,
    technical specifications, customer feedback, and strategic planning initiatives.
    
    The transcript discusses multiple aspects of the organization including:
    - Financial performance and metrics
    - Operational efficiency improvements
    - Technology infrastructure updates
    - Human resources and talent acquisition
    - Market expansion opportunities
    - Customer satisfaction and feedback
    - Product development roadmaps
    - Competitive analysis and positioning
    
    Each section provides detailed insights and actionable recommendations for stakeholders.
    """
    
    # Repeat the base text to create a long transcript
    return (base_text + "\n") * 50  # Creates a ~25KB transcript
