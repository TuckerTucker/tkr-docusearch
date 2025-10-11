"""
Monitoring utilities for long-running operations.

Provides:
- Periodic status updates during blocking operations
- Timeout monitoring to prevent stuck processes
- Context managers for easy integration
"""

import threading
import time
import signal
import logging
from typing import Optional, Callable, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Raised when an operation times out."""
    pass


class PeriodicStatusUpdater:
    """
    Updates status periodically during long-running operations.

    Uses a background thread to send status updates every N seconds,
    preventing documents from appearing "stuck" during blocking operations
    like Docling parsing or Whisper transcription.
    """

    def __init__(
        self,
        update_callback: Callable[[], None],
        interval_seconds: float = 5.0
    ):
        """
        Initialize periodic updater.

        Args:
            update_callback: Function to call periodically (no args)
            interval_seconds: Seconds between updates (default: 5.0)
        """
        self.update_callback = update_callback
        self.interval = interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._update_count = 0

    def start(self):
        """Start periodic updates in background thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("PeriodicStatusUpdater already running")
            return

        self._stop_event.clear()
        self._update_count = 0
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        logger.debug(f"Started periodic status updates (interval: {self.interval}s)")

    def stop(self):
        """Stop periodic updates and wait for thread to finish."""
        if self._thread is None:
            return

        self._stop_event.set()
        self._thread.join(timeout=2.0)

        if self._thread.is_alive():
            logger.warning("PeriodicStatusUpdater thread did not stop cleanly")
        else:
            logger.debug(
                f"Stopped periodic status updates "
                f"({self._update_count} updates sent)"
            )

    def _update_loop(self):
        """Background thread that sends periodic updates."""
        while not self._stop_event.wait(self.interval):
            try:
                self.update_callback()
                self._update_count += 1
            except Exception as e:
                logger.error(f"Error in periodic status update: {e}")
                # Continue anyway - don't stop updates due to callback error

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False  # Don't suppress exceptions


@contextmanager
def periodic_status_updates(
    update_callback: Callable[[], None],
    interval_seconds: float = 5.0
):
    """
    Context manager for periodic status updates.

    Usage:
        with periodic_status_updates(lambda: update_status(...)):
            result = long_running_operation()

    Args:
        update_callback: Function to call periodically
        interval_seconds: Seconds between updates (default: 5.0)
    """
    updater = PeriodicStatusUpdater(update_callback, interval_seconds)
    updater.start()
    try:
        yield updater
    finally:
        updater.stop()


@contextmanager
def operation_timeout(timeout_seconds: int, operation_name: str = "Operation"):
    """
    Context manager for timeout monitoring.

    Raises TimeoutException if operation takes longer than timeout_seconds.

    Usage:
        with operation_timeout(300, "Docling parsing"):
            result = converter.convert(file_path)

    Args:
        timeout_seconds: Maximum seconds before timeout
        operation_name: Name for error messages

    Raises:
        TimeoutException: If operation exceeds timeout
    """
    def timeout_handler(signum, frame):
        raise TimeoutException(
            f"{operation_name} timed out after {timeout_seconds}s"
        )

    # Set up signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    logger.debug(
        f"Starting {operation_name} with {timeout_seconds}s timeout"
    )

    try:
        yield
        # Cancel alarm if operation completes successfully
        signal.alarm(0)
        logger.debug(f"{operation_name} completed within timeout")
    except TimeoutException:
        logger.error(
            f"{operation_name} exceeded timeout of {timeout_seconds}s"
        )
        raise
    finally:
        # Restore original handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


@contextmanager
def monitored_operation(
    status_callback: Optional[Callable[[], None]] = None,
    timeout_seconds: Optional[int] = None,
    operation_name: str = "Operation",
    update_interval: float = 5.0
):
    """
    Combined context manager for both periodic updates and timeout monitoring.

    Usage:
        with monitored_operation(
            status_callback=lambda: update_status(...),
            timeout_seconds=300,
            operation_name="Docling parsing"
        ):
            result = converter.convert(file_path)

    Args:
        status_callback: Optional callback for periodic updates
        timeout_seconds: Optional timeout in seconds
        operation_name: Name for logging/errors
        update_interval: Seconds between status updates (default: 5.0)

    Raises:
        TimeoutException: If operation exceeds timeout
    """
    # Stack context managers
    contexts = []

    if timeout_seconds is not None:
        contexts.append(
            operation_timeout(timeout_seconds, operation_name)
        )

    if status_callback is not None:
        contexts.append(
            periodic_status_updates(status_callback, update_interval)
        )

    # Enter all contexts
    for ctx in contexts:
        ctx.__enter__()

    try:
        yield
    finally:
        # Exit all contexts in reverse order
        for ctx in reversed(contexts):
            try:
                ctx.__exit__(None, None, None)
            except Exception as e:
                logger.error(f"Error exiting context: {e}")


# Convenience function for simple timeout use
def with_timeout(func: Callable, timeout_seconds: int, *args, **kwargs) -> Any:
    """
    Run a function with timeout monitoring.

    Args:
        func: Function to run
        timeout_seconds: Maximum seconds before timeout
        *args, **kwargs: Arguments to pass to func

    Returns:
        Function return value

    Raises:
        TimeoutException: If function exceeds timeout
    """
    with operation_timeout(timeout_seconds, func.__name__):
        return func(*args, **kwargs)
