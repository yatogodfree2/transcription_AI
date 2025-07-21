"""Script to launch the full transcription pipeline (API and worker) in parallel."""
import os
import signal
import subprocess
import sys
import time
from typing import Dict

# Default configuration
DEFAULT_CONFIG = {
    "api_host": "0.0.0.0",
    "api_port": 8001,  # Using 8001 since 8000 might be occupied
    "queue_name": "transcription",
    "redis_host": "localhost",
    "redis_port": 6379,
}

# Global process registry
processes: Dict[str, subprocess.Popen] = {}


def signal_handler(sig, frame):
    """Handle interruption signals by gracefully stopping all processes."""
    print("\n\nShutting down pipeline...")
    stop_all_processes()
    sys.exit(0)


def stop_all_processes():
    """Stop all registered processes gracefully."""
    for name, process in processes.items():
        if process.poll() is None:  # If process is still running
            print(f"Stopping {name}...")
            process.terminate()
            
    # Wait for processes to terminate gracefully
    for name, process in processes.items():
        try:
            process.wait(timeout=5)
            print(f"{name} stopped.")
        except subprocess.TimeoutExpired:
            print(f"Force killing {name}...")
            process.kill()


def start_api(host: str = DEFAULT_CONFIG["api_host"], port: int = DEFAULT_CONFIG["api_port"]):
    """Start FastAPI server using the Poetry script."""
    env = os.environ.copy()
    env["API_PORT"] = str(port)
    
    print(f"Starting API server at http://{host}:{port}")
    api_process = subprocess.Popen(
        ["poetry", "run", "api"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    processes["api"] = api_process
    return api_process


def start_worker(queue_name: str = DEFAULT_CONFIG["queue_name"]):
    """Start RQ worker using the Poetry script."""
    env = os.environ.copy()
    env["QUEUE_NAME"] = queue_name
    
    print(f"Starting worker for queue: {queue_name}")
    worker_process = subprocess.Popen(
        ["poetry", "run", "worker"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    processes["worker"] = worker_process
    return worker_process


def print_process_output():
    """Print output from all running processes in real-time."""
    while True:
        for name, process in processes.items():
            # Check if process is still running
            if process.poll() is not None:
                print(f"\n{name} exited with code {process.returncode}")
                
            # Print any available output
            if hasattr(process, "stdout") and process.stdout:
                while True:
                    output = process.stdout.readline()
                    if output:
                        print(f"[{name}] {output.strip()}")
                    else:
                        break
                        
        # If all processes have exited, break the loop
        if all(p.poll() is not None for p in processes.values()):
            print("All processes have exited.")
            break
            
        # Sleep briefly to avoid high CPU usage
        time.sleep(0.1)


def start_pipeline():
    """Start the full transcription pipeline with API and worker."""
    print("Starting transcription pipeline...")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start API server
    api_process = start_api()
    
    # Wait a moment to ensure the API is starting up
    time.sleep(2)
    
    # Start worker
    worker_process = start_worker()
    
    # Print startup message
    print("\n" + "=" * 60)
    print("Transcription Pipeline Started!")
    print("-" * 60)
    print(f"API server running at: http://{DEFAULT_CONFIG['api_host']}:{DEFAULT_CONFIG['api_port']}")
    print(f"API endpoints:")
    print(f"  - Upload audio: POST http://{DEFAULT_CONFIG['api_host']}:{DEFAULT_CONFIG['api_port']}/api/v1/transcribe")
    print(f"  - Swagger UI:   http://{DEFAULT_CONFIG['api_host']}:{DEFAULT_CONFIG['api_port']}/docs")
    print("-" * 60)
    print("Press Ctrl+C to stop the pipeline")
    print("=" * 60 + "\n")
    
    # Continuously print process output until they exit
    try:
        print_process_output()
    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_all_processes()
    
    print("Pipeline shutdown complete.")


if __name__ == "__main__":
    start_pipeline()
