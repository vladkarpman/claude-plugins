"""Frame buffer for storing and analyzing recent frames."""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import List, Optional, Tuple

import numpy as np

try:
    from PIL import Image
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False


class FrameBuffer:
    """Circular buffer holding recent frames for analysis."""

    def __init__(self, max_frames: int = 120, max_seconds: float = 2.0):
        """
        Initialize frame buffer.

        Args:
            max_frames: Maximum number of frames to keep
            max_seconds: Maximum age of frames in seconds
        """
        self.max_frames = max_frames
        self.max_seconds = max_seconds
        self.frames: deque[Tuple[float, np.ndarray]] = deque(maxlen=max_frames)
        self.lock = threading.Lock()

    def add_frame(self, frame: np.ndarray, timestamp: Optional[float] = None) -> None:
        """
        Add a frame to the buffer.

        Args:
            frame: Frame as numpy array (BGR format from scrcpy)
            timestamp: Frame timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()

        with self.lock:
            self.frames.append((timestamp, frame.copy()))
            self._cleanup_old()

    def _cleanup_old(self) -> None:
        """Remove frames older than max_seconds."""
        if not self.frames:
            return

        cutoff = time.time() - self.max_seconds
        while self.frames and self.frames[0][0] < cutoff:
            self.frames.popleft()

    def get_latest(self) -> Tuple[Optional[np.ndarray], float]:
        """
        Get the most recent frame.

        Returns:
            Tuple of (frame, timestamp) or (None, 0) if empty
        """
        with self.lock:
            if self.frames:
                ts, frame = self.frames[-1]
                return frame.copy(), ts
            return None, 0

    def get_frame_count(self) -> int:
        """Get number of frames in buffer."""
        with self.lock:
            return len(self.frames)

    def get_recent(self, n: int) -> List[Tuple[float, np.ndarray]]:
        """
        Get the N most recent frames.

        Args:
            n: Number of frames to get

        Returns:
            List of (timestamp, frame) tuples, newest last
        """
        with self.lock:
            frames = list(self.frames)[-n:]
            return [(ts, frame.copy()) for ts, frame in frames]

    def get_around(
        self,
        timestamp: float,
        before: int = 3,
        after: int = 5
    ) -> List[Tuple[float, np.ndarray]]:
        """
        Get frames around a specific timestamp.

        Args:
            timestamp: Target timestamp
            before: Number of frames before timestamp
            after: Number of frames after timestamp

        Returns:
            List of (timestamp, frame) tuples around the target time
        """
        with self.lock:
            frames = list(self.frames)

        if not frames:
            return []

        # Find the closest frame to the timestamp
        closest_idx = 0
        min_diff = float('inf')
        for i, (ts, _) in enumerate(frames):
            diff = abs(ts - timestamp)
            if diff < min_diff:
                min_diff = diff
                closest_idx = i

        # Get frames around it
        start = max(0, closest_idx - before)
        end = min(len(frames), closest_idx + after + 1)

        return [(ts, frame.copy()) for ts, frame in frames[start:end]]

    def _compute_hash(self, frame: np.ndarray) -> Optional[object]:
        """Compute perceptual hash of a frame."""
        if not IMAGEHASH_AVAILABLE:
            return None

        try:
            # Convert BGR to RGB
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                rgb = frame[:, :, ::-1]
            else:
                rgb = frame

            img = Image.fromarray(rgb)
            return imagehash.phash(img)
        except Exception:
            return None

    def frames_differ(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray,
        threshold: float = 0.95
    ) -> bool:
        """
        Check if two frames are significantly different.

        Args:
            frame1: First frame
            frame2: Second frame
            threshold: Similarity threshold (0-1, higher = more similar required)

        Returns:
            True if frames are different, False if similar
        """
        if IMAGEHASH_AVAILABLE:
            hash1 = self._compute_hash(frame1)
            hash2 = self._compute_hash(frame2)
            if hash1 is not None and hash2 is not None:
                # imagehash difference: 0 = identical, higher = more different
                diff = hash1 - hash2
                # Convert to similarity (64 is max diff for phash)
                similarity = 1 - (diff / 64.0)
                return similarity < threshold

        # Fallback: simple pixel comparison (less accurate but works)
        if frame1.shape != frame2.shape:
            return True

        # Downsample for speed
        scale = 8
        h, w = frame1.shape[:2]
        small1 = frame1[::scale, ::scale]
        small2 = frame2[::scale, ::scale]

        # Mean absolute difference
        diff = np.mean(np.abs(small1.astype(float) - small2.astype(float)))
        # Normalize to 0-1 (255 max diff per pixel)
        similarity = 1 - (diff / 255.0)
        return similarity < threshold

    def is_stable(self, threshold: float = 0.98, samples: int = 3) -> bool:
        """
        Check if the screen is stable (recent frames are similar).

        Args:
            threshold: Similarity threshold (0-1)
            samples: Number of recent frames to compare

        Returns:
            True if screen is stable, False if still changing
        """
        with self.lock:
            if len(self.frames) < samples:
                return False

            recent = [frame for _, frame in list(self.frames)[-samples:]]

        # Compare consecutive frames
        for i in range(len(recent) - 1):
            if self.frames_differ(recent[i], recent[i + 1], threshold):
                return False

        return True

    def wait_stable(
        self,
        timeout: float = 5.0,
        threshold: float = 0.98,
        check_interval: float = 0.1
    ) -> bool:
        """
        Block until screen is stable or timeout.

        Args:
            timeout: Maximum wait time in seconds
            threshold: Similarity threshold for stability
            check_interval: Time between stability checks

        Returns:
            True if stable, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            if self.is_stable(threshold=threshold):
                return True
            time.sleep(check_interval)
        return False

    def get_timestamps_diff(
        self,
        ts1: float,
        ts2: float
    ) -> bool:
        """
        Check if screen changed between two timestamps.

        Args:
            ts1: First timestamp
            ts2: Second timestamp

        Returns:
            True if screen changed, False if same
        """
        frames1 = self.get_around(ts1, before=0, after=1)
        frames2 = self.get_around(ts2, before=0, after=1)

        if not frames1 or not frames2:
            return True  # Assume different if we can't compare

        _, frame1 = frames1[0]
        _, frame2 = frames2[0]

        return self.frames_differ(frame1, frame2)

    def clear(self) -> None:
        """Clear all frames from buffer."""
        with self.lock:
            self.frames.clear()

    def get_duration(self) -> float:
        """Get time span of buffered frames in seconds."""
        with self.lock:
            if len(self.frames) < 2:
                return 0
            return self.frames[-1][0] - self.frames[0][0]

    def get_fps(self) -> float:
        """Estimate current frame rate."""
        with self.lock:
            if len(self.frames) < 2:
                return 0
            duration = self.frames[-1][0] - self.frames[0][0]
            if duration <= 0:
                return 0
            return (len(self.frames) - 1) / duration
