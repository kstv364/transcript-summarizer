"""Gradio web interface for the Transcript Summarizer."""

import gradio as gr
import asyncio
import httpx
import json
import time
from typing import Optional, Tuple, Any
import os
from pathlib import Path
import tempfile

from ..utils.vtt_parser import VTTParser, is_valid_vtt
from ..config.settings import Settings


class TranscriptSummarizerUI:
    """Gradio web interface for transcript summarization."""
    
    def __init__(self, api_base_url: str = None):
        """
        Initialize the UI.
        
        Args:
            api_base_url: Base URL for the API (default: http://localhost:8000)
        """
        self.settings = Settings()
        self.api_base_url = api_base_url or "http://localhost:8000"
        self.vtt_parser = VTTParser()
        
    def process_file_upload(self, file) -> Tuple[str, str]:
        """
        Process uploaded file (VTT or text).
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (processed_text, status_message)
        """
        if file is None:
            return "", "❌ No file uploaded"
        
        try:
            # Read file content
            file_path = file.name
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.vtt':
                # Parse VTT file
                transcript = self.vtt_parser.parse_vtt_file(file_path)
                metadata = self.vtt_parser.extract_metadata(file_path)
                
                status = f"✅ VTT file processed successfully!\n"
                status += f"📊 Captions: {metadata.get('total_captions', 'Unknown')}\n"
                status += f"⏱️ Duration: {metadata.get('duration', 'Unknown')}\n"
                status += f"📝 Text length: {len(transcript)} characters"
                
                return transcript, status
                
            elif file_ext in ['.txt', '.text']:
                # Read plain text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    transcript = f.read()
                
                status = f"✅ Text file processed successfully!\n"
                status += f"📝 Text length: {len(transcript)} characters"
                
                return transcript, status
                
            else:
                return "", f"❌ Unsupported file type: {file_ext}. Please upload .vtt or .txt files."
                
        except Exception as e:
            return "", f"❌ Error processing file: {str(e)}"
    
    def validate_transcript_input(self, text: str) -> Tuple[bool, str]:
        """
        Validate transcript input.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (is_valid, status_message)
        """
        if not text or not text.strip():
            return False, "❌ Please provide transcript text or upload a file"
        
        if len(text.strip()) < 50:
            return False, "❌ Transcript too short (minimum 50 characters)"
        
        if len(text) > 1000000:  # 1MB limit
            return False, "❌ Transcript too long (maximum 1MB)"
        
        return True, "✅ Transcript validation passed"
    
    async def summarize_transcript(
        self, 
        transcript: str, 
        summary_type: str = "concise",
        custom_prompt: str = ""
    ) -> Tuple[str, str, str]:
        """
        Summarize transcript using the API.
        
        Args:
            transcript: Transcript text
            summary_type: Type of summary (concise, detailed, bullet_points)
            custom_prompt: Custom summarization prompt
            
        Returns:
            Tuple of (summary, status, task_id)
        """
        try:
            # Validate input
            is_valid, validation_msg = self.validate_transcript_input(transcript)
            if not is_valid:
                return "", validation_msg, ""
            
            # Prepare request
            request_data = {
                "text": transcript.strip(),
                "summary_type": summary_type
            }
            
            if custom_prompt.strip():
                request_data["custom_prompt"] = custom_prompt.strip()
            
            # Submit summarization request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/summarize",
                    json=request_data
                )
                
                if response.status_code != 200:
                    error_msg = f"❌ API Error: {response.status_code}"
                    try:
                        error_detail = response.json().get("detail", "Unknown error")
                        error_msg += f" - {error_detail}"
                    except:
                        pass
                    return "", error_msg, ""
                
                result = response.json()
                task_id = result.get("task_id")
                
                if not task_id:
                    return "", "❌ No task ID returned from API", ""
                
                # Poll for completion
                status_msg = f"🔄 Summarization started (Task ID: {task_id})"
                
                max_attempts = 60  # 5 minutes maximum
                attempt = 0
                
                while attempt < max_attempts:
                    await asyncio.sleep(5)  # Wait 5 seconds between checks
                    attempt += 1
                    
                    try:
                        status_response = await client.get(
                            f"{self.api_base_url}/status/{task_id}"
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            task_status = status_data.get("status")
                            
                            if task_status == "completed":
                                # Get the summary
                                summary_response = await client.get(
                                    f"{self.api_base_url}/summary/{task_id}"
                                )
                                
                                if summary_response.status_code == 200:
                                    summary_data = summary_response.json()
                                    summary = summary_data.get("summary", "")
                                    
                                    final_status = f"✅ Summarization completed!\n"
                                    final_status += f"📝 Summary length: {len(summary)} characters\n"
                                    final_status += f"⏱️ Processing time: {attempt * 5} seconds"
                                    
                                    return summary, final_status, task_id
                                else:
                                    return "", f"❌ Failed to retrieve summary: {summary_response.status_code}", task_id
                            
                            elif task_status == "failed":
                                error_msg = status_data.get("error", "Unknown error")
                                return "", f"❌ Summarization failed: {error_msg}", task_id
                            
                            elif task_status in ["pending", "processing"]:
                                status_msg = f"🔄 Processing... (attempt {attempt}/{max_attempts})"
                                continue
                        
                    except Exception as e:
                        continue  # Continue polling on temporary errors
                
                return "", f"⏰ Summarization timed out after {max_attempts * 5} seconds", task_id
                
        except Exception as e:
            return "", f"❌ Error: {str(e)}", ""
    
    def check_api_health(self) -> str:
        """Check if the API is healthy."""
        try:
            import requests
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    return "✅ API is healthy and ready"
                else:
                    return f"⚠️ API status: {data.get('status', 'unknown')}"
            else:
                return f"❌ API health check failed: {response.status_code}"
        except Exception as e:
            return f"❌ Cannot connect to API: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface."""
        
        with gr.Blocks(
            title="Transcript Summarizer",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px !important;
            }
            .status-box {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                margin: 10px 0;
                background-color: #f9f9f9;
            }
            """
        ) as demo:
            
            gr.Markdown("""
            # 🎯 Transcript Summarizer
            
            Upload a VTT subtitle file or paste transcript text to generate AI-powered summaries using Ollama models.
            
            ### Supported formats:
            - **VTT files** (.vtt) - WebVTT subtitle files
            - **Text files** (.txt) - Plain text transcripts
            - **Direct text input** - Paste transcript directly
            """)
            
            # API Health Status
            with gr.Row():
                health_status = gr.Textbox(
                    label="🔍 API Status",
                    value=self.check_api_health(),
                    interactive=False,
                    elem_classes=["status-box"]
                )
                refresh_health = gr.Button("🔄 Refresh Status", size="sm")
            
            with gr.Row():
                # Left column - Input
                with gr.Column(scale=1):
                    gr.Markdown("## 📝 Input")
                    
                    # File upload
                    file_upload = gr.File(
                        label="Upload VTT or Text File",
                        file_types=[".vtt", ".txt"],
                        file_count="single"
                    )
                    
                    file_status = gr.Textbox(
                        label="📁 File Status",
                        interactive=False,
                        elem_classes=["status-box"]
                    )
                    
                    # Text input
                    transcript_input = gr.Textbox(
                        label="Or paste transcript text here",
                        placeholder="Paste your transcript here...",
                        lines=8,
                        max_lines=15
                    )
                    
                    # Summary options
                    with gr.Row():
                        summary_type = gr.Dropdown(
                            choices=["concise", "detailed", "bullet_points"],
                            value="concise",
                            label="📋 Summary Type"
                        )
                    
                    custom_prompt = gr.Textbox(
                        label="🎯 Custom Prompt (Optional)",
                        placeholder="Custom instructions for summarization...",
                        lines=2
                    )
                    
                    # Action buttons
                    with gr.Row():
                        summarize_btn = gr.Button("✨ Summarize", variant="primary", size="lg")
                        clear_btn = gr.Button("🗑️ Clear", size="sm")
                
                # Right column - Output
                with gr.Column(scale=1):
                    gr.Markdown("## 📄 Summary")
                    
                    summary_output = gr.Textbox(
                        label="Generated Summary",
                        lines=12,
                        max_lines=20,
                        show_copy_button=True
                    )
                    
                    process_status = gr.Textbox(
                        label="📊 Processing Status",
                        interactive=False,
                        elem_classes=["status-box"]
                    )
                    
                    task_id_output = gr.Textbox(
                        label="🔗 Task ID",
                        interactive=False,
                        visible=False
                    )
            
            # Examples section
            gr.Markdown("## 💡 Examples")
            
            examples = gr.Examples(
                examples=[
                    ["This is a sample meeting transcript. John: Hello everyone, welcome to today's quarterly review meeting. We'll be discussing our performance metrics and future planning strategies.", "concise", ""],
                    ["Technical discussion about software development. Sarah: We need to implement the new authentication system. Mike: I agree, security is paramount for our users.", "detailed", "Focus on technical decisions and action items"],
                    ["Training session transcript. Instructor: Today we'll cover safety protocols. Student: What are the emergency procedures?", "bullet_points", ""]
                ],
                inputs=[transcript_input, summary_type, custom_prompt],
                outputs=[summary_output, process_status],
                fn=lambda x, y, z: asyncio.run(self.summarize_transcript(x, y, z))[:2],  # Only return summary and status
                cache_examples=False
            )
            
            # Event handlers
            def handle_file_upload(file):
                if file is None:
                    return "", ""
                text, status = self.process_file_upload(file)
                return text, status
            
            def handle_summarize(transcript, summary_type, custom_prompt):
                try:
                    # Run async function
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(
                        self.summarize_transcript(transcript, summary_type, custom_prompt)
                    )
                    loop.close()
                    return result
                except Exception as e:
                    return "", f"❌ Error: {str(e)}", ""
            
            def handle_clear():
                return "", "", "", "", "", ""
            
            def handle_refresh_health():
                return self.check_api_health()
            
            # Wire up events
            file_upload.change(
                fn=handle_file_upload,
                inputs=[file_upload],
                outputs=[transcript_input, file_status]
            )
            
            summarize_btn.click(
                fn=handle_summarize,
                inputs=[transcript_input, summary_type, custom_prompt],
                outputs=[summary_output, process_status, task_id_output]
            )
            
            clear_btn.click(
                fn=handle_clear,
                outputs=[transcript_input, file_status, summary_output, process_status, task_id_output, custom_prompt]
            )
            
            refresh_health.click(
                fn=handle_refresh_health,
                outputs=[health_status]
            )
        
        return demo
    
    def launch(self, **kwargs):
        """Launch the Gradio interface."""
        demo = self.create_interface()
        return demo.launch(**kwargs)


def create_ui(api_base_url: str = None) -> TranscriptSummarizerUI:
    """Create and return the UI instance."""
    return TranscriptSummarizerUI(api_base_url)


def launch_ui(
    api_base_url: str = None,
    server_name: str = "0.0.0.0",
    server_port: int = 7860,
    share: bool = False,
    **kwargs
) -> None:
    """Launch the Gradio UI."""
    ui = create_ui(api_base_url)
    ui.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        **kwargs
    )


if __name__ == "__main__":
    # Launch with default settings
    launch_ui()
