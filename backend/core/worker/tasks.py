"""Task definitions for worker processing."""
import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.worker import transcription

from backend.core.worker.queue import get_queue


def _ensure_upload_dir(upload_dir: str = "data/uploads") -> Path:
    """Ensure upload directory exists.

    Args:
        upload_dir: Directory to store uploaded files.

    Returns:
        Path: Path to upload directory.
    """
    path = Path(upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_uploaded_file(file_content: bytes, filename: str, upload_dir: str = "data/uploads") -> Dict:
    """Save uploaded file to disk.

    Args:
        file_content: File content.
        filename: Original filename.
        upload_dir: Directory to store uploaded files.

    Returns:
        Dict: Information about the saved file.
    """
    # Generate a unique ID for the file
    file_id = str(uuid.uuid4())
    
    # Get file extension
    _, ext = os.path.splitext(filename)
    
    # Create safe filename with original name and unique ID
    safe_filename = f"{file_id}{ext}"
    
    # Ensure upload directory exists
    upload_path = _ensure_upload_dir(upload_dir)
    
    # Full path to the file
    file_path = upload_path / safe_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return {
        "file_id": file_id,
        "original_filename": filename,
        "path": str(file_path),
        "size": len(file_content)
    }


def process_file(file_info: Dict) -> Dict:
    """Process uploaded file using Whisper for transcription.
    
    This function is executed by the worker to process audio files.
    It transcribes audio to text using OpenAI's Whisper and returns
    the results in JSON and VTT formats.

    Args:
        file_info: Information about the file.

    Returns:
        Dict: Processing result with transcription data.
    """
    try:
        file_path = file_info["path"]
        file_id = file_info["file_id"]
        
        # Create transcription directory if it doesn't exist
        transcription_dir = Path("data/transcriptions")
        transcription_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert audio to a format compatible with Whisper if needed
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in [".wav"]:
            # Convert to WAV format for best compatibility with Whisper
            wav_path = os.path.join("data/uploads", f"{file_id}.wav")
            converted_path = transcription.convert_audio_format(
                input_file=file_path,
                output_file=wav_path
            )
        else:
            converted_path = file_path
        
        # Perform transcription using Whisper
        result = transcription.transcribe_audio(
            audio_file=converted_path,
            output_dir="data/transcriptions",
            model_size="base",  # Use base model for faster processing
            output_formats=["json", "vtt"]
        )
        
        # Return results
        return {
            **file_info,
            "status": "transcribed",
            "transcription": {
                "json_path": result["outputs"].get("json", ""),
                "vtt_path": result["outputs"].get("vtt", ""),
                "transcript": result["outputs"].get("transcription", {}).get("text", "")
            }
        }
    except Exception as e:
        # Log the error and return error status
        print(f"Error processing file: {str(e)}")
        return {
            **file_info,
            "status": "error",
            "error": str(e)
        }


def enqueue_file(file_content: bytes, filename: str, upload_dir: str = "data/uploads") -> Dict:
    """Save file and enqueue it for processing.

    Args:
        file_content: File content.
        filename: Original filename.
        upload_dir: Directory to store uploaded files.

    Returns:
        Dict: Job information.
    """
    # Save the file
    file_info = save_uploaded_file(file_content, filename, upload_dir)
    
    # Get queue
    queue = get_queue()
    
    # Enqueue job
    job = queue.enqueue(process_file, file_info)
    
    return {
        "job_id": job.id,
        "file_id": file_info["file_id"],
        "original_filename": file_info["original_filename"],
        "status": "queued"
    }
