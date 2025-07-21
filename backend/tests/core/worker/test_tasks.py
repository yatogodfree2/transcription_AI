"""Tests for tasks.py module."""
import os
import uuid
from pathlib import Path
from unittest import mock

import pytest

from backend.core.worker.tasks import (
    _ensure_upload_dir,
    save_uploaded_file,
    process_file,
    enqueue_file,
)


class TestTasks:
    """Test class for tasks.py module."""

    def test_ensure_upload_dir_creates_directory(self):
        """Test _ensure_upload_dir creates directory if it doesn't exist."""
        test_dir = "test_uploads"
        with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            result = _ensure_upload_dir(test_dir)
            assert result == Path(test_dir)
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_ensure_upload_dir_returns_path(self):
        """Test _ensure_upload_dir returns Path object."""
        test_dir = "test_uploads"
        result = _ensure_upload_dir(test_dir)
        assert isinstance(result, Path)
        assert str(result) == test_dir

    @mock.patch("backend.core.worker.tasks._ensure_upload_dir")
    @mock.patch("uuid.uuid4")
    def test_save_uploaded_file(self, mock_uuid, mock_ensure_dir):
        """Test save_uploaded_file saves file correctly."""
        # Setup mocks
        mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_ensure_dir.return_value = Path("test_uploads")
        
        # Call function
        file_content = b"test file content"
        filename = "test.mp3"
        
        # Mock open with context manager
        mock_file = mock.mock_open()
        with mock.patch("builtins.open", mock_file):
            result = save_uploaded_file(file_content, filename, "test_uploads")
        
        # Check results
        assert result["file_id"] == "12345678-1234-5678-1234-567812345678"
        assert result["original_filename"] == filename
        assert result["path"] == "test_uploads/12345678-1234-5678-1234-567812345678.mp3"
        assert result["size"] == len(file_content)
        
        # Verify file was written correctly
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with(file_content)

    @mock.patch("backend.core.worker.tasks.transcription")
    @mock.patch("pathlib.Path.mkdir")
    def test_process_file_mp3(self, mock_mkdir, mock_transcription):
        """Test process_file with MP3 file."""
        # Setup file info
        file_info = {
            "file_id": "12345678-1234-5678-1234-567812345678",
            "original_filename": "test.mp3",
            "path": "uploads/12345678-1234-5678-1234-567812345678.mp3",
            "size": 1000
        }
        
        # Setup transcription mock
        mock_transcription.convert_audio_format.return_value = "uploads/12345678-1234-5678-1234-567812345678.wav"
        mock_transcription.transcribe_audio.return_value = {
            "outputs": {
                "json": "transcriptions/12345678-1234-5678-1234-567812345678.json",
                "vtt": "transcriptions/12345678-1234-5678-1234-567812345678.vtt",
                "transcription": {"text": "Hello world"}
            }
        }
        
        # Call function
        result = process_file(file_info)
        
        # Check results
        assert result["status"] == "transcribed"
        assert result["transcription"]["transcript"] == "Hello world"
        assert "json_path" in result["transcription"]
        assert "vtt_path" in result["transcription"]
        
        # Verify transcription was called
        mock_transcription.convert_audio_format.assert_called_once()
        mock_transcription.transcribe_audio.assert_called_once()
        
    @mock.patch("backend.core.worker.tasks.transcription")
    @mock.patch("pathlib.Path.mkdir")
    def test_process_file_wav(self, mock_mkdir, mock_transcription):
        """Test process_file with WAV file (no conversion needed)."""
        # Setup file info
        file_info = {
            "file_id": "12345678-1234-5678-1234-567812345678",
            "original_filename": "test.wav",
            "path": "uploads/12345678-1234-5678-1234-567812345678.wav",
            "size": 1000
        }
        
        # Setup transcription mock
        mock_transcription.transcribe_audio.return_value = {
            "outputs": {
                "json": "transcriptions/12345678-1234-5678-1234-567812345678.json",
                "vtt": "transcriptions/12345678-1234-5678-1234-567812345678.vtt",
                "transcription": {"text": "Hello world"}
            }
        }
        
        # Call function
        result = process_file(file_info)
        
        # Check results
        assert result["status"] == "transcribed"
        
        # Verify transcription was called directly (no conversion)
        mock_transcription.convert_audio_format.assert_not_called()
        mock_transcription.transcribe_audio.assert_called_once()

    @mock.patch("backend.core.worker.tasks.transcription")
    @mock.patch("pathlib.Path.mkdir")
    def test_process_file_error(self, mock_mkdir, mock_transcription):
        """Test process_file handles errors correctly."""
        # Setup file info
        file_info = {
            "file_id": "12345678-1234-5678-1234-567812345678",
            "original_filename": "test.mp3",
            "path": "uploads/12345678-1234-5678-1234-567812345678.mp3",
            "size": 1000
        }
        
        # Setup transcription mock to raise an exception
        mock_transcription.transcribe_audio.side_effect = Exception("Transcription failed")
        
        # Call function
        result = process_file(file_info)
        
        # Check results
        assert result["status"] == "error"
        assert "error" in result
        assert "Transcription failed" in result["error"]

    @mock.patch("backend.core.worker.tasks.save_uploaded_file")
    @mock.patch("backend.core.worker.tasks.get_queue")
    def test_enqueue_file(self, mock_get_queue, mock_save_file):
        """Test enqueue_file correctly saves and enqueues file."""
        # Setup mocks
        mock_save_file.return_value = {
            "file_id": "12345678-1234-5678-1234-567812345678",
            "original_filename": "test.mp3",
            "path": "uploads/12345678-1234-5678-1234-567812345678.mp3",
            "size": 1000
        }
        
        mock_queue = mock.MagicMock()
        mock_job = mock.MagicMock()
        mock_job.id = "job-123"
        mock_queue.enqueue.return_value = mock_job
        mock_get_queue.return_value = mock_queue
        
        # Call function
        file_content = b"test file content"
        filename = "test.mp3"
        result = enqueue_file(file_content, filename)
        
        # Check results
        assert result["job_id"] == "job-123"
        assert result["file_id"] == "12345678-1234-5678-1234-567812345678"
        assert result["original_filename"] == "test.mp3"
        assert result["status"] == "queued"
        
        # Verify functions were called
        mock_save_file.assert_called_once_with(file_content, filename, "data/uploads")
        mock_queue.enqueue.assert_called_once()
