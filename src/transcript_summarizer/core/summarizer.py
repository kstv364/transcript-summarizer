"""Core summarization logic using LangChain and Ollama."""

import asyncio
from typing import List, Optional
import structlog
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaLLM
from langchain.chains.summarize import load_summarize_chain
from langchain.schema import Document
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate

from ..config.settings import get_settings
from ..models.schemas import SummarizationResult

logger = structlog.get_logger(__name__)


class TranscriptSummarizer:
    """Main summarizer class that handles long transcripts using chunking strategies."""

    def __init__(self):
        self.settings = get_settings()
        self.llm = OllamaLLM(
            base_url=self.settings.ollama_base_url,
            model=self.settings.ollama_model,
            temperature=0.1,
            num_predict=2048,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        
    async def summarize_transcript(
        self, 
        text: str, 
        summary_type: str = "comprehensive"
    ) -> SummarizationResult:
        """
        Summarize a transcript using map-reduce strategy for long texts.
        
        Args:
            text: The transcript text to summarize
            summary_type: Type of summary (comprehensive, brief, key_points)
            
        Returns:
            SummarizationResult with the summary and metadata
        """
        logger.info("Starting transcript summarization", 
                   text_length=len(text), summary_type=summary_type)
        
        try:
            # Split text into chunks
            documents = self._create_documents(text)
            
            if len(documents) == 1:
                # Single chunk - direct summarization
                summary = await self._summarize_single_chunk(documents[0], summary_type)
            else:
                # Multiple chunks - map-reduce strategy
                summary = await self._summarize_multiple_chunks(documents, summary_type)
            
            result = SummarizationResult(
                summary=summary,
                original_length=len(text),
                summary_length=len(summary),
                compression_ratio=len(text) / len(summary) if summary else 0,
                chunk_count=len(documents),
                summary_type=summary_type
            )
            
            logger.info("Summarization completed", 
                       chunk_count=len(documents),
                       compression_ratio=result.compression_ratio)
            
            return result
            
        except Exception as e:
            logger.error("Summarization failed", error=str(e))
            raise

    def _create_documents(self, text: str) -> List[Document]:
        """Split text into documents."""
        texts = self.text_splitter.split_text(text)
        return [Document(page_content=text) for text in texts]

    async def _summarize_single_chunk(self, document: Document, summary_type: str) -> str:
        """Summarize a single chunk directly."""
        prompt = self._get_summary_prompt(summary_type)
        
        # Run LLM call in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        summary = await loop.run_in_executor(
            None, 
            lambda: self.llm.invoke(prompt.format(text=document.page_content))
        )
        
        return summary.strip()

    async def _summarize_multiple_chunks(self, documents: List[Document], summary_type: str) -> str:
        """Summarize multiple chunks using map-reduce strategy."""
        # Step 1: Map - Summarize each chunk
        chunk_summaries = []
        map_prompt = self._get_map_prompt(summary_type)
        
        loop = asyncio.get_event_loop()
        
        # Process chunks in batches to avoid overwhelming the model
        batch_size = 3
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_tasks = []
            
            for doc in batch:
                task = loop.run_in_executor(
                    None,
                    lambda d=doc: self.llm.invoke(map_prompt.format(text=d.page_content))
                )
                batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks)
            chunk_summaries.extend([result.strip() for result in batch_results])
            
            # Small delay between batches to be nice to the model
            await asyncio.sleep(0.5)
        
        # Step 2: Reduce - Combine all chunk summaries
        combined_summaries = "\n\n".join(chunk_summaries)
        reduce_prompt = self._get_reduce_prompt(summary_type)
        
        final_summary = await loop.run_in_executor(
            None,
            lambda: self.llm.invoke(reduce_prompt.format(summaries=combined_summaries))
        )
        
        return final_summary.strip()

    def _get_summary_prompt(self, summary_type: str) -> PromptTemplate:
        """Get prompt template for single chunk summarization."""
        templates = {
            "comprehensive": """
Please provide a comprehensive summary of the following transcript. Include all key points, important details, and main themes discussed.

Transcript:
{text}

Comprehensive Summary:""",
            
            "brief": """
Please provide a brief, concise summary of the following transcript. Focus on the most important points only.

Transcript:
{text}

Brief Summary:""",
            
            "key_points": """
Please extract the key points from the following transcript and present them as a bulleted list.

Transcript:
{text}

Key Points:
•""",
        }
        
        template = templates.get(summary_type, templates["comprehensive"])
        return PromptTemplate(template=template, input_variables=["text"])

    def _get_map_prompt(self, summary_type: str) -> PromptTemplate:
        """Get prompt template for map phase (chunk summarization)."""
        templates = {
            "comprehensive": """
Summarize this section of a transcript, preserving all important information and context:

Section:
{text}

Section Summary:""",
            
            "brief": """
Briefly summarize this section of a transcript, focusing only on the most important points:

Section:
{text}

Brief Section Summary:""",
            
            "key_points": """
Extract the key points from this section of a transcript:

Section:
{text}

Key Points from this section:
•""",
        }
        
        template = templates.get(summary_type, templates["comprehensive"])
        return PromptTemplate(template=template, input_variables=["text"])

    def _get_reduce_prompt(self, summary_type: str) -> PromptTemplate:
        """Get prompt template for reduce phase (combining summaries)."""
        templates = {
            "comprehensive": """
Combine the following section summaries into one comprehensive, coherent summary of the entire transcript. Ensure all important information is preserved and well-organized.

Section Summaries:
{summaries}

Final Comprehensive Summary:""",
            
            "brief": """
Combine the following section summaries into one brief, coherent summary of the entire transcript.

Section Summaries:
{summaries}

Final Brief Summary:""",
            
            "key_points": """
Combine and organize the following key points from different sections into a comprehensive list of key points for the entire transcript. Remove duplicates and organize logically.

Key Points from Sections:
{summaries}

Final Key Points:
•""",
        }
        
        template = templates.get(summary_type, templates["comprehensive"])
        return PromptTemplate(template=template, input_variables=["summaries"])


async def create_summarizer() -> TranscriptSummarizer:
    """Factory function to create a summarizer instance."""
    return TranscriptSummarizer()
