"""Vector storage using ChromaDB for transcript and summary storage."""

import uuid
from typing import List, Optional, Dict, Any
import structlog
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain.schema import Document

from ..config.settings import get_settings
from ..models.schemas import SummarizationResult

logger = structlog.get_logger(__name__)


class VectorStore:
    """ChromaDB-based vector store for transcripts and summaries."""

    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.collection = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Configure ChromaDB client
            chroma_settings = ChromaSettings(
                chroma_server_host=self.settings.chroma_host,
                chroma_server_http_port=self.settings.chroma_port,
                chroma_api_impl="rest",
            )
            
            self.client = chromadb.HttpClient(
                host=self.settings.chroma_host,
                port=self.settings.chroma_port,
                settings=chroma_settings
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=self.settings.chroma_collection_name
                )
                logger.info("Connected to existing ChromaDB collection")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.settings.chroma_collection_name,
                    metadata={"description": "Transcript summaries and related documents"}
                )
                logger.info("Created new ChromaDB collection")
                
        except Exception as e:
            logger.error("Failed to initialize ChromaDB", error=str(e))
            raise

    async def store_summary(
        self, 
        task_id: str, 
        original_text: str, 
        result: SummarizationResult
    ) -> str:
        """
        Store a summarization result in the vector database.
        
        Args:
            task_id: Unique task identifier
            original_text: Original transcript text
            result: Summarization result
            
        Returns:
            Document ID in the vector store
        """
        try:
            doc_id = f"summary_{task_id}"
            
            metadata = {
                "task_id": task_id,
                "summary_type": result.summary_type,
                "original_length": result.original_length,
                "summary_length": result.summary_length,
                "compression_ratio": result.compression_ratio,
                "chunk_count": result.chunk_count,
                "created_at": result.created_at.isoformat(),
                "document_type": "summary"
            }
            
            if result.processing_time:
                metadata["processing_time"] = result.processing_time
            
            # Store the summary with metadata
            self.collection.add(
                documents=[result.summary],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            # Also store the original text for reference
            original_doc_id = f"original_{task_id}"
            original_metadata = {
                "task_id": task_id,
                "document_type": "original",
                "text_length": len(original_text),
                "created_at": result.created_at.isoformat(),
                "related_summary_id": doc_id
            }
            
            self.collection.add(
                documents=[original_text],
                metadatas=[original_metadata],
                ids=[original_doc_id]
            )
            
            logger.info("Stored summary in vector database", 
                       task_id=task_id, doc_id=doc_id)
            
            return doc_id
            
        except Exception as e:
            logger.error("Failed to store summary", task_id=task_id, error=str(e))
            raise

    async def get_summary(self, task_id: str) -> Optional[SummarizationResult]:
        """
        Retrieve a summary by task ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            SummarizationResult if found, None otherwise
        """
        try:
            doc_id = f"summary_{task_id}"
            
            results = self.collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            
            if not results["ids"]:
                return None
            
            document = results["documents"][0]
            metadata = results["metadatas"][0]
            
            # Reconstruct SummarizationResult
            result = SummarizationResult(
                summary=document,
                original_length=metadata["original_length"],
                summary_length=metadata["summary_length"],
                compression_ratio=metadata["compression_ratio"],
                chunk_count=metadata["chunk_count"],
                summary_type=metadata["summary_type"],
                processing_time=metadata.get("processing_time"),
                created_at=metadata["created_at"]
            )
            
            return result
            
        except Exception as e:
            logger.error("Failed to retrieve summary", task_id=task_id, error=str(e))
            return None

    async def search_similar_summaries(
        self, 
        query_text: str, 
        limit: int = 5,
        summary_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar summaries using semantic similarity.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results
            summary_type: Filter by summary type
            
        Returns:
            List of similar summaries with metadata
        """
        try:
            where_clause = {"document_type": "summary"}
            if summary_type:
                where_clause["summary_type"] = summary_type
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=limit,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            similar_summaries = []
            for i, doc_id in enumerate(results["ids"][0]):
                similar_summaries.append({
                    "id": doc_id,
                    "summary": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                })
            
            logger.info("Found similar summaries", count=len(similar_summaries))
            return similar_summaries
            
        except Exception as e:
            logger.error("Failed to search similar summaries", error=str(e))
            return []

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            count = self.collection.count()
            
            # Get sample of metadata to analyze
            sample_results = self.collection.get(
                limit=min(100, count),
                include=["metadatas"]
            )
            
            stats = {
                "total_documents": count,
                "summary_count": 0,
                "original_count": 0,
                "summary_types": {},
            }
            
            for metadata in sample_results["metadatas"]:
                doc_type = metadata.get("document_type", "unknown")
                if doc_type == "summary":
                    stats["summary_count"] += 1
                    summary_type = metadata.get("summary_type", "unknown")
                    stats["summary_types"][summary_type] = stats["summary_types"].get(summary_type, 0) + 1
                elif doc_type == "original":
                    stats["original_count"] += 1
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            return {"error": str(e)}

    async def delete_summary(self, task_id: str) -> bool:
        """
        Delete a summary and its original text from the store.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            doc_ids = [f"summary_{task_id}", f"original_{task_id}"]
            
            # Check if documents exist
            existing = self.collection.get(ids=doc_ids)
            
            if existing["ids"]:
                self.collection.delete(ids=existing["ids"])
                logger.info("Deleted summary from vector store", task_id=task_id)
                return True
            else:
                logger.warning("Summary not found for deletion", task_id=task_id)
                return False
                
        except Exception as e:
            logger.error("Failed to delete summary", task_id=task_id, error=str(e))
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the ChromaDB connection."""
        try:
            # Try to get collection info
            count = self.collection.count()
            return {
                "status": "healthy",
                "collection_name": self.settings.chroma_collection_name,
                "document_count": count,
                "host": self.settings.chroma_host,
                "port": self.settings.chroma_port
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "host": self.settings.chroma_host,
                "port": self.settings.chroma_port
            }


# Global instance
_vector_store_instance = None


async def get_vector_store() -> VectorStore:
    """Get or create a vector store instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
