"""Tests for the vector store functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from transcript_summarizer.storage.vector_store import VectorStore, get_vector_store
from transcript_summarizer.models.schemas import SummarizationResult
from datetime import datetime


class TestVectorStore:
    """Test cases for VectorStore class."""

    @pytest.fixture
    def mock_chromadb_client(self):
        """Mock ChromaDB client."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        mock_client.create_collection.return_value = mock_collection
        return mock_client, mock_collection

    @pytest.fixture
    def vector_store(self, mock_chromadb_client):
        """Create VectorStore instance with mocked ChromaDB."""
        mock_client, mock_collection = mock_chromadb_client
        
        with patch('transcript_summarizer.storage.vector_store.chromadb.HttpClient') as mock_http_client:
            mock_http_client.return_value = mock_client
            store = VectorStore()
            store.collection = mock_collection
            return store

    @pytest.fixture
    def sample_result(self):
        """Sample summarization result."""
        return SummarizationResult(
            summary="This is a test summary.",
            original_length=1000,
            summary_length=100,
            compression_ratio=10.0,
            chunk_count=1,
            summary_type="comprehensive",
            processing_time=5.0,
            created_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_store_summary(self, vector_store, sample_result):
        """Test storing a summary in the vector store."""
        task_id = "test-task-123"
        original_text = "This is the original transcript text."
        
        doc_id = await vector_store.store_summary(task_id, original_text, sample_result)
        
        assert doc_id == f"summary_{task_id}"
        
        # Verify collection.add was called twice (summary + original)
        assert vector_store.collection.add.call_count == 2

    @pytest.mark.asyncio
    async def test_get_summary_found(self, vector_store, sample_result):
        """Test retrieving an existing summary."""
        task_id = "test-task-123"
        
        # Mock ChromaDB response
        vector_store.collection.get.return_value = {
            "ids": [f"summary_{task_id}"],
            "documents": [sample_result.summary],
            "metadatas": [{
                "task_id": task_id,
                "summary_type": sample_result.summary_type,
                "original_length": sample_result.original_length,
                "summary_length": sample_result.summary_length,
                "compression_ratio": sample_result.compression_ratio,
                "chunk_count": sample_result.chunk_count,
                "created_at": sample_result.created_at.isoformat(),
                "processing_time": sample_result.processing_time
            }]
        }
        
        result = await vector_store.get_summary(task_id)
        
        assert result is not None
        assert result.summary == sample_result.summary
        assert result.original_length == sample_result.original_length
        assert result.summary_type == sample_result.summary_type

    @pytest.mark.asyncio
    async def test_get_summary_not_found(self, vector_store):
        """Test retrieving a non-existent summary."""
        task_id = "non-existent-task"
        
        # Mock ChromaDB response for not found
        vector_store.collection.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": []
        }
        
        result = await vector_store.get_summary(task_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_search_similar_summaries(self, vector_store):
        """Test searching for similar summaries."""
        query_text = "quarterly results and financial performance"
        
        # Mock ChromaDB query response
        vector_store.collection.query.return_value = {
            "ids": [["summary_1", "summary_2"]],
            "documents": [["Summary 1 text", "Summary 2 text"]],
            "metadatas": [[
                {"task_id": "task_1", "summary_type": "comprehensive"},
                {"task_id": "task_2", "summary_type": "brief"}
            ]],
            "distances": [[0.2, 0.3]]
        }
        
        results = await vector_store.search_similar_summaries(query_text, limit=5)
        
        assert len(results) == 2
        assert results[0]["similarity_score"] == 0.8  # 1 - 0.2
        assert results[1]["similarity_score"] == 0.7  # 1 - 0.3
        assert results[0]["summary"] == "Summary 1 text"

    @pytest.mark.asyncio
    async def test_search_similar_summaries_with_filter(self, vector_store):
        """Test searching with summary type filter."""
        query_text = "test query"
        summary_type = "comprehensive"
        
        vector_store.collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        
        await vector_store.search_similar_summaries(
            query_text, 
            limit=5, 
            summary_type=summary_type
        )
        
        # Verify that the where clause includes summary_type filter
        call_args = vector_store.collection.query.call_args
        where_clause = call_args[1]["where"]
        assert where_clause["summary_type"] == summary_type

    @pytest.mark.asyncio
    async def test_get_collection_stats(self, vector_store):
        """Test getting collection statistics."""
        # Mock collection count
        vector_store.collection.count.return_value = 100
        
        # Mock get response for metadata analysis
        vector_store.collection.get.return_value = {
            "metadatas": [
                {"document_type": "summary", "summary_type": "comprehensive"},
                {"document_type": "summary", "summary_type": "brief"},
                {"document_type": "original"},
                {"document_type": "summary", "summary_type": "comprehensive"}
            ]
        }
        
        stats = await vector_store.get_collection_stats()
        
        assert stats["total_documents"] == 100
        assert stats["summary_count"] == 3
        assert stats["original_count"] == 1
        assert stats["summary_types"]["comprehensive"] == 2
        assert stats["summary_types"]["brief"] == 1

    @pytest.mark.asyncio
    async def test_delete_summary(self, vector_store):
        """Test deleting a summary."""
        task_id = "test-task-123"
        
        # Mock existing documents
        vector_store.collection.get.return_value = {
            "ids": [f"summary_{task_id}", f"original_{task_id}"]
        }
        
        result = await vector_store.delete_summary(task_id)
        
        assert result is True
        vector_store.collection.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_summary_not_found(self, vector_store):
        """Test deleting a non-existent summary."""
        task_id = "non-existent-task"
        
        # Mock no documents found
        vector_store.collection.get.return_value = {"ids": []}
        
        result = await vector_store.delete_summary(task_id)
        
        assert result is False
        vector_store.collection.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, vector_store):
        """Test health check when service is healthy."""
        vector_store.collection.count.return_value = 50
        
        health = await vector_store.health_check()
        
        assert health["status"] == "healthy"
        assert health["document_count"] == 50
        assert "collection_name" in health

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, vector_store):
        """Test health check when service is unhealthy."""
        vector_store.collection.count.side_effect = Exception("Connection failed")
        
        health = await vector_store.health_check()
        
        assert health["status"] == "unhealthy"
        assert "error" in health

    @pytest.mark.asyncio
    async def test_get_vector_store_singleton(self):
        """Test that get_vector_store returns the same instance."""
        with patch('transcript_summarizer.storage.vector_store.VectorStore') as mock_vector_store_class:
            mock_instance = MagicMock()
            mock_vector_store_class.return_value = mock_instance
            
            # Clear the global instance
            import transcript_summarizer.storage.vector_store as vs_module
            vs_module._vector_store_instance = None
            
            store1 = await get_vector_store()
            store2 = await get_vector_store()
            
            assert store1 is store2
            mock_vector_store_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_summary_error_handling(self, vector_store, sample_result):
        """Test error handling when storing summary fails."""
        task_id = "test-task-123"
        original_text = "Test text"
        
        # Mock ChromaDB to raise an exception
        vector_store.collection.add.side_effect = Exception("Storage failed")
        
        with pytest.raises(Exception) as exc_info:
            await vector_store.store_summary(task_id, original_text, sample_result)
        
        assert "Storage failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_error_handling(self, vector_store):
        """Test error handling when search fails."""
        vector_store.collection.query.side_effect = Exception("Query failed")
        
        results = await vector_store.search_similar_summaries("test query")
        
        # Should return empty list on error
        assert results == []
