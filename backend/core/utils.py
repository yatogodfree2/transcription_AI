"""Shared utilities for the application."""
import os
from typing import Optional

import redis


def get_redis_connection(host: Optional[str] = None, port: Optional[int] = None) -> redis.Redis:
    """Get Redis connection with parameters from environment or defaults.
    
    Args:
        host: Redis host. If None, will use REDIS_HOST environment variable or default to 'localhost'.
        port: Redis port. If None, will use REDIS_PORT environment variable or default to 6379.
        
    Returns:
        redis.Redis: Redis connection.
    """
    # Get Redis connection params from environment or use defaults/provided values
    redis_host = host or os.environ.get("REDIS_HOST", "localhost")
    redis_port = port or int(os.environ.get("REDIS_PORT", 6379))
    
    return redis.Redis(host=redis_host, port=redis_port)
