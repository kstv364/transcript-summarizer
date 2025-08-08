"""Example usage of the transcript summarizer API."""

import asyncio
import time
import httpx


async def main():
    """Demonstrate the transcript summarizer API."""
    base_url = "http://localhost:8000"
    
    # Sample transcript
    transcript = """
    Welcome to our quarterly board meeting. I'm pleased to report that this has been 
    our strongest quarter yet, with revenue reaching $4.2 million, representing a 
    28% increase from the same quarter last year.
    
    Our growth has been driven primarily by three factors: expansion into the European 
    market, the successful launch of our new product line, and improved customer 
    retention rates. The European expansion alone contributed $800,000 in new revenue.
    
    On the operational side, we've made significant investments in our infrastructure. 
    We've hired 15 new engineers, upgraded our data centers, and implemented new 
    security protocols. These investments position us well for continued growth.
    
    Customer satisfaction scores have improved to 4.6 out of 5, up from 4.1 last quarter. 
    Our new customer support team and enhanced product features have been key drivers 
    of this improvement.
    
    Looking ahead to next quarter, we're planning to launch in two additional markets 
    and introduce three new product features. We expect this to drive another 20-25% 
    growth in revenue.
    
    However, we're also monitoring some challenges. Supply chain costs have increased 
    by 12%, and we're seeing increased competition in our core markets. We have 
    strategies in place to address both of these issues.
    
    In terms of financial health, our cash position remains strong at $2.1 million, 
    and we're on track to achieve profitability by the end of next quarter.
    
    Are there any questions about our performance or strategy going forward?
    """
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🚀 Starting transcript summarization example...")
        
        # 1. Check health
        print("\n1. Checking API health...")
        try:
            health_response = await client.get(f"{base_url}/health")
            health_response.raise_for_status()
            health_data = health_response.json()
            print(f"   Status: {health_data['status']}")
            print(f"   Services: {health_data['services']}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return
        
        # 2. Submit transcript for summarization
        print("\n2. Submitting transcript for summarization...")
        try:
            summarize_response = await client.post(
                f"{base_url}/summarize",
                json={
                    "text": transcript,
                    "summary_type": "comprehensive"
                }
            )
            summarize_response.raise_for_status()
            summarize_data = summarize_response.json()
            task_id = summarize_data["task_id"]
            print(f"   ✅ Task submitted: {task_id}")
            print(f"   Estimated completion: {summarize_data['estimated_completion_time']}s")
        except Exception as e:
            print(f"   ❌ Summarization request failed: {e}")
            return
        
        # 3. Monitor task status
        print("\n3. Monitoring task progress...")
        max_attempts = 60  # 5 minutes
        attempt = 0
        
        while attempt < max_attempts:
            try:
                status_response = await client.get(f"{base_url}/status/{task_id}")
                status_response.raise_for_status()
                status_data = status_response.json()
                
                status = status_data["status"]
                progress = status_data.get("progress")
                
                if progress is not None:
                    print(f"   📊 Status: {status} ({progress}%)")
                else:
                    print(f"   📊 Status: {status}")
                
                if status == "completed":
                    print("   ✅ Summarization completed!")
                    break
                elif status == "failed":
                    error_msg = status_data.get("error_message", "Unknown error")
                    print(f"   ❌ Summarization failed: {error_msg}")
                    return
                
                await asyncio.sleep(5)
                attempt += 1
                
            except Exception as e:
                print(f"   ❌ Status check failed: {e}")
                await asyncio.sleep(5)
                attempt += 1
        
        if attempt >= max_attempts:
            print("   ⏰ Timeout waiting for completion")
            return
        
        # 4. Get the summary
        print("\n4. Retrieving summary...")
        try:
            summary_response = await client.get(f"{base_url}/summary/{task_id}")
            summary_response.raise_for_status()
            summary_data = summary_response.json()
            
            print("   ✅ Summary retrieved!")
            print("\n" + "="*80)
            print("SUMMARY RESULTS")
            print("="*80)
            print(f"Summary Type: {summary_data['summary_type']}")
            print(f"Original Length: {summary_data['original_length']:,} characters")
            print(f"Summary Length: {summary_data['summary_length']:,} characters")
            print(f"Compression Ratio: {summary_data['compression_ratio']:.1f}x")
            print(f"Processing Time: {summary_data.get('processing_time', 'N/A')}s")
            print(f"Chunks Processed: {summary_data['chunk_count']}")
            print("\n" + "-"*80)
            print("SUMMARY:")
            print("-"*80)
            print(summary_data['summary'])
            print("="*80)
            
        except Exception as e:
            print(f"   ❌ Failed to retrieve summary: {e}")
            return
        
        # 5. Search for similar summaries
        print("\n5. Searching for similar summaries...")
        try:
            search_response = await client.get(
                f"{base_url}/search",
                params={"query": "quarterly financial results", "limit": 3}
            )
            search_response.raise_for_status()
            search_data = search_response.json()
            
            print(f"   Found {search_data['count']} similar summaries")
            for i, result in enumerate(search_data['results'][:2], 1):
                print(f"   {i}. Similarity: {result['similarity_score']:.2f}")
                print(f"      Preview: {result['summary'][:100]}...")
                
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
        
        # 6. Get application stats
        print("\n6. Getting application statistics...")
        try:
            stats_response = await client.get(f"{base_url}/stats")
            stats_response.raise_for_status()
            stats_data = stats_response.json()
            
            print("   📈 Application Statistics:")
            if "vector_store" in stats_data:
                vs_stats = stats_data["vector_store"]
                print(f"      Total documents: {vs_stats.get('total_documents', 'N/A')}")
                print(f"      Summaries: {vs_stats.get('summary_count', 'N/A')}")
            
            if "celery" in stats_data:
                celery_stats = stats_data["celery"]
                print(f"      Active tasks: {celery_stats.get('active_tasks', 'N/A')}")
                
        except Exception as e:
            print(f"   ❌ Stats retrieval failed: {e}")
        
        print("\n🎉 Example completed successfully!")


if __name__ == "__main__":
    print("Transcript Summarizer API Example")
    print("="*50)
    print("Make sure the API server is running at http://localhost:8000")
    print("Start it with: uvicorn transcript_summarizer.api:app --reload")
    print("(Install dependencies with: uv pip install -e \".[dev]\")")
    print()
    
    asyncio.run(main())
