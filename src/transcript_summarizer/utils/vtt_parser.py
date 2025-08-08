"""VTT file parser for transcript summarization."""

import webvtt
import io
from typing import Optional, List, Dict, Any
import re
from pathlib import Path
import tempfile
import os


class VTTParser:
    """Parser for WebVTT subtitle files."""
    
    def __init__(self):
        """Initialize the VTT parser."""
        pass
    
    def parse_vtt_file(self, file_path: str) -> str:
        """
        Parse a VTT file and extract the transcript text.
        
        Args:
            file_path: Path to the VTT file
            
        Returns:
            Extracted transcript text
            
        Raises:
            ValueError: If file parsing fails
        """
        try:
            vtt = webvtt.read(file_path)
            return self._extract_text_from_vtt(vtt)
        except Exception as e:
            raise ValueError(f"Failed to parse VTT file: {str(e)}")
    
    def parse_vtt_content(self, content: str) -> str:
        """
        Parse VTT content from a string.
        
        Args:
            content: VTT file content as string
            
        Returns:
            Extracted transcript text
            
        Raises:
            ValueError: If content parsing fails
        """
        try:
            # Create a temporary file to work with webvtt library
            with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                vtt = webvtt.read(temp_file_path)
                return self._extract_text_from_vtt(vtt)
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            raise ValueError(f"Failed to parse VTT content: {str(e)}")
    
    def parse_vtt_upload(self, file_content: bytes) -> str:
        """
        Parse VTT content from uploaded file bytes.
        
        Args:
            file_content: VTT file content as bytes
            
        Returns:
            Extracted transcript text
            
        Raises:
            ValueError: If content parsing fails
        """
        try:
            # Decode bytes to string
            content = file_content.decode('utf-8')
            return self.parse_vtt_content(content)
        except UnicodeDecodeError:
            raise ValueError("File is not a valid UTF-8 encoded VTT file")
    
    def _extract_text_from_vtt(self, vtt) -> str:
        """
        Extract clean text from parsed VTT object.
        
        Args:
            vtt: Parsed WebVTT object
            
        Returns:
            Clean transcript text
        """
        transcript_parts = []
        
        for caption in vtt:
            # Clean the caption text
            text = self._clean_caption_text(caption.text)
            if text.strip():
                transcript_parts.append(text)
        
        # Join all parts with spaces
        transcript = ' '.join(transcript_parts)
        
        # Final cleanup
        transcript = self._final_cleanup(transcript)
        
        return transcript
    
    def _clean_caption_text(self, text: str) -> str:
        """
        Clean individual caption text.
        
        Args:
            text: Raw caption text
            
        Returns:
            Cleaned caption text
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove VTT formatting (like positioning)
        text = re.sub(r'\{[^}]*\}', '', text)
        
        # Remove speaker labels like [Speaker 1:] or (John):
        text = re.sub(r'^\[.*?:\]\s*', '', text)
        text = re.sub(r'^\(.*?\):\s*', '', text)
        
        # Remove music notation like ♪ or [Music]
        text = re.sub(r'♪.*?♪', '', text)
        text = re.sub(r'\[Music\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[.*?\]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _final_cleanup(self, transcript: str) -> str:
        """
        Final cleanup of the complete transcript.
        
        Args:
            transcript: Raw transcript text
            
        Returns:
            Cleaned transcript text
        """
        # Remove multiple spaces
        transcript = re.sub(r'\s+', ' ', transcript)
        
        # Remove repeated words (common in auto-generated subtitles)
        words = transcript.split()
        cleaned_words = []
        prev_word = None
        
        for word in words:
            # Don't add if it's the same as previous word (case-insensitive)
            if prev_word is None or word.lower() != prev_word.lower():
                cleaned_words.append(word)
            prev_word = word
        
        transcript = ' '.join(cleaned_words)
        
        # Fix common punctuation issues
        transcript = re.sub(r'\s+([,.!?;:])', r'\1', transcript)
        transcript = re.sub(r'([.!?])\s*([a-z])', r'\1 \2', transcript)
        
        return transcript.strip()
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from VTT file.
        
        Args:
            file_path: Path to the VTT file
            
        Returns:
            Dictionary containing metadata
        """
        try:
            vtt = webvtt.read(file_path)
            
            total_captions = len(vtt)
            if total_captions == 0:
                return {
                    "total_captions": 0,
                    "duration": "00:00:00",
                    "start_time": None,
                    "end_time": None
                }
            
            start_time = vtt[0].start
            end_time = vtt[-1].end
            
            return {
                "total_captions": total_captions,
                "duration": end_time,
                "start_time": start_time,
                "end_time": end_time,
                "file_size": Path(file_path).stat().st_size if Path(file_path).exists() else 0
            }
            
        except Exception as e:
            return {
                "error": f"Failed to extract metadata: {str(e)}"
            }
    
    def is_valid_vtt(self, content: str) -> bool:
        """
        Check if content is valid VTT format.
        
        Args:
            content: Content to validate
            
        Returns:
            True if valid VTT format
        """
        try:
            # Basic VTT validation
            lines = content.strip().split('\n')
            if not lines:
                return False
            
            # First line should be WEBVTT
            first_line = lines[0].strip()
            if not first_line.startswith('WEBVTT'):
                return False
            
            # Try to parse it
            self.parse_vtt_content(content)
            return True
            
        except Exception:
            return False


# Utility functions for easy access
def parse_vtt_file(file_path: str) -> str:
    """Parse VTT file and return transcript text."""
    parser = VTTParser()
    return parser.parse_vtt_file(file_path)


def parse_vtt_content(content: str) -> str:
    """Parse VTT content string and return transcript text."""
    parser = VTTParser()
    return parser.parse_vtt_content(content)


def parse_vtt_upload(file_content: bytes) -> str:
    """Parse uploaded VTT file bytes and return transcript text."""
    parser = VTTParser()
    return parser.parse_vtt_upload(file_content)


def is_valid_vtt(content: str) -> bool:
    """Check if content is valid VTT format."""
    parser = VTTParser()
    return parser.is_valid_vtt(content)
