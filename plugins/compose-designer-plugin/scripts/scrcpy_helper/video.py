"""Video recording from frame buffer."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class VideoRecorder:
    """Records frames to video file."""

    def __init__(self, output_dir: str = "tests/videos"):
        self.output_dir = Path(output_dir)
        self.recording = False
        self.frames: List[Tuple[float, np.ndarray]] = []
        self.start_time: float = 0
        self.lock = threading.Lock()

    def _log(self, message: str) -> None:
        """Log to stderr."""
        print(f"[video-recorder] {message}", file=sys.stderr)

    def start(self) -> bool:
        """Start recording frames."""
        with self.lock:
            if self.recording:
                return False

            self.frames = []
            self.start_time = time.time()
            self.recording = True
            self._log("Recording started")
            return True

    def add_frame(self, frame: np.ndarray, timestamp: float) -> None:
        """Add a frame to the recording."""
        if not self.recording:
            return

        with self.lock:
            self.frames.append((timestamp, frame.copy()))

    def stop(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Stop recording and save video.

        Args:
            filename: Output filename (without extension). If None, auto-generated.

        Returns:
            Path to saved video file, or None on failure.
        """
        with self.lock:
            if not self.recording:
                return None

            self.recording = False
            frames = self.frames.copy()
            self.frames = []

        if not frames:
            self._log("No frames to save")
            return None

        # Generate filename if not provided
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}"

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Try to save as video using ffmpeg
        output_path = self.output_dir / f"{filename}.mp4"
        if self._save_with_ffmpeg(frames, output_path):
            self._log(f"Saved video: {output_path}")
            return str(output_path)

        # Fallback: save as image sequence
        seq_dir = self.output_dir / filename
        if self._save_as_images(frames, seq_dir):
            self._log(f"Saved image sequence: {seq_dir}")
            return str(seq_dir)

        return None

    def _save_with_ffmpeg(
        self,
        frames: List[Tuple[float, np.ndarray]],
        output_path: Path
    ) -> bool:
        """Save frames as video using ffmpeg."""
        # Check if ffmpeg is available
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            self._log("ffmpeg not available, falling back to image sequence")
            return False

        if not PIL_AVAILABLE:
            self._log("Pillow not available for image conversion")
            return False

        # Calculate frame rate from timestamps
        if len(frames) < 2:
            fps = 30
        else:
            duration = frames[-1][0] - frames[0][0]
            fps = len(frames) / duration if duration > 0 else 30

        fps = min(max(fps, 1), 60)  # Clamp to reasonable range

        # Create temporary directory for frames
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Save frames as images
            for i, (ts, frame) in enumerate(frames):
                # Convert BGR to RGB
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    rgb = frame[:, :, ::-1]
                else:
                    rgb = frame

                img = Image.fromarray(rgb)
                img.save(tmpdir_path / f"frame_{i:06d}.png")

            # Run ffmpeg
            try:
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",  # Overwrite output
                        "-framerate", str(int(fps)),
                        "-i", str(tmpdir_path / "frame_%06d.png"),
                        "-c:v", "libx264",
                        "-preset", "fast",
                        "-crf", "23",
                        "-pix_fmt", "yuv420p",
                        str(output_path)
                    ],
                    capture_output=True,
                    check=True
                )
                return True
            except subprocess.SubprocessError as e:
                self._log(f"ffmpeg failed: {e}")
                return False

    def _save_as_images(
        self,
        frames: List[Tuple[float, np.ndarray]],
        output_dir: Path
    ) -> bool:
        """Save frames as image sequence."""
        if not PIL_AVAILABLE:
            self._log("Pillow not available")
            return False

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            for i, (ts, frame) in enumerate(frames):
                # Convert BGR to RGB
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    rgb = frame[:, :, ::-1]
                else:
                    rgb = frame

                img = Image.fromarray(rgb)
                img.save(output_dir / f"frame_{i:06d}_{ts:.3f}.png")

            # Save metadata
            with open(output_dir / "metadata.txt", "w") as f:
                f.write(f"frames: {len(frames)}\n")
                f.write(f"start_time: {frames[0][0]}\n")
                f.write(f"end_time: {frames[-1][0]}\n")
                f.write(f"duration: {frames[-1][0] - frames[0][0]:.3f}s\n")

            return True
        except Exception as e:
            self._log(f"Failed to save images: {e}")
            return False

    def get_status(self) -> dict:
        """Get recording status."""
        with self.lock:
            return {
                "recording": self.recording,
                "frames": len(self.frames),
                "duration": time.time() - self.start_time if self.recording else 0,
            }
