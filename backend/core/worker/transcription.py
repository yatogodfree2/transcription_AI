"""Module for transcription using Vosk ASR (replacing Whisper CLI)."""
import json
import os
import subprocess
import tempfile
import wave
import datetime
import requests
import shutil
import tarfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from vosk import Model, KaldiRecognizer, SetLogLevel

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('vosk_transcription')

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
    model_size: str = "small",  # Vosk model size (small, medium, large)
    language: Optional[str] = None,
    output_formats: Optional[List[str]] = None,
    mock_mode: bool = False,  # Set to False since we're implementing actual Vosk integration
) -> Dict[str, Union[str, Dict]]:
    """Transcribe audio using Vosk ASR.

    Args:
        audio_file: Path to audio file.
        output_dir: Directory to save transcription results.
        model_size: Vosk model size (small, medium, large).
        language: Language code (ISO 639-1) to force. None for auto-detection (defaults to English).
        output_formats: List of output formats. Defaults to ["json", "vtt"].
        mock_mode: If True, generates mock output instead of calling Vosk.

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
        mock_transcript = "This is a mock transcript generated as a placeholder. Vosk integration pending."
        
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
                    "text": "Vosk integration pending."
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
                  "3\n00:00:06.000 --> 00:00:09.000\nVosk integration pending."
                  
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
        try:
            # Convert audio to format suitable for Vosk if needed
            wav_file = audio_file
            if not audio_file.lower().endswith('.wav'):
                wav_file = convert_audio_format(audio_file, "wav")
                
            # Get appropriate model path, downloading if necessary
            try:
                model_path = get_vosk_model(model_size, language)
                logger.info(f"Using Vosk model at {model_path}")
            except Exception as e:
                raise TranscriptionError(f"Could not obtain Vosk model: {str(e)}")
                
            # Load the model
            SetLogLevel(0)  # Reduce verbosity
            model = Model(str(model_path))
            
            # Process the audio file
            segments = []
            full_text = ""
            segment_id = 0
            sample_rate = 0
            
            with wave.open(wav_file, "rb") as wf:
                # Check audio format - must be 16-bit PCM
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                    raise TranscriptionError("Audio file must be WAV format mono PCM.")
                
                # Get sample rate for accurate timings
                sample_rate = wf.getframerate()
                    
                # Create recognizer
                rec = KaldiRecognizer(model, sample_rate)
                rec.SetWords(True)  # Get word timestamps
                
                # Get file duration for proper timings
                duration = wf.getnframes() / float(sample_rate)
                logger.info(f"Audio duration: {duration:.2f} seconds")
                
                # Process audio chunks
                chunk_size = 8000  # Read 8000 frames at a time for better sentence boundaries
                all_words = []
                
                while True:
                    data = wf.readframes(chunk_size)
                    if len(data) == 0:
                        break
                        
                    if rec.AcceptWaveform(data):
                        # Process complete utterance
                        result = json.loads(rec.Result())
                        if "result" in result and result["result"]:
                            # Add words with precise timestamps
                            all_words.extend(result["result"])
                            # We'll group them into segments later
                
                # Get final result
                final_result = json.loads(rec.FinalResult())
                if "result" in final_result and final_result["result"]:
                    all_words.extend(final_result["result"])
                
                # Group words into sentences/segments based on natural pauses
                # A new segment starts when there's a significant pause (>0.3s)
                if all_words:
                    current_segment = {
                        "id": segment_id,
                        "words": [],
                        "text": ""
                    }
                    
                    prev_end = all_words[0]["start"]
                    
                    for word in all_words:
                        # Check if there's a significant pause
                        if word["start"] - prev_end > 0.3 and current_segment["words"]:
                            # Finalize current segment
                            words_text = " ".join(w["word"] for w in current_segment["words"])
                            start_time = current_segment["words"][0]["start"]
                            end_time = current_segment["words"][-1]["end"]
                            
                            segments.append({
                                "id": segment_id,
                                "start": round(start_time, 3),
                                "end": round(end_time, 3),
                                "text": words_text
                            })
                            
                            full_text += words_text + " "
                            segment_id += 1
                            
                            # Start new segment
                            current_segment = {
                                "id": segment_id,
                                "words": [word],
                                "text": ""
                            }
                        else:
                            # Add to current segment
                            current_segment["words"].append(word)
                        
                        prev_end = word["end"]
                    
                    # Don't forget the last segment
                    if current_segment["words"]:
                        words_text = " ".join(w["word"] for w in current_segment["words"])
                        start_time = current_segment["words"][0]["start"]
                        end_time = current_segment["words"][-1]["end"]
                        
                        segments.append({
                            "id": segment_id,
                            "start": round(start_time, 3),
                            "end": round(end_time, 3),
                            "text": words_text
                        })
                        
                        full_text += words_text
            
            # Create transcription result
            transcription = {
                "text": full_text.strip(),
                "segments": segments,
                "language": language or "en"
            }
            
            # Write JSON output file
            json_file = output_path / f"{base_name}.json"
            with open(json_file, "w") as f:
                json.dump(transcription, f, indent=2)
            
            # Write VTT output file if requested
            vtt_file = None
            if "vtt" in output_formats:
                vtt_file = output_path / f"{base_name}.vtt"
                vtt_content = ["WEBVTT", ""]
                
                for segment in segments:
                    # Format timestamps for VTT (HH:MM:SS.mmm)
                    start_time = str(datetime.timedelta(seconds=segment["start"]))
                    if "." not in start_time:
                        start_time += ".000"
                    else:
                        start_time = start_time[:-3] if len(start_time.split(".")[-1]) > 3 else start_time
                        
                    end_time = str(datetime.timedelta(seconds=segment["end"]))
                    if "." not in end_time:
                        end_time += ".000"
                    else:
                        end_time = end_time[:-3] if len(end_time.split(".")[-1]) > 3 else end_time
                    
                    # Ensure HH:MM:SS format (VTT requires hours)
                    if start_time.count(":") == 1:
                        start_time = f"00:{start_time}"
                    if end_time.count(":") == 1:
                        end_time = f"00:{end_time}"
                        
                    vtt_content.append(f"{segment['id'] + 1}")
                    vtt_content.append(f"{start_time} --> {end_time}")
                    vtt_content.append(segment["text"])
                    vtt_content.append("")
                
                with open(vtt_file, "w") as f:
                    f.write("\n".join(vtt_content))
            
            # Return paths to output files
            outputs = {}
            if "json" in output_formats:
                outputs["json"] = str(json_file)
            if vtt_file and "vtt" in output_formats:
                outputs["vtt"] = str(vtt_file)
            outputs["transcription"] = transcription
                    
            return {
                "success": True,
                "audio_file": audio_file,
                "outputs": outputs,
                "model": model_name,
                "command_output": f"Vosk transcription completed successfully with model: {model_name}",
            }
            
        except Exception as e:
            raise TranscriptionError(f"Vosk transcription failed: {str(e)}")



def get_vosk_model(model_size: str = "small", language: Optional[str] = None) -> Path:
    """Get the path to a Vosk model, downloading it if it doesn't exist.
    
    Args:
        model_size: Size of the model (small, medium, large).
        language: ISO language code, defaults to English if None.
        
    Returns:
        Path: Path to the Vosk model directory.
        
    Raises:
        TranscriptionError: If the model couldn't be found or downloaded.
    """
    # Normalize inputs
    language = (language or "en").lower()
    model_size = model_size.lower()
    
    # Define model name and directory structure
    models_dir = Path(os.environ.get("VOSK_MODEL_PATH", "./models"))
    models_dir.mkdir(exist_ok=True, parents=True)
    
    # Define model mapping for different languages and sizes
    model_map = {
        # English models
        ("en", "small"): ("vosk-model-small-en-us-0.15", "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"),
        ("en", "medium"): ("vosk-model-en-us-0.22", "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"),
        ("en", "large"): ("vosk-model-en-us-0.22-lgraph", "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip"),
        
        # Russian models
        ("ru", "small"): ("vosk-model-small-ru-0.22", "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"),
        ("ru", "medium"): ("vosk-model-ru-0.42", "https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip"),
        
        # German models
        ("de", "small"): ("vosk-model-small-de-0.15", "https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip"),
        ("de", "large"): ("vosk-model-de-0.21", "https://alphacephei.com/vosk/models/vosk-model-de-0.21.zip"),
        
        # French models
        ("fr", "small"): ("vosk-model-small-fr-0.22", "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"),
        ("fr", "large"): ("vosk-model-fr-0.22", "https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip"),
        
        # Spanish models
        ("es", "small"): ("vosk-model-small-es-0.42", "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"),
        ("es", "large"): ("vosk-model-es-0.42", "https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip"),
    }
    
    # Fallback to English if language not available
    if (language, model_size) not in model_map:
        logger.warning(f"Model for language '{language}' and size '{model_size}' not found. Falling back to English.")
        language = "en"
        
    # Still ensure the model size is valid
    if (language, model_size) not in model_map:
        # If specific size not available, choose the closest one
        available_sizes = [size for lang, size in model_map.keys() if lang == language]
        if not available_sizes:
            raise TranscriptionError(f"No models available for language: {language}")
            
        # Choose fallback model size
        if "small" in available_sizes:
            model_size = "small"
        else:
            model_size = available_sizes[0]
        
        logger.warning(f"Using '{model_size}' model for language '{language}' as fallback.")
    
    # Get model info
    model_name, model_url = model_map[(language, model_size)]
    model_path = models_dir / model_name
    
    # Check if model exists
    if model_path.exists():
        logger.info(f"Vosk model already exists at {model_path}")
        return model_path
        
    # Download model if it doesn't exist
    logger.info(f"Downloading Vosk model from {model_url}...")
    return download_vosk_model(model_url, model_name, models_dir)


def download_vosk_model(url: str, model_name: str, models_dir: Path) -> Path:
    """Download and extract a Vosk model.
    
    Args:
        url: URL to download the model from.
        model_name: Name of the model.
        models_dir: Directory to store models.
        
    Returns:
        Path: Path to the extracted model directory.
        
    Raises:
        TranscriptionError: If download or extraction fails.
    """
    try:
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / f"{model_name}.zip"
            
            # Download model
            logger.info(f"Downloading model {model_name} from {url}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save to temporary file
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # Extract model
            logger.info(f"Extracting model to {models_dir}...")
            shutil.unpack_archive(zip_path, models_dir)
            
            # Check if extraction was successful
            model_path = models_dir / model_name
            if not model_path.exists():
                raise TranscriptionError(f"Model extraction failed. Path not found: {model_path}")
                
            return model_path
    except (requests.exceptions.RequestException, shutil.Error, OSError) as e:
        raise TranscriptionError(f"Failed to download or extract model: {str(e)}")


def extract_transcript_from_json(json_file: str) -> str:
    """Extract plain transcript text from JSON output.
    
    Args:
        json_file: Path to JSON file generated by the transcription process.
        
    Returns:
        str: Plain text transcript.
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        if "text" in data:
            # Main text field with full transcript
            return data["text"]
        
        # For older format or Vosk output, concatenate segments
        if "segments" in data:
            transcript = ""
            for segment in data["segments"]:
                if "text" in segment:
                    transcript += segment["text"] + " "
            return transcript.strip()
            
        raise TranscriptionError("Unexpected JSON format: no text or segments found")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise TranscriptionError(f"Failed to extract transcript: {str(e)}")
