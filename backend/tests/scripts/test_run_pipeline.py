"""Tests for run_pipeline.py module."""
import signal
import sys
import time
from unittest import mock

import pytest

from backend.scripts.run_pipeline import (
    signal_handler,
    stop_all_processes,
    start_api,
    start_worker,
    print_process_output,
    start_pipeline,
    DEFAULT_CONFIG,
    processes
)


class TestRunPipeline:
    """Test class for run_pipeline.py module."""

    def setup_method(self):
        """Set up test environment for each test."""
        # Clear global processes dict before each test
        processes.clear()

    def teardown_method(self):
        """Clean up after each test."""
        # Clear global processes dict after each test
        processes.clear()

    @mock.patch("backend.scripts.run_pipeline.stop_all_processes")
    @mock.patch("sys.exit")
    def test_signal_handler(self, mock_exit, mock_stop_all):
        """Test signal handler function."""
        # Call function
        signal_handler(signal.SIGINT, None)
        
        # Verify
        mock_stop_all.assert_called_once()
        mock_exit.assert_called_once_with(0)

    def test_stop_all_processes_running(self):
        """Test stop_all_processes when processes are running."""
        # Setup mock processes
        mock_process1 = mock.MagicMock()
        mock_process1.poll.return_value = None  # Process is running
        
        mock_process2 = mock.MagicMock()
        mock_process2.poll.return_value = None  # Process is running
        
        # Add to processes dict
        processes["api"] = mock_process1
        processes["worker"] = mock_process2
        
        # Call function
        stop_all_processes()
        
        # Verify processes were terminated
        mock_process1.terminate.assert_called_once()
        mock_process2.terminate.assert_called_once()
        mock_process1.wait.assert_called_once()
        mock_process2.wait.assert_called_once()

    def test_stop_all_processes_timeout(self):
        """Test stop_all_processes when process doesn't terminate in time."""
        # Setup mock process that times out
        mock_process = mock.MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.wait.side_effect = subprocess.TimeoutExpired("cmd", 5)
        
        # Add to processes dict
        processes["api"] = mock_process
        
        # Call function
        stop_all_processes()
        
        # Verify process was killed after timeout
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        mock_process.kill.assert_called_once()

    @mock.patch("subprocess.Popen")
    def test_start_api(self, mock_popen):
        """Test start_api function."""
        # Setup mock
        mock_process = mock.MagicMock()
        mock_popen.return_value = mock_process
        
        # Call function
        result = start_api()
        
        # Verify
        assert result == mock_process
        assert processes["api"] == mock_process
        mock_popen.assert_called_once()
        
        # Verify correct command and parameters
        args, kwargs = mock_popen.call_args
        assert args[0] == ["poetry", "run", "api"]
        assert kwargs["env"] is not None

    @mock.patch("subprocess.Popen")
    def test_start_worker(self, mock_popen):
        """Test start_worker function."""
        # Setup mock
        mock_process = mock.MagicMock()
        mock_popen.return_value = mock_process
        
        # Call function
        result = start_worker("test_queue")
        
        # Verify
        assert result == mock_process
        assert processes["worker"] == mock_process
        mock_popen.assert_called_once()
        
        # Verify correct command and parameters
        args, kwargs = mock_popen.call_args
        assert args[0] == ["poetry", "run", "worker"]
        assert kwargs["env"] is not None
        assert kwargs["env"].get("QUEUE_NAME") == "test_queue"

    @mock.patch("time.sleep")
    def test_print_process_output_exited(self, mock_sleep):
        """Test print_process_output when processes have exited."""
        # Setup mock process that has exited
        mock_process = mock.MagicMock()
        mock_process.poll.return_value = 0  # Process has exited
        mock_process.stdout.readline.return_value = ""  # No output
        
        # Add to processes dict
        processes["api"] = mock_process
        
        # Call function
        print_process_output()
        
        # Verify
        mock_process.poll.assert_called()
        mock_process.stdout.readline.assert_called()

    @mock.patch("time.sleep", side_effect=KeyboardInterrupt)  # Raise KeyboardInterrupt to exit loop
    def test_print_process_output_with_output(self, mock_sleep):
        """Test print_process_output with process output."""
        # Setup mock process with output
        mock_process = mock.MagicMock()
        mock_process.poll.return_value = None  # Process still running
        mock_process.stdout.readline.side_effect = ["Output line 1", "Output line 2", ""]
        
        # Add to processes dict
        processes["api"] = mock_process
        
        # Call function - will exit due to KeyboardInterrupt from mock
        with pytest.raises(KeyboardInterrupt):
            print_process_output()
        
        # Verify
        mock_process.poll.assert_called()
        assert mock_process.stdout.readline.call_count >= 3

    @mock.patch("backend.scripts.run_pipeline.start_api")
    @mock.patch("backend.scripts.run_pipeline.start_worker")
    @mock.patch("backend.scripts.run_pipeline.signal.signal")
    @mock.patch("backend.scripts.run_pipeline.time.sleep")
    @mock.patch("backend.scripts.run_pipeline.print_process_output")
    def test_start_pipeline(self, mock_print_output, mock_sleep, mock_signal, 
                          mock_start_worker, mock_start_api):
        """Test start_pipeline function."""
        # Call function
        start_pipeline()
        
        # Verify
        mock_start_api.assert_called_once()
        mock_start_worker.assert_called_once()
        mock_print_output.assert_called_once()
        
        # Verify signal handlers were set
        assert mock_signal.call_count == 2
        signal_calls = [call[0][0] for call in mock_signal.call_args_list]
        assert signal.SIGINT in signal_calls
        assert signal.SIGTERM in signal_calls

    @mock.patch("backend.scripts.run_pipeline.start_api")
    @mock.patch("backend.scripts.run_pipeline.start_worker")
    @mock.patch("backend.scripts.run_pipeline.signal.signal")
    @mock.patch("backend.scripts.run_pipeline.time.sleep")
    @mock.patch("backend.scripts.run_pipeline.print_process_output", side_effect=KeyboardInterrupt)
    @mock.patch("backend.scripts.run_pipeline.stop_all_processes")
    def test_start_pipeline_keyboard_interrupt(self, mock_stop_all, mock_print_output, 
                                             mock_sleep, mock_signal, 
                                             mock_start_worker, mock_start_api):
        """Test start_pipeline function with KeyboardInterrupt."""
        # Call function
        start_pipeline()
        
        # Verify
        mock_stop_all.assert_called_once()
        mock_start_api.assert_called_once()
        mock_start_worker.assert_called_once()
