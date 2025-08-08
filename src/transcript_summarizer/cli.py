"""Command-line interface for the transcript summarizer."""

import asyncio
import sys
from typing import Optional
import click
import structlog

from .config.settings import get_settings
from .core.summarizer import create_summarizer
from .models.schemas import SummaryType

logger = structlog.get_logger(__name__)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
def cli(debug: bool):
    """Transcript Summarizer CLI."""
    if debug:
        import os
        os.environ['DEBUG'] = 'true'
        os.environ['LOG_LEVEL'] = 'DEBUG'


@cli.command()
@click.argument('text_file', type=click.File('r'))
@click.option('--summary-type', 
              type=click.Choice(['comprehensive', 'brief', 'key_points']), 
              default='comprehensive',
              help='Type of summary to generate')
@click.option('--output', '-o', type=click.File('w'), default=sys.stdout,
              help='Output file (default: stdout)')
def summarize(text_file, summary_type: str, output):
    """Summarize a transcript from a file."""
    async def _summarize():
        try:
            # Read input text
            text = text_file.read().strip()
            if not text:
                click.echo("Error: Input file is empty", err=True)
                sys.exit(1)
            
            click.echo(f"Processing {len(text)} characters...", err=True)
            
            # Create summarizer and process
            summarizer = await create_summarizer()
            result = await summarizer.summarize_transcript(text, summary_type)
            
            # Write output
            output.write(result.summary)
            output.write('\n')
            
            # Print stats to stderr
            click.echo(f"\nSummary completed:", err=True)
            click.echo(f"  Original length: {result.original_length:,} characters", err=True)
            click.echo(f"  Summary length: {result.summary_length:,} characters", err=True)
            click.echo(f"  Compression ratio: {result.compression_ratio:.2f}x", err=True)
            click.echo(f"  Chunks processed: {result.chunk_count}", err=True)
            
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_summarize())


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
def serve(host: str, port: int, reload: bool):
    """Start the FastAPI server."""
    import uvicorn
    
    uvicorn.run(
        "transcript_summarizer.api:app",
        host=host,
        port=port,
        reload=reload
    )


@cli.command()
@click.option('--loglevel', default='info', help='Celery log level')
@click.option('--concurrency', default=1, help='Number of worker processes')
def worker(loglevel: str, concurrency: int):
    """Start a Celery worker."""
    from .worker import app as celery_app
    
    celery_app.worker_main([
        'worker',
        f'--loglevel={loglevel}',
        f'--concurrency={concurrency}',
        '--queues=summarization',
    ])


@cli.command()
def health():
    """Check the health of all services."""
    async def _health_check():
        try:
            settings = get_settings()
            
            click.echo("Checking service health...")
            
            # Check Ollama
            try:
                from langchain_ollama import OllamaLLM
                llm = OllamaLLM(
                    base_url=settings.ollama_base_url,
                    model=settings.ollama_model
                )
                # Simple test
                response = llm.invoke("Hello")
                click.echo("✓ Ollama: Healthy")
            except Exception as e:
                click.echo(f"✗ Ollama: Unhealthy - {e}")
            
            # Check ChromaDB
            try:
                from .storage.vector_store import get_vector_store
                vector_store = await get_vector_store()
                health = await vector_store.health_check()
                if health.get("status") == "healthy":
                    click.echo("✓ ChromaDB: Healthy")
                else:
                    click.echo(f"✗ ChromaDB: Unhealthy - {health.get('error', 'Unknown error')}")
            except Exception as e:
                click.echo(f"✗ ChromaDB: Unhealthy - {e}")
            
            # Check Redis
            try:
                import redis
                r = redis.from_url(settings.redis_url)
                r.ping()
                click.echo("✓ Redis: Healthy")
            except Exception as e:
                click.echo(f"✗ Redis: Unhealthy - {e}")
                
        except Exception as e:
            click.echo(f"Health check failed: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_health_check())


@cli.command()
def init():
    """Initialize the application (create necessary directories, etc.)."""
    click.echo("Initializing transcript summarizer...")
    
    settings = get_settings()
    
    # Create any necessary directories
    import os
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    click.echo("✓ Created data and logs directories")
    
    # Test configuration
    click.echo(f"✓ Ollama URL: {settings.ollama_base_url}")
    click.echo(f"✓ Ollama Model: {settings.ollama_model}")
    click.echo(f"✓ ChromaDB: {settings.chroma_host}:{settings.chroma_port}")
    click.echo(f"✓ Redis: {settings.redis_url}")
    
    click.echo("Initialization complete!")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
