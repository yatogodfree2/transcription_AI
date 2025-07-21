"""Tests for main.py module."""
import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app, run_api


class TestMain:
    """Test class for main.py module."""

    def setup_method(self):
        """Set up test client for each test method."""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test the root endpoint returns expected response."""
        response = self.client.get("/")
        assert response.status_code == 200
        
        json_data = response.json()
        assert "message" in json_data
        assert "status" in json_data
        assert "version" in json_data
        assert json_data["status"] == "operational"

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @mock.patch("backend.app.main.uvicorn.run")
    def test_run_api_default(self, mock_run):
        """Test run_api with default parameters."""
        # Setup environment
        with mock.patch.dict(os.environ, {}, clear=True):
            # Call function
            run_api()
            
            # Verify
            mock_run.assert_called_once_with(
                "backend.app.main:app", 
                host="0.0.0.0", 
                port=8000, 
                reload=True
            )

    @mock.patch("backend.app.main.uvicorn.run")
    def test_run_api_custom_params(self, mock_run):
        """Test run_api with custom parameters."""
        # Call function with custom parameters
        run_api(host="127.0.0.1", port=9000)
        
        # Verify
        mock_run.assert_called_once_with(
            "backend.app.main:app", 
            host="127.0.0.1", 
            port=9000, 
            reload=True
        )

    @mock.patch("backend.app.main.uvicorn.run")
    def test_run_api_env_override(self, mock_run):
        """Test run_api with environment variable overrides."""
        # Setup environment with port override
        with mock.patch.dict(os.environ, {"API_PORT": "5000"}, clear=True):
            # Call function with default parameters
            run_api()
            
            # Verify port was overridden from env
            mock_run.assert_called_once_with(
                "backend.app.main:app", 
                host="0.0.0.0", 
                port=5000,  # Should use env var
                reload=True
            )
