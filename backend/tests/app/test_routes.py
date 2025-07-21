"""Tests for routes.py module."""
from unittest import mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.app.routes import router


class TestRoutes:
    """Test class for routes.py module."""

    def setup_method(self):
        """Set up test app for each test method."""
        # Create a FastAPI app for testing
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    @mock.patch("backend.app.routes.enqueue_file")
    async def test_upload_file_success(self, mock_enqueue):
        """Test successful file upload."""
        # Setup mock
        mock_enqueue.return_value = {
            "job_id": "job-123",
            "file_id": "file-123",
            "original_filename": "test.mp3",
            "status": "queued"
        }
        
        # Create test file content
        file_content = b"test audio file content"
        
        # Make API call
        response = self.client.post(
            "/api/v1/transcribe",
            files={"file": ("test.mp3", file_content, "audio/mp3")}
        )
        
        # Check response
        assert response.status_code == 202
        json_response = response.json()
        assert json_response["job_id"] == "job-123"
        assert json_response["file_id"] == "file-123"
        assert json_response["filename"] == "test.mp3"
        assert json_response["status"] == "queued"
        
        # Verify enqueue was called
        mock_enqueue.assert_called_once()
        args, kwargs = mock_enqueue.call_args
        assert args[0] == file_content  # First arg should be file content
        assert args[1] == "test.mp3"    # Second arg should be filename

    async def test_upload_file_invalid_extension(self):
        """Test file upload with invalid extension."""
        # Create test file with invalid extension
        file_content = b"test file content"
        
        # Make API call
        response = self.client.post(
            "/api/v1/transcribe",
            files={"file": ("test.txt", file_content, "text/plain")}
        )
        
        # Check response
        assert response.status_code == 400
        json_response = response.json()
        assert "Unsupported file type" in json_response["detail"]

    @mock.patch("backend.app.routes.enqueue_file")
    async def test_upload_file_server_error(self, mock_enqueue):
        """Test file upload with server error."""
        # Setup mock to raise exception
        mock_enqueue.side_effect = Exception("Server error")
        
        # Create test file content
        file_content = b"test audio file content"
        
        # Make API call
        response = self.client.post(
            "/api/v1/transcribe",
            files={"file": ("test.mp3", file_content, "audio/mp3")}
        )
        
        # Check response
        assert response.status_code == 500
        json_response = response.json()
        assert "Error processing file" in json_response["detail"]
