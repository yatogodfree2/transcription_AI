"""Queue management for Redis RQ."""
from typing import Optional

import redis
from rq import Queue as RQQueue

from backend.core.utils import get_redis_connection


class Queue:
    """Wrapper around Redis RQ queue."""

    def __init__(self, name: str = "transcription", connection: Optional[redis.Redis] = None):
        """Initialize queue with Redis connection.

        Args:
            name: Name of the queue.
            connection: Redis connection. If None, a new connection will be created.
        """
        if connection is None:
            connection = get_redis_connection()

        self._queue = RQQueue(name=name, connection=connection)
        self.name = name
        self.connection = connection

    def enqueue(self, func, *args, **kwargs):
        """Enqueue a job to the queue.

        Args:
            func: Function to execute.
            *args: Arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            rq.Job: Job object.
        """
        job = self._queue.enqueue(func, *args, **kwargs)
        return job

    def get_job_ids(self):
        """Get all job IDs in the queue.

        Returns:
            list: List of job IDs.
        """
        return self._queue.job_ids

    def get_job_count(self):
        """Get number of jobs in the queue.

        Returns:
            int: Number of jobs.
        """
        return len(self._queue)


_default_queue = None


def get_queue(name: str = "transcription") -> Queue:
    """Get default queue instance.

    Args:
        name: Name of the queue.

    Returns:
        Queue: Queue instance.
    """
    global _default_queue
    if _default_queue is None:
        _default_queue = Queue(name=name)
    return _default_queue
