"""Worker runner module for RQ."""
import os
import sys
from redis import Redis
from rq import Connection, Worker

def start_worker(queue_name="transcription", burst=False):
    """Start RQ worker for processing transcription jobs.
    
    Args:
        queue_name: Name of the queue to process. Default is "transcription".
        burst: If True, worker processes all available jobs and exits. Default is False.
    """
    # Allow queue name override via environment variable
    queue_name = os.environ.get("QUEUE_NAME", queue_name)
    
    # Get Redis connection params from environment or use defaults
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    
    print(f"Starting worker for queue: {queue_name}")
    print(f"Redis connection: {redis_host}:{redis_port}")
    
    # Connect to Redis
    redis_conn = Redis(host=redis_host, port=redis_port)
    
    # Start worker
    with Connection(redis_conn):
        worker = Worker([queue_name])
        worker.work(burst=burst)

if __name__ == "__main__":
    # Optional command line argument for queue name
    queue_name = sys.argv[1] if len(sys.argv) > 1 else "transcription"
    start_worker(queue_name)
