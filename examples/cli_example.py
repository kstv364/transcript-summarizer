"""Example CLI usage of the transcript summarizer."""

import asyncio
from transcript_summarizer.core.summarizer import create_summarizer


async def main():
    """Demonstrate direct usage of the summarizer."""
    print("Transcript Summarizer CLI Example")
    print("=" * 50)
    
    # Sample transcript
    transcript = """
    Today's product development meeting covered several important updates and decisions 
    for our upcoming release cycle.
    
    First, we reviewed the progress on our mobile application redesign. The UI/UX team 
    has completed 80% of the wireframes, and early user testing shows a 35% improvement 
    in user engagement. The development team estimates completion by the end of next month.
    
    Second, we discussed the integration of AI-powered features. The machine learning team 
    has successfully implemented natural language processing capabilities that can analyze 
    user feedback and provide automated insights. This feature will be rolled out in beta 
    to select customers next week.
    
    We also addressed some technical challenges. The recent API performance issues have 
    been resolved through database optimization and caching improvements. Response times 
    have improved by 60%, and we haven't seen any downtime in the past two weeks.
    
    On the security front, we've completed the penetration testing with the external 
    security firm. They identified three minor vulnerabilities, all of which have been 
    patched. We've also implemented two-factor authentication for all admin accounts.
    
    Finally, we discussed the roadmap for Q2. Priority features include advanced analytics 
    dashboard, mobile app launch, and expansion of our API capabilities. The team agreed 
    on resource allocation and timeline estimates.
    
    The meeting concluded with action items assigned to each team lead, with a follow-up 
    scheduled for next Friday.
    """
    
    print(f"Original transcript: {len(transcript)} characters\n")
    
    # Create summarizer
    print("Creating summarizer...")
    summarizer = await create_summarizer()
    print("✅ Summarizer created\n")
    
    # Test different summary types
    summary_types = ["comprehensive", "brief", "key_points"]
    
    for summary_type in summary_types:
        print(f"Generating {summary_type} summary...")
        print("-" * 40)
        
        try:
            result = await summarizer.summarize_transcript(transcript, summary_type)
            
            print(f"Summary Type: {result.summary_type}")
            print(f"Original Length: {result.original_length:,} characters")
            print(f"Summary Length: {result.summary_length:,} characters")
            print(f"Compression Ratio: {result.compression_ratio:.1f}x")
            print(f"Chunks Processed: {result.chunk_count}")
            print()
            print("Summary:")
            print(result.summary)
            print("\n" + "=" * 80 + "\n")
            
        except Exception as e:
            print(f"❌ Error generating {summary_type} summary: {e}\n")


if __name__ == "__main__":
    print("Make sure Ollama is running with llama3 model loaded:")
    print("  ollama serve")
    print("  ollama pull llama3")
    print()
    print("And install dependencies with uv:")
    print("  uv pip install -e \".[dev]\"")
    print()
    
    asyncio.run(main())
