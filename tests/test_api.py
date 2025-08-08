"""Tests for the FastAPI application."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from transcript_summarizer.models.schemas import SummarizationRequest, TaskStatus


class TestAPI:
    """Test cases for FastAPI application."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        with patch('transcript_summarizer.api.celery_app') as mock_celery, \
             patch('transcript_summarizer.api.get_vector_store') as mock_get_store:
            
            # Mock Celery health check
            mock_inspect = MagicMock()
            mock_inspect.active.return_value = {"worker1": []}
            mock_celery.control.inspect.return_value = mock_inspect
            
            # Mock vector store health check
            mock_store = AsyncMock()
            mock_store.health_check.return_value = {"status": "healthy"}
            mock_get_store.return_value = mock_store
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "services" in data
            assert "version" in data

    def test_summarize_endpoint_success(self, client, sample_transcript):
        """Test successful transcript summarization request."""
        with patch('transcript_summarizer.api.celery_app') as mock_celery:
            # Mock Celery task
            mock_task = MagicMock()
            mock_task.id = "test-task-123"
            mock_celery.send_task.return_value = mock_task
            
            request_data = {
                "text": sample_transcript,
                "summary_type": "comprehensive"
            }
            
            response = client.post("/summarize", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["task_id"] == "test-task-123"
            assert data["status"] == "pending"
            assert "estimated_completion_time" in data

    def test_summarize_endpoint_text_too_long(self, client):
        """Test summarization with text that exceeds maximum length."""
        long_text = "a" * 1000001  # Exceed default max length
        
        request_data = {
            "text": long_text,
            "summary_type": "comprehensive"
        }
        
        response = client.post("/summarize", json=request_data)
        assert response.status_code == 413
        assert "too long" in response.json()["detail"].lower()

    def test_summarize_endpoint_empty_text(self, client):
        """Test summarization with empty text."""
        request_data = {
            "text": "",
            "summary_type": "comprehensive"
        }
        
        response = client.post("/summarize", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_summarize_endpoint_invalid_summary_type(self, client, sample_transcript):
        """Test summarization with invalid summary type."""
        request_data = {
            "text": sample_transcript,
            "summary_type": "invalid_type"
        }
        
        response = client.post("/summarize", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_get_task_status_pending(self, client):
        """Test getting status of a pending task."""
        with patch('transcript_summarizer.api.celery_app') as mock_celery:
            # Mock pending task
            mock_result = MagicMock()
            mock_result.state = "PENDING"
            mock_result.info = None
            mock_celery.AsyncResult.return_value = mock_result
            
            response = client.get("/status/test-task-123")
            assert response.status_code == 200
            
            data = response.json()
            assert data["task_id"] == "test-task-123"
            assert data["status"] == "pending"
            assert data["progress"] is None

    def test_get_task_status_processing(self, client):
        """Test getting status of a processing task."""
        with patch('transcript_summarizer.api.celery_app') as mock_celery:
            # Mock processing task
            mock_result = MagicMock()
            mock_result.state = "PROCESSING"
            mock_result.info = {"progress": 50, "message": "Processing..."}
            mock_celery.AsyncResult.return_value = mock_result
            
            response = client.get("/status/test-task-123")
            assert response.status_code == 200
            
            data = response.json()
            assert data["task_id"] == "test-task-123"
            assert data["status"] == "processing"
            assert data["progress"] == 50

    def test_get_task_status_completed(self, client):
        """Test getting status of a completed task."""
        with patch('transcript_summarizer.api.celery_app') as mock_celery:
            # Mock completed task
            mock_result = MagicMock()
            mock_result.state = "SUCCESS"
            mock_result.result = {
                "summary": "Test summary",
                "original_length": 1000,
                "summary_length": 100,
                "compression_ratio": 10.0,
                "chunk_count": 1,
                "summary_type": "comprehensive",
                "processing_time": 5.0,
                "created_at": "2023-01-01T00:00:00"
            }
            mock_celery.AsyncResult.return_value = mock_result
            
            response = client.get("/status/test-task-123")
            assert response.status_code == 200
            
            data = response.json()
            assert data["task_id"] == "test-task-123"
            assert data["status"] == "completed"
            assert data["progress"] == 100
            assert data["result"] is not None

    def test_get_task_status_failed(self, client):
        """Test getting status of a failed task."""
        with patch('transcript_summarizer.api.celery_app') as mock_celery:
            # Mock failed task
            mock_result = MagicMock()
            mock_result.state = "FAILURE"
            mock_result.info = "Task failed due to error"
            mock_celery.AsyncResult.return_value = mock_result
            
            response = client.get("/status/test-task-123")
            assert response.status_code == 200
            
            data = response.json()
            assert data["task_id"] == "test-task-123"
            assert data["status"] == "failed"
            assert data["error_message"] == "Task failed due to error"

    def test_get_summary_success(self, client):
        """Test getting a completed summary."""
        with patch('transcript_summarizer.api.celery_app') as mock_celery:
            # Mock successful task result
            mock_result = MagicMock()
            mock_result.state = "SUCCESS"
            mock_result.result = {
                "summary": "Test summary",
                "original_length": 1000,
                "summary_length": 100,
                "compression_ratio": 10.0,
                "chunk_count": 1,
                "summary_type": "comprehensive",
                "processing_time": 5.0,
                "created_at": "2023-01-01T00:00:00"
            }
            mock_celery.AsyncResult.return_value = mock_result
            
            response = client.get("/summary/test-task-123")
            assert response.status_code == 200
            
            data = response.json()
            assert data["summary"] == "Test summary"
            assert data["original_length"] == 1000

    def test_get_summary_not_ready(self, client):
        """Test getting summary for a task that's still processing."""
        with patch('transcript_summarizer.api.celery_app') as mock_celery:
            # Mock processing task
            mock_result = MagicMock()
            mock_result.state = "PROCESSING"
            mock_result.result = None
            mock_celery.AsyncResult.return_value = mock_result
            
            response = client.get("/summary/test-task-123")
            assert response.status_code == 202  # Accepted, still processing

    def test_get_summary_not_found(self, client):
        """Test getting summary for a non-existent task."""
        with patch('transcript_summarizer.api.celery_app') as mock_celery, \
             patch('transcript_summarizer.api.get_vector_store') as mock_get_store:
            
            # Mock task not found in Celery
            mock_result = MagicMock()
            mock_result.state = "PENDING"
            mock_result.result = None
            mock_celery.AsyncResult.return_value = mock_result
            
            # Mock not found in vector store
            mock_store = AsyncMock()
            mock_store.get_summary.return_value = None
            mock_get_store.return_value = mock_store
            
            response = client.get("/summary/non-existent-task")
            assert response.status_code == 404

    def test_search_summaries(self, client):
        """Test searching for similar summaries."""
        with patch('transcript_summarizer.api.get_vector_store') as mock_get_store:
            mock_store = AsyncMock()
            mock_store.search_similar_summaries.return_value = [
                {
                    "id": "summary_123",
                    "summary": "Similar summary",
                    "metadata": {"summary_type": "comprehensive"},
                    "similarity_score": 0.85
                }
            ]
            mock_get_store.return_value = mock_store
            
            response = client.get("/search?query=test query&limit=5")
            assert response.status_code == 200
            
            data = response.json()
            assert data["query"] == "test query"
            assert len(data["results"]) == 1
            assert data["count"] == 1

    def test_get_stats(self, client):
        """Test getting application statistics."""
        with patch('transcript_summarizer.api.get_vector_store') as mock_get_store, \
             patch('transcript_summarizer.api.celery_app') as mock_celery:
            
            # Mock vector store stats
            mock_store = AsyncMock()
            mock_store.get_collection_stats.return_value = {
                "total_documents": 100,
                "summary_count": 50
            }
            mock_get_store.return_value = mock_store
            
            # Mock Celery stats
            mock_inspect = MagicMock()
            mock_inspect.active.return_value = {"worker1": []}
            mock_inspect.scheduled.return_value = {}
            mock_inspect.reserved.return_value = {}
            mock_celery.control.inspect.return_value = mock_inspect
            
            response = client.get("/stats")
            assert response.status_code == 200
            
            data = response.json()
            assert "vector_store" in data
            assert "celery" in data
            assert "timestamp" in data

    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/health")
        assert response.status_code == 200
