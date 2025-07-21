"""Script to run the worker for processing transcription jobs."""
import os
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.core.worker.worker import run_worker

if __name__ == "__main__":
    print("Starting transcription worker...")
    run_worker(["transcription"])
