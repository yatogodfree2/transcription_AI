"""Module for transcription using Whisper CLI."""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union


class TranscriptionError(Exception):
    """Exception raised for errors in the transcription process."""

    pass


def ensure_ffmpeg() -> bool:
    """Check if ffmpeg is installed.

    Returns:
        bool: True if ffmpeg is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True, 
            check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def convert_audio_format(
    input_file: str, 
    output_format: str = "wav", 
    output_file: Optional[str] = None
) -> str:
    """Convert audio file to a format compatible with Whisper.

    Args:
        input_file: Path to input audio file.
        output_format: Desired output format (default: wav).
        output_file: Path to output file. If None, a temporary file will be created.

    Returns:
        str: Path to the converted audio file.

    Raises:
        TranscriptionError: If conversion fails.
    """
    if not ensure_ffmpeg():
        raise TranscriptionError("FFmpeg is not installed. Required for audio conversion.")

    if output_file is None:
        fd, output_file = tempfile.mkstemp(suffix=f".{output_format}")
        os.close(fd)

    try:
        result = subprocess.run(
            [
                "ffmpeg", 
                "-i", input_file,
                "-ar", "16000",  # Whisper prefers 16kHz audio
                "-ac", "1",      # Mono channel
                "-c:a", "pcm_s16le",  # 16-bit PCM
                "-y",            # Overwrite output file
                output_file
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return output_file
    except subprocess.CalledProcessError as e:
        raise TranscriptionError(f"Audio conversion failed: {e.stderr}")


def transcribe_audio(
    audio_file: str,
    output_dir: str = "data/transcriptions",
    model_size: str = "base",
    language: Optional[str] = None,
    output_formats: Optional[List[str]] = None,
    mock_mode: bool = True,  # Set to True until Whisper is properly installed
) -> Dict[str, Union[str, Dict]]:
    """Transcribe audio using Whisper CLI.

    Args:
        audio_file: Path to audio file.
        output_dir: Directory to save transcription results.
        model_size: Whisper model size (tiny, base, small, medium, large).
        language: Language code (ISO 639-1) to force. None for auto-detection.
        output_formats: List of output formats. Defaults to ["json", "vtt"].
        mock_mode: If True, generates mock output instead of calling Whisper CLI.

    Returns:
        Dict: Transcription results with paths to output files.

    Raises:
        TranscriptionError: If transcription fails.
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Set default output formats if not provided
    if output_formats is None:
        output_formats = ["json", "vtt"]

    # Generate a unique name for the output files based on input filename
    base_name = Path(audio_file).stem
    output_prefix = output_path / base_name
    
    if mock_mode:
        print(f"[MOCK MODE] Generating mock transcription for {audio_file}")
        # Generate mock output files
        mock_transcript = "This is a mock transcript generated as a placeholder. Whisper integration pending."
        
        # Create mock JSON file
        json_file = output_path / f"{base_name}.json"
        mock_json = {
            "text": mock_transcript,
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 3.0,
                    "text": "This is a mock transcript"
                },
                {
                    "id": 1,
                    "start": 3.0,
                    "end": 6.0,
                    "text": "generated as a placeholder."
                },
                {
                    "id": 2,
                    "start": 6.0,
                    "end": 9.0,
                    "text": "Whisper integration pending."
                }
            ],
            "language": language or "en"
        }
        with open(json_file, "w") as f:
            json.dump(mock_json, f, indent=2)
            
        # Create mock VTT file
        vtt_file = output_path / f"{base_name}.vtt"
        mock_vtt = "WEBVTT\n\n" + \
                  "1\n00:00:00.000 --> 00:00:03.000\nThis is a mock transcript\n\n" + \
                  "2\n00:00:03.000 --> 00:00:06.000\ngenerated as a placeholder.\n\n" + \
                  "3\n00:00:06.000 --> 00:00:09.000\nWhisper integration pending."
                  
        with open(vtt_file, "w") as f:
            f.write(mock_vtt)
            
        # Return paths to mock output files
        outputs = {
            "json": str(json_file),
            "vtt": str(vtt_file),
            "transcription": mock_json
        }
                
        return {
            "success": True,
            "audio_file": audio_file,
            "outputs": outputs,
            "model": "mock",
            "command_output": "[MOCK] Transcription completed successfully.",
        }
    else:
        # Prepare command for real Whisper CLI
        cmd = ["whisper", audio_file, "--model", model_size]
        
        # Add language if specified
        if language:
            cmd.extend(["--language", language])
        
        # Add output directory
        cmd.extend(["--output_dir", str(output_path)])
        
        # Add output formats
        for fmt in output_formats:
            cmd.append(f"--{fmt}")

        try:
            # Run whisper command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Return paths to output files
            outputs = {}
            for fmt in output_formats:
                out_file = output_path / f"{base_name}.{fmt}"
                outputs[fmt] = str(out_file)
            
            # If JSON output was requested, also load its contents
            json_file = output_path / f"{base_name}.json"
            if json_file.exists():
                with open(json_file, 'r') as f:
                    outputs["transcription"] = json.load(f)
                    
            return {
                "success": True,
                "audio_file": audio_file,
                "outputs": outputs,
                "model": model_size,
                "command_output": result.stdout,
            }
            
        except subprocess.CalledProcessError as e:
            raise TranscriptionError(f"Transcription failed: {e.stderr}")


def extract_transcript_from_json(json_file: str) -> str:
    """Extract plain transcript text from Whisper JSON output.
    
    Args:
        json_file: Path to JSON file generated by Whisper.
        
    Returns:
        str: Plain text transcript.
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        if "text" in data:
            # Newer whisper versions include a "text" field with full transcript
            return data["text"]
        
        # For older versions, concatenate segments
        if "segments" in data:
            transcript = ""
            for segment in data["segments"]:
                if "text" in segment:
                    transcript += segment["text"] + " "
            return transcript.strip()
            
        raise TranscriptionError("Unexpected JSON format: no text or segments found")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise TranscriptionError(f"Failed to extract transcript: {str(e)}")
