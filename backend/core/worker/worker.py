"""Worker script to process jobs from Redis queue."""
import argparse
import os
import sys

import redis
from rq import Connection, Worker


def run_worker(queue_names=None):
    """Run worker process to handle jobs from Redis queue.

    Args:
        queue_names: Names of queues to listen to. Defaults to ["transcription"].
    """
    if queue_names is None:
        queue_names = ["transcription"]

    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    redis_connection = redis.Redis(host=redis_host, port=redis_port)

    with Connection(redis_connection):
        worker = Worker(queue_names)
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RQ worker for transcription processing")
    parser.add_argument(
        "--queues",
        type=str,
        default="transcription",
        help="Queue names to listen to (comma separated)",
    )

    args = parser.parse_args()
    queue_names = [q.strip() for q in args.queues.split(",")]

    run_worker(queue_names)
