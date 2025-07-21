"""Tests for queue.py module."""
from unittest import mock

import pytest
import redis
from rq import Queue as RQQueue

from backend.core.worker.queue import Queue, get_queue


class TestQueue:
    """Test class for Queue wrapper."""

    def test_init_with_connection(self):
        """Test Queue initialization with existing connection."""
        mock_conn = mock.MagicMock(spec=redis.Redis)
        queue = Queue(name="test_queue", connection=mock_conn)
        
        assert queue.name == "test_queue"
        assert queue.connection == mock_conn

    @mock.patch("backend.core.worker.queue.get_redis_connection")
    def test_init_without_connection(self, mock_get_redis):
        """Test Queue initialization without connection."""
        mock_conn = mock.MagicMock(spec=redis.Redis)
        mock_get_redis.return_value = mock_conn
        
        queue = Queue(name="test_queue")
        
        assert queue.connection == mock_conn
        mock_get_redis.assert_called_once()

    @mock.patch("backend.core.worker.queue.RQQueue")
    def test_enqueue(self, mock_rq_queue):
        """Test enqueueing a job."""
        # Setup mock
        mock_queue = mock.MagicMock()
        mock_job = mock.MagicMock()
        mock_queue.enqueue.return_value = mock_job
        mock_rq_queue.return_value = mock_queue
        
        # Create queue
        mock_conn = mock.MagicMock(spec=redis.Redis)
        queue = Queue(name="test_queue", connection=mock_conn)
        
        # Test enqueue
        test_func = mock.MagicMock()
        result = queue.enqueue(test_func, "arg1", arg2="value")
        
        # Verify
        assert result == mock_job
        mock_queue.enqueue.assert_called_once_with(test_func, "arg1", arg2="value")

    @mock.patch("backend.core.worker.queue.RQQueue")
    def test_get_job_ids(self, mock_rq_queue):
        """Test getting job IDs."""
        # Setup mock
        mock_queue = mock.MagicMock()
        mock_queue.job_ids = ["job1", "job2"]
        mock_rq_queue.return_value = mock_queue
        
        # Create queue
        mock_conn = mock.MagicMock(spec=redis.Redis)
        queue = Queue(name="test_queue", connection=mock_conn)
        
        # Test getting job IDs
        result = queue.get_job_ids()
        
        # Verify
        assert result == ["job1", "job2"]

    @mock.patch("backend.core.worker.queue.RQQueue")
    def test_get_job_count(self, mock_rq_queue):
        """Test getting job count."""
        # Setup mock
        mock_queue = mock.MagicMock()
        mock_queue.__len__.return_value = 5
        mock_rq_queue.return_value = mock_queue
        
        # Create queue
        mock_conn = mock.MagicMock(spec=redis.Redis)
        queue = Queue(name="test_queue", connection=mock_conn)
        
        # Test getting job count
        result = queue.get_job_count()
        
        # Verify
        assert result == 5
        mock_queue.__len__.assert_called_once()

    @mock.patch("backend.core.worker.queue.Queue")
    def test_get_queue_first_call(self, mock_queue_cls):
        """Test get_queue creates new instance on first call."""
        # Reset module-level variable
        import backend.core.worker.queue
        backend.core.worker.queue._default_queue = None
        
        # Setup mock
        mock_queue_instance = mock.MagicMock()
        mock_queue_cls.return_value = mock_queue_instance
        
        # Call function
        result = get_queue("test_queue")
        
        # Verify
        assert result == mock_queue_instance
        mock_queue_cls.assert_called_once_with(name="test_queue")

    @mock.patch("backend.core.worker.queue.Queue")
    def test_get_queue_subsequent_call(self, mock_queue_cls):
        """Test get_queue returns existing instance on subsequent calls."""
        # Setup mock
        mock_queue_instance = mock.MagicMock()
        
        # Set module-level variable directly
        import backend.core.worker.queue
        backend.core.worker.queue._default_queue = mock_queue_instance
        
        # Call function
        result = get_queue("another_queue")
        
        # Verify that no new queue was created and original was returned
        assert result == mock_queue_instance
        mock_queue_cls.assert_not_called()
        
        # Reset module-level variable for other tests
        backend.core.worker.queue._default_queue = None
