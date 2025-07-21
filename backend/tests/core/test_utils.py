"""Tests for utils.py module."""
import os
from unittest import mock

import pytest
import redis

from backend.core.utils import get_redis_connection


class TestUtils:
    """Test class for utils.py module."""

    @mock.patch("redis.Redis")
    def test_get_redis_connection_default(self, mock_redis_cls):
        """Test get_redis_connection with default parameters."""
        # Setup environment
        with mock.patch.dict(os.environ, {}, clear=True):
            # Call function
            get_redis_connection()
            
            # Verify
            mock_redis_cls.assert_called_once_with(host="localhost", port=6379)

    @mock.patch("redis.Redis")
    def test_get_redis_connection_from_env(self, mock_redis_cls):
        """Test get_redis_connection with environment variables."""
        # Setup environment
        with mock.patch.dict(os.environ, {"REDIS_HOST": "redis.example.com", "REDIS_PORT": "6380"}, clear=True):
            # Call function
            get_redis_connection()
            
            # Verify
            mock_redis_cls.assert_called_once_with(host="redis.example.com", port=6380)

    @mock.patch("redis.Redis")
    def test_get_redis_connection_params(self, mock_redis_cls):
        """Test get_redis_connection with explicit parameters."""
        # Call function with explicit parameters
        get_redis_connection(host="custom.redis.host", port=1234)
        
        # Verify
        mock_redis_cls.assert_called_once_with(host="custom.redis.host", port=1234)

    @mock.patch("redis.Redis")
    def test_get_redis_connection_mixed_params(self, mock_redis_cls):
        """Test get_redis_connection with mixed parameters and env variables."""
        # Setup environment with one parameter
        with mock.patch.dict(os.environ, {"REDIS_PORT": "6380"}, clear=True):
            # Call function with the other parameter
            get_redis_connection(host="custom.redis.host")
            
            # Verify - should use explicit host and env var port
            mock_redis_cls.assert_called_once_with(host="custom.redis.host", port=6380)
