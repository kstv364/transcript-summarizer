"""Tests for the core summarization functionality."""

import pytest
from unittest.mock import patch, AsyncMock
from transcript_summarizer.core.summarizer import TranscriptSummarizer, create_summarizer
from transcript_summarizer.models.schemas import SummaryType


class TestTranscriptSummarizer:
    """Test cases for TranscriptSummarizer class."""

    @pytest.fixture
    def summarizer(self, mock_ollama_llm):
        """Create a summarizer instance with mocked LLM."""
        with patch('transcript_summarizer.core.summarizer.OllamaLLM') as mock_llm_class:
            mock_llm_class.return_value = mock_ollama_llm
            return TranscriptSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_short_transcript(self, summarizer, sample_transcript, mock_ollama_llm):
        """Test summarization of a short transcript (single chunk)."""
        result = await summarizer.summarize_transcript(sample_transcript, "comprehensive")
        
        assert result.summary == "This is a test summary of the transcript."
        assert result.original_length == len(sample_transcript)
        assert result.chunk_count == 1
        assert result.compression_ratio > 0
        assert result.summary_type == "comprehensive"
        
        # Verify LLM was called once
        mock_ollama_llm.invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarize_long_transcript(self, summarizer, sample_long_transcript, mock_ollama_llm):
        """Test summarization of a long transcript (multiple chunks)."""
        # Mock multiple calls for map-reduce
        mock_ollama_llm.invoke.side_effect = [
            "Summary of chunk 1",
            "Summary of chunk 2", 
            "Summary of chunk 3",
            "Final combined summary"
        ]
        
        result = await summarizer.summarize_transcript(sample_long_transcript, "comprehensive")
        
        assert result.summary == "Final combined summary"
        assert result.original_length == len(sample_long_transcript)
        assert result.chunk_count > 1
        assert result.compression_ratio > 0
        assert result.summary_type == "comprehensive"
        
        # Verify LLM was called multiple times (chunks + final)
        assert mock_ollama_llm.invoke.call_count > 2

    @pytest.mark.asyncio
    async def test_different_summary_types(self, summarizer, sample_transcript, mock_ollama_llm):
        """Test different summary types."""
        summary_types = ["comprehensive", "brief", "key_points"]
        
        for summary_type in summary_types:
            mock_ollama_llm.reset_mock()
            result = await summarizer.summarize_transcript(sample_transcript, summary_type)
            
            assert result.summary_type == summary_type
            assert result.summary == "This is a test summary of the transcript."
            mock_ollama_llm.invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_text_handling(self, summarizer):
        """Test handling of empty or whitespace-only text."""
        with pytest.raises(Exception):
            await summarizer.summarize_transcript("", "comprehensive")
        
        with pytest.raises(Exception):
            await summarizer.summarize_transcript("   \n  \t  ", "comprehensive")

    @pytest.mark.asyncio
    async def test_create_summarizer_factory(self):
        """Test the factory function for creating summarizer."""
        with patch('transcript_summarizer.core.summarizer.OllamaLLM'):
            summarizer = await create_summarizer()
            assert isinstance(summarizer, TranscriptSummarizer)

    def test_text_splitting(self, summarizer, sample_long_transcript):
        """Test text splitting into chunks."""
        documents = summarizer._create_documents(sample_long_transcript)
        
        assert len(documents) > 1
        
        # Check that chunks have reasonable sizes
        for doc in documents:
            assert len(doc.page_content) <= summarizer.settings.chunk_size + 500  # Allow for overlap

    def test_prompt_generation(self, summarizer):
        """Test prompt template generation for different summary types."""
        summary_types = ["comprehensive", "brief", "key_points"]
        
        for summary_type in summary_types:
            # Test single chunk prompt
            prompt = summarizer._get_summary_prompt(summary_type)
            assert prompt.template is not None
            assert "{text}" in prompt.template
            
            # Test map prompt
            map_prompt = summarizer._get_map_prompt(summary_type)
            assert map_prompt.template is not None
            assert "{text}" in map_prompt.template
            
            # Test reduce prompt
            reduce_prompt = summarizer._get_reduce_prompt(summary_type)
            assert reduce_prompt.template is not None
            assert "{summaries}" in reduce_prompt.template

    @pytest.mark.asyncio
    async def test_error_handling(self, summarizer, sample_transcript, mock_ollama_llm):
        """Test error handling in summarization."""
        # Mock LLM to raise an exception
        mock_ollama_llm.invoke.side_effect = Exception("LLM Error")
        
        with pytest.raises(Exception) as exc_info:
            await summarizer.summarize_transcript(sample_transcript, "comprehensive")
        
        assert "LLM Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_compression_ratio_calculation(self, summarizer, sample_transcript, mock_ollama_llm):
        """Test compression ratio calculation."""
        # Use a shorter mock summary to test compression ratio
        mock_ollama_llm.invoke.return_value = "Short summary."
        
        result = await summarizer.summarize_transcript(sample_transcript, "comprehensive")
        
        expected_ratio = len(sample_transcript) / len("Short summary.")
        assert abs(result.compression_ratio - expected_ratio) < 0.01
