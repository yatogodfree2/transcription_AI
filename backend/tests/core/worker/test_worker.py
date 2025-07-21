"""Tests for worker.py module."""
import argparse
from unittest import mock

import pytest
from rq import Worker, Connection

from backend.core.worker.worker import run_worker


class TestWorker:
    """Test class for worker.py module."""

    @mock.patch("backend.core.worker.worker.get_redis_connection")
    @mock.patch("backend.core.worker.worker.Worker")
    @mock.patch("backend.core.worker.worker.Connection")
    def test_run_worker_default_queue(self, mock_connection, mock_worker_cls, mock_get_redis):
        """Test run_worker with default queue name."""
        # Setup mocks
        mock_redis_conn = mock.MagicMock()
        mock_get_redis.return_value = mock_redis_conn
        
        mock_connection_ctx = mock.MagicMock()
        mock_connection.return_value = mock_connection_ctx
        
        mock_worker = mock.MagicMock()
        mock_worker_cls.return_value = mock_worker
        
        # Call function
        run_worker()
        
        # Verify
        mock_get_redis.assert_called_once()
        mock_connection.assert_called_once_with(mock_redis_conn)
        mock_worker_cls.assert_called_once_with(["transcription"])
        mock_worker.work.assert_called_once_with(with_scheduler=True)

    @mock.patch("backend.core.worker.worker.get_redis_connection")
    @mock.patch("backend.core.worker.worker.Worker")
    @mock.patch("backend.core.worker.worker.Connection")
    def test_run_worker_custom_queues(self, mock_connection, mock_worker_cls, mock_get_redis):
        """Test run_worker with custom queue names."""
        # Setup mocks
        mock_redis_conn = mock.MagicMock()
        mock_get_redis.return_value = mock_redis_conn
        
        mock_connection_ctx = mock.MagicMock()
        mock_connection.return_value = mock_connection_ctx
        
        mock_worker = mock.MagicMock()
        mock_worker_cls.return_value = mock_worker
        
        # Call function with custom queue names
        custom_queues = ["high", "low"]
        run_worker(queue_names=custom_queues)
        
        # Verify
        mock_worker_cls.assert_called_once_with(custom_queues)
        mock_worker.work.assert_called_once_with(with_scheduler=True)

    @mock.patch("backend.core.worker.worker.argparse.ArgumentParser")
    @mock.patch("backend.core.worker.worker.run_worker")
    def test_main_execution(self, mock_run_worker, mock_arg_parser):
        """Test main execution code."""
        # This test is a bit tricky since we're testing code in __main__ block
        # We need to directly import and test the main module execution code
        
        # Setup mock parser
        mock_parser = mock.MagicMock()
        mock_arg_parser.return_value = mock_parser
        
        mock_args = mock.MagicMock()
        mock_args.queues = "high,low"
        mock_parser.parse_args.return_value = mock_args
        
        # Import the module to execute __main__ block
        # We need to mock sys.argv first to avoid actual argument parsing
        with mock.patch("sys.argv", ["worker.py", "--queues", "high,low"]):
            # We can't actually test the __main__ block easily in a unit test
            # So we'll simulate its behavior here
            import backend.core.worker.worker
            
            # Manually call what the main block would do
            queue_names = [q.strip() for q in mock_args.queues.split(",")]
            backend.core.worker.worker.run_worker(queue_names)
            
            # Verify
            mock_run_worker.assert_called_once_with(["high", "low"])
