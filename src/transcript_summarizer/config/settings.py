"""Application settings and configuration."""

import os
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        env="OLLAMA_BASE_URL",
        description="Base URL for Ollama API"
    )
    
    ollama_model: str = Field(
        default="llama3",
        env="OLLAMA_MODEL", 
        description="Ollama model name to use"
    )
    
    # Text Processing Configuration
    chunk_size: int = Field(
        default=4000,
        env="CHUNK_SIZE",
        description="Size of text chunks for processing"
    )
    
    chunk_overlap: int = Field(
        default=200,
        env="CHUNK_OVERLAP",
        description="Overlap between text chunks"
    )
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="Redis connection URL"
    )
    
    # ChromaDB Configuration
    chroma_host: str = Field(
        default="localhost",
        env="CHROMA_HOST",
        description="ChromaDB host"
    )
    
    chroma_port: int = Field(
        default=8000,
        env="CHROMA_PORT",
        description="ChromaDB port"
    )
    
    chroma_collection_name: str = Field(
        default="transcripts",
        env="CHROMA_COLLECTION_NAME",
        description="ChromaDB collection name"
    )
    
    # API Configuration
    api_title: str = Field(
        default="Transcript Summarizer API",
        env="API_TITLE"
    )
    
    api_version: str = Field(
        default="0.1.0",
        env="API_VERSION"
    )
    
    api_host: str = Field(
        default="0.0.0.0",
        env="API_HOST"
    )
    
    api_port: int = Field(
        default=8000,
        env="API_PORT"
    )
    
    # Celery Configuration
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_BROKER_URL"
    )
    
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_RESULT_BACKEND"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    
    log_format: str = Field(
        default="json",
        env="LOG_FORMAT",
        description="Log format: json or console"
    )
    
    # Performance Configuration
    max_workers: int = Field(
        default=4,
        env="MAX_WORKERS",
        description="Maximum number of worker processes"
    )
    
    request_timeout: int = Field(
        default=300,
        env="REQUEST_TIMEOUT",
        description="Request timeout in seconds"
    )
    
    max_text_length: int = Field(
        default=1000000,  # 1MB of text
        env="MAX_TEXT_LENGTH",
        description="Maximum text length for processing"
    )
    
    # Development/Testing
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Enable debug mode"
    )
    
    testing: bool = Field(
        default=False,
        env="TESTING",
        description="Enable testing mode"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
