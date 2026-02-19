"""Timelapse capture service — periodic snapshots assembled into video."""

import logging
import os
import shutil
import subprocess

log = logging.getLogger("timelapse")

import tempfile
import threading
import time
from datetime import datetime


_DEFAULT_INTERVAL_SEC = 30
_DEFAULT_MAX_VIDEOS = 10
_SNAPSHOT_TIMEOUT = 10


class TimelapseService:
    """Captures periodic snapshots during a print and assembles a timelapse video."""

    def __init__(self, config_manager, captures_dir=None):
        self._config_manager = config_manager
        self._captures_dir = captures_dir or os.getenv("TIMELAPSE_CAPTURES_DIR", "/captures")
        os.makedirs(self._captures_dir, exist_ok=True)

        self._lock = threading.Lock()
        self._capture_thread = None
        self._stop_event = threading.Event()
        self._current_dir = None
        self._current_filename = None
        self._frame_count = 0

        # Set defaults to ensure attributes exist even if config is None
        self._enabled = False
        self._interval = _DEFAULT_INTERVAL_SEC
        self._max_videos = _DEFAULT_MAX_VIDEOS
        self._save_persistent = True

        self.reload_config()

    def reload_config(self, config=None):
        """Update configuration from Config object or ConfigManager."""
        # If no config passed, use stored config_manager
        if config is None:
            config = self._config_manager

        # If config is a ConfigManager (has .open() method), load the actual config
        if config and hasattr(config, 'open'):
            with config.open() as cfg:
                config = cfg

        if not config or not getattr(config, 'timelapse', None):
            return

        cfg = config.timelapse
        self._enabled = cfg.get("enabled", False)
        self._interval = int(cfg.get("interval", _DEFAULT_INTERVAL_SEC))
        self._max_videos = int(cfg.get("max_videos", _DEFAULT_MAX_VIDEOS))
        self._save_persistent = cfg.get("save_persistent", True)
        
        # Output dir updates might require restart or migration, ignoring for now unless changed?
        # self._captures_dir is tricky to change at runtime if we have existing files.
        # We'll stick to env var or init param for captures_dir for now to avoid complexity.

        self._lock = threading.Lock()
        self._capture_thread = None
        self._stop_event = threading.Event()
        self._current_dir = None
        self._current_filename = None
        self._frame_count = 0

    @property
    def enabled(self):
        return self._enabled

    def start_capture(self, filename="unknown"):
        """Begin periodic snapshot capture for a new print."""
        if not self._enabled:
            return
        if not shutil.which("ffmpeg"):
            log.warning("Timelapse: ffmpeg not available, skipping")
            return

        with self._lock:
            self._stop_capture_thread()

            self._current_filename = filename
            self._current_dir = tempfile.mkdtemp(prefix="timelapse_")
            self._frame_count = 0
            self._stop_event.clear()

            self._capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True,
                name="timelapse-capture",
            )
            self._capture_thread.start()
            log.info(f"Timelapse: started capture for '{filename}' (interval={self._interval}s)")

    def finish_capture(self):
        """Stop capture and assemble video from frames."""
        if not self._enabled:
            return
        with self._lock:
            self._stop_capture_thread()
            if not self._current_dir or self._frame_count < 2:
                log.info("Timelapse: not enough frames, skipping assembly")
                self._cleanup_temp()
                return
            self._assemble_video()
            self._cleanup_temp()
            self._prune_old_videos()

    def fail_capture(self):
        """Stop capture on failure — assemble partial timelapse if frames exist."""
        if not self._enabled:
            return
        with self._lock:
            self._stop_capture_thread()
            if self._current_dir and self._frame_count >= 2:
                log.info("Timelapse: print failed, assembling partial timelapse")
                self._assemble_video(suffix="_partial")
            self._cleanup_temp()

    def _stop_capture_thread(self):
        if self._capture_thread and self._capture_thread.is_alive():
            self._stop_event.set()
            self._capture_thread.join(timeout=5)
            self._capture_thread = None

    def _capture_loop(self):
        """Periodically capture snapshots from the video stream."""
        while not self._stop_event.is_set():
            try:
                self._take_snapshot()
            except Exception as err:
                log.warning(f"Timelapse: snapshot failed: {err}")
            self._stop_event.wait(self._interval)

    def _take_snapshot(self):
        """Capture a single frame using ffmpeg."""
        from web import app  # Lazy import to avoid circular deps

        host = os.getenv("FLASK_HOST") or "127.0.0.1"
        if host in {"0.0.0.0", "::"}:
            host = "127.0.0.1"
        port = os.getenv("FLASK_PORT") or "4470"
        url = f"http://{host}:{port}/video?for_timelapse=1"

        frame_path = os.path.join(self._current_dir, f"frame_{self._frame_count:05d}.jpg")
        result = subprocess.run(
            [
                "ffmpeg", "-loglevel", "error", "-nostdin", "-y",
                "-f", "h264", "-i", url,
                "-frames:v", "1",
                frame_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_SNAPSHOT_TIMEOUT,
        )
        if result.returncode != 0:
            # Retry without format hint
            result = subprocess.run(
                [
                    "ffmpeg", "-loglevel", "error", "-nostdin", "-y",
                    "-i", url,
                    "-frames:v", "1",
                    frame_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=_SNAPSHOT_TIMEOUT,
            )

        if result.returncode == 0 and os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
            self._frame_count += 1
        else:
            try:
                os.remove(frame_path)
            except OSError:
                pass

    def _assemble_video(self, suffix=""):
        """Assemble captured frames into an MP4 video."""
        if not self._save_persistent:
            log.info("Timelapse: persistent save disabled, skipping assembly")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in (self._current_filename or "print"))
        output_name = f"{safe_name}_{ts}{suffix}.mp4"
        output_path = os.path.join(self._captures_dir, output_name)

        # Calculate fps to make ~30s videos, min 1fps max 30fps
        fps = max(1, min(30, self._frame_count // 30)) if self._frame_count > 30 else 1

        input_pattern = os.path.join(self._current_dir, "frame_%05d.jpg")

        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-loglevel", "error", "-nostdin", "-y",
                    "-framerate", str(fps),
                    "-i", input_pattern,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    output_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
            )
            if result.returncode == 0 and os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                log.info(f"Timelapse: assembled {output_name} ({self._frame_count} frames, {size_mb:.1f}MB)")
            else:
                stderr = result.stderr.decode(errors="ignore").strip()
                log.warning(f"Timelapse: assembly failed: {stderr}")
        except (subprocess.TimeoutExpired, OSError) as err:
            log.warning(f"Timelapse: assembly failed: {err}")

    def _cleanup_temp(self):
        """Remove temporary frame directory."""
        if self._current_dir and os.path.isdir(self._current_dir):
            try:
                shutil.rmtree(self._current_dir)
            except OSError as err:
                log.warning(f"Timelapse: cleanup failed: {err}")
        self._current_dir = None
        self._current_filename = None
        self._frame_count = 0

    def _prune_old_videos(self):
        """Remove oldest videos if over max count."""
        if self._max_videos <= 0:
            return
        try:
            videos = sorted(
                [f for f in os.listdir(self._captures_dir) if f.endswith(".mp4")],
                key=lambda f: os.path.getmtime(os.path.join(self._captures_dir, f)),
            )
            while len(videos) > self._max_videos:
                oldest = videos.pop(0)
                os.remove(os.path.join(self._captures_dir, oldest))
                log.info(f"Timelapse: pruned old video {oldest}")
        except OSError as err:
            log.warning(f"Timelapse: prune failed: {err}")

    def list_videos(self):
        """Return list of available timelapse videos with metadata."""
        videos = []
        try:
            for f in sorted(os.listdir(self._captures_dir), reverse=True):
                if not f.endswith(".mp4"):
                    continue
                path = os.path.join(self._captures_dir, f)
                stat = os.stat(path)
                videos.append({
                    "filename": f,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        except OSError:
            pass
        return videos

    def get_video_path(self, filename):
        """Return full path to a video file, or None if not found."""
        path = os.path.join(self._captures_dir, filename)
        if os.path.isfile(path) and filename.endswith(".mp4"):
            return path
        return None

    def delete_video(self, filename):
        """Delete a timelapse video."""
        path = self.get_video_path(filename)
        if path:
            os.remove(path)
            log.info(f"Timelapse: deleted {filename}")
            return True
        return False
