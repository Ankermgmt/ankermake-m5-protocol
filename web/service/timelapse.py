"""Timelapse capture service — periodic snapshots assembled into video."""

import json
import logging
import math
import os
import shutil
import subprocess

log = logging.getLogger("timelapse")

import threading
import time
from datetime import datetime


_DEFAULT_INTERVAL_SEC = 30
_DEFAULT_MAX_VIDEOS = 10
_SNAPSHOT_TIMEOUT = 10
_RESUME_WINDOW_SEC = 60 * 60  # 60 minutes
_IN_PROGRESS_SUBDIR = "in_progress"
_MAX_ORPHAN_AGE_SEC = 24 * 3600  # 24 hours


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
        self._light_mode = None  # None | "session" | "snapshot"

        # Track whether timelapse enabled video/light so we can restore afterwards
        self._video_enabled_by_timelapse = False
        self._enable_generation = None  # VideoQueue generation when WE enabled video
        self._light_was_on = None  # original light state before timelapse touched it

        # Resume-window state: hold completed capture state while waiting to see
        # if the same print resumes (e.g. after a filament change).
        self._resume_dir = None
        self._resume_filename = None
        self._resume_frame_count = 0
        self._finalize_timer = None

        self.reload_config()
        self._scan_in_progress_captures()

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
        self._interval = max(1, int(cfg.get("interval", _DEFAULT_INTERVAL_SEC)))
        self._max_videos = int(cfg.get("max_videos", _DEFAULT_MAX_VIDEOS))
        self._save_persistent = cfg.get("save_persistent", True)
        raw_light = cfg.get("light", None)
        if raw_light == "snapshot":
            self._light_mode = "snapshot"
        elif raw_light in (True, "session", "on"):
            self._light_mode = "session"
        else:
            self._light_mode = None
        log.info(f"Timelapse: config loaded — enabled={self._enabled}, interval={self._interval}s, light_mode={self._light_mode}")

    @property
    def enabled(self):
        return self._enabled

    def _enable_video_for_timelapse(self):
        """Start video streaming for timelapse capture if not already active."""
        from web import app
        from web.lib.service import RunState, ServiceStoppedError

        vq = app.svc.svcs.get("videoqueue")
        if not vq:
            log.warning("Timelapse: videoqueue service not available, snapshots will be skipped")
            return

        was_enabled = vq.video_enabled
        self._video_enabled_by_timelapse = not was_enabled

        if not was_enabled:
            log.info("Timelapse: enabling video streaming for capture")
            vq.set_video_enabled(True)
            self._enable_generation = vq._enable_generation

        # If service is Running but PPPP not connected (was started with video_enabled=False),
        # stop and restart so worker_start() runs with video_enabled=True.
        if vq.state == RunState.Running and getattr(vq, "pppp", None) is None:
            log.info("Timelapse: restarting VideoQueue to establish PPPP connection")
            vq.stop()
            vq.await_stopped()
            vq.start()
        elif vq.state == RunState.Stopped:
            vq.start()

        if vq.wanted and vq.state != RunState.Running:
            try:
                vq.await_ready()
                log.info("Timelapse: video service ready")
            except ServiceStoppedError:
                log.warning("Timelapse: video service failed to start, snapshots may fail")
                self._video_enabled_by_timelapse = False

        if self._light_mode == "session":
            self._light_was_on = getattr(vq, "saved_light_state", None)
            if self._light_was_on is not True:
                log.info("Timelapse: turning on light for capture session")
                vq.api_light_state(True)

    def _disable_video_for_timelapse(self):
        """Disable video streaming if timelapse enabled it."""
        from web import app
        vq = app.svc.svcs.get("videoqueue")

        if self._light_mode == "session" and vq and self._light_was_on is not True:
            restore = self._light_was_on if self._light_was_on is not None else False
            log.info(f"Timelapse: restoring light state to {restore}")
            vq.api_light_state(restore)
        self._light_was_on = None

        if not self._video_enabled_by_timelapse:
            return
        if vq:
            if (self._enable_generation is not None
                    and vq._enable_generation != self._enable_generation):
                log.info("Timelapse: video was re-enabled by user during capture, leaving it on")
            else:
                log.info("Timelapse: disabling video streaming after capture")
                vq.set_video_enabled(False)
        self._video_enabled_by_timelapse = False
        self._enable_generation = None

    def _await_video_frame(self, timeout=2.5, max_age=1.5):
        """Wait until a recent video frame has been received from the camera."""
        from web import app
        vq = app.svc.svcs.get("videoqueue")
        if not vq or not hasattr(vq, "last_frame_at"):
            return True
        now = time.monotonic()
        last_frame = getattr(vq, "last_frame_at", None)
        if last_frame and (now - last_frame) <= max_age:
            return True
        deadline = now + timeout
        while time.monotonic() < deadline:
            last_frame = getattr(vq, "last_frame_at", None)
            if last_frame and (time.monotonic() - last_frame) <= max_age:
                return True
            time.sleep(0.1)
        log.debug("Timelapse: _await_video_frame timed out")
        return False

    def _cancel_finalize_timer(self):
        """Cancel any pending delayed assembly timer."""
        if self._finalize_timer:
            self._finalize_timer.cancel()
            self._finalize_timer = None

    def _cancel_pending_resume(self):
        """Cancel pending resume and delete its temporary frame directory."""
        self._cancel_finalize_timer()
        if self._resume_dir:
            try:
                if os.path.isdir(self._resume_dir):
                    shutil.rmtree(self._resume_dir)
            except OSError as err:
                log.warning(f"Timelapse: cleanup of pending resume dir failed: {err}")
            self._resume_dir = None
            self._resume_filename = None
            self._resume_frame_count = 0

    def _schedule_finalize(self, dir_path, filename, frame_count, suffix=""):
        """Save capture state and schedule delayed assembly.

        If start_capture() is called with the same filename within
        _RESUME_WINDOW_SEC (e.g. after a filament change), the capture
        resumes seamlessly instead of creating a separate video.
        """
        # Discard any previous pending resume for a different file
        if self._resume_dir and self._resume_dir != dir_path:
            try:
                if os.path.isdir(self._resume_dir):
                    shutil.rmtree(self._resume_dir)
            except OSError:
                pass

        self._cancel_finalize_timer()
        self._resume_dir = dir_path
        self._resume_filename = filename
        self._resume_frame_count = frame_count

        def _finalize():
            with self._lock:
                if self._resume_dir != dir_path:
                    return  # Resumed or superseded — don't assemble here
                saved_dir = self._resume_dir
                saved_filename = self._resume_filename
                saved_frame_count = self._resume_frame_count
                self._resume_dir = None
                self._resume_filename = None
                self._resume_frame_count = 0
                self._finalize_timer = None

            # Assemble outside the lock (ffmpeg can take a while)
            # Pass locals directly — avoids writing to self outside the lock
            if saved_frame_count >= 2:
                self._assemble_video_from(saved_dir, saved_filename, saved_frame_count, suffix=suffix)
                self._prune_old_videos()
            else:
                log.info("Timelapse: not enough frames after resume window, skipping assembly")
            self._cleanup_dir(saved_dir)

        timer = threading.Timer(_RESUME_WINDOW_SEC, _finalize)
        timer.daemon = True
        timer.start()
        self._finalize_timer = timer
        log.info(
            f"Timelapse: capture paused for '{filename}' ({frame_count} frames), "
            f"resumable for {_RESUME_WINDOW_SEC // 60} min"
        )

    def start_capture(self, filename="unknown"):
        """Begin periodic snapshot capture for a new print."""
        if not self._enabled:
            return
        if not filename or filename.strip().lower() in {"unknown", "unknown.gcode", ""}:
            log.debug(f"Timelapse: skipping placeholder filename {filename!r}")
            return
        if not shutil.which("ffmpeg"):
            log.warning("Timelapse: ffmpeg not available, skipping")
            return

        with self._lock:
            self._stop_capture_thread()

            # Check if we can seamlessly resume a previous capture of the same print
            can_resume = (
                self._resume_dir is not None
                and self._resume_filename == filename
                and filename
                and filename != "unknown"
            )

            if can_resume:
                log.info(
                    f"Timelapse: resuming capture for '{filename}' "
                    f"({self._resume_frame_count} existing frames)"
                )
                self._cancel_finalize_timer()
                self._current_dir = self._resume_dir
                self._current_filename = self._resume_filename
                self._frame_count = self._resume_frame_count
                self._resume_dir = None
                self._resume_filename = None
                self._resume_frame_count = 0
                self._enable_video_for_timelapse()
            else:
                # New capture or different file — discard any pending resume
                self._cancel_pending_resume()
                self._enable_video_for_timelapse()
                self._current_filename = filename
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in filename)
                self._current_dir = os.path.join(self._in_progress_base(), f"{safe_name}_{ts}")
                os.makedirs(self._current_dir, exist_ok=True)
                self._write_meta(self._current_dir, filename, 0)
                self._frame_count = 0

            self._stop_event.clear()

            self._capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True,
                name="timelapse-capture",
            )
            self._capture_thread.start()
            log.info(f"Timelapse: started capture for '{filename}' (interval={self._interval}s)")

    def finish_capture(self, final=False):
        """Stop capture and assemble video.

        Args:
            final: If True, the print is definitively complete — cancel any
                   pending resume window and assemble the video immediately
                   in a background thread.  If False (default), enter the
                   resume window so that a filament-change pause can be
                   continued seamlessly.
        """
        if not self._enabled:
            return
        assemble_dir = None
        assemble_filename = None
        assemble_frame_count = 0
        with self._lock:
            self._stop_capture_thread()
            if not self._current_dir:
                if not self._resume_dir:
                    self._disable_video_for_timelapse()
                return
            if final:
                self._cancel_pending_resume()
                assemble_dir = self._current_dir
                assemble_filename = self._current_filename
                assemble_frame_count = self._frame_count
                self._current_dir = None
                self._current_filename = None
                self._frame_count = 0
            else:
                self._schedule_finalize(
                    self._current_dir, self._current_filename, self._frame_count
                )
                self._current_dir = None
                self._current_filename = None
                self._frame_count = 0
            self._disable_video_for_timelapse()
        if final and assemble_dir:
            if assemble_frame_count >= 2:
                t = threading.Thread(
                    target=self._finalize_now,
                    args=(assemble_dir, assemble_filename, assemble_frame_count),
                    daemon=True,
                    name="timelapse-assemble",
                )
                t.start()
            else:
                log.info("Timelapse: not enough frames, skipping assembly")
                self._cleanup_dir(assemble_dir)

    def _finalize_now(self, dir_path, filename, frame_count):
        """Assemble video immediately (runs in dedicated background thread)."""
        try:
            self._assemble_video_from(dir_path, filename, frame_count)
            self._prune_old_videos()
        finally:
            self._cleanup_dir(dir_path)

    def fail_capture(self):
        """Stop capture on failure — assemble partial timelapse if frames exist."""
        if not self._enabled:
            return
        assemble_dir = None
        assemble_filename = None
        assemble_frame_count = 0
        with self._lock:
            self._stop_capture_thread()
            self._cancel_pending_resume()
            if self._current_dir and self._frame_count >= 2:
                log.info("Timelapse: print failed, assembling partial timelapse")
                assemble_dir = self._current_dir
                assemble_filename = self._current_filename
                assemble_frame_count = self._frame_count
                self._current_dir = None
                self._current_filename = None
                self._frame_count = 0
            else:
                self._cleanup_temp()
            self._disable_video_for_timelapse()
        # Assemble outside the lock — ffmpeg can take up to 120 s
        if assemble_dir:
            try:
                self._assemble_video_from(assemble_dir, assemble_filename, assemble_frame_count, suffix="_partial")
                self._prune_old_videos()
            finally:
                self._cleanup_dir(assemble_dir)

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

        # Per-snapshot light control: turn on, wait for camera to adjust, then shoot
        vq = app.svc.svcs.get("videoqueue") if self._light_mode == "snapshot" else None
        snap_original_light = None
        if vq:
            snap_original_light = getattr(vq, "saved_light_state", None)
            if snap_original_light is not True:
                log.info("Timelapse: light on for snapshot, waiting 1.5s")
                vq.api_light_state(True)
                time.sleep(1.5)

        self._await_video_frame()

        frame_path = os.path.join(self._current_dir, f"frame_{self._frame_count:05d}.jpg")
        try:
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
                self._write_meta(self._current_dir, self._current_filename, self._frame_count)
            else:
                try:
                    os.remove(frame_path)
                except OSError:
                    pass
        finally:
            # Always restore light even if ffmpeg timed out or raised an exception
            if vq and snap_original_light is not True:
                time.sleep(1.0)
                restore = snap_original_light if snap_original_light is not None else False
                log.info(f"Timelapse: restoring light to {restore} after snapshot")
                vq.api_light_state(restore)

    def _in_progress_base(self):
        """Return (and create) the persistent in-progress frames directory."""
        path = os.path.join(self._captures_dir, _IN_PROGRESS_SUBDIR)
        os.makedirs(path, exist_ok=True)
        return path

    def _write_meta(self, dir_path, filename, frame_count):
        """Write a small JSON sidecar so state survives container restarts."""
        try:
            with open(os.path.join(dir_path, ".meta"), "w") as f:
                json.dump({"filename": filename, "frame_count": frame_count}, f)
        except OSError as err:
            log.warning(f"Timelapse: could not write .meta: {err}")

    def _read_meta(self, dir_path):
        """Read the JSON sidecar, or return None if missing/corrupt."""
        try:
            with open(os.path.join(dir_path, ".meta")) as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def _scan_in_progress_captures(self):
        """On startup, detect persisted in-progress frame directories.

        - Loads the most recent dir (≤24h old) as resume state.
        - Assembles and removes any older/excess orphaned dirs.
        """
        base = os.path.join(self._captures_dir, _IN_PROGRESS_SUBDIR)
        if not os.path.isdir(base):
            return
        now = time.time()
        candidates = []
        for name in sorted(os.listdir(base)):
            dir_path = os.path.join(base, name)
            if not os.path.isdir(dir_path):
                continue
            frames = [f for f in os.listdir(dir_path) if f.startswith("frame_") and f.endswith(".jpg")]
            frame_count = len(frames)
            if frame_count == 0:
                shutil.rmtree(dir_path, ignore_errors=True)
                continue
            meta = self._read_meta(dir_path)
            filename = (meta or {}).get("filename", "unknown")
            age = now - os.path.getmtime(dir_path)
            candidates.append((age, dir_path, filename, frame_count))

        if not candidates:
            return

        # Sort by age ascending (youngest first)
        candidates.sort()
        youngest_age, youngest_dir, youngest_filename, youngest_frames = candidates[0]

        # Assemble/delete all but the youngest (shouldn't normally happen)
        for age, dir_path, filename, frame_count in candidates[1:]:
            if frame_count >= 2:
                log.info(f"Timelapse: recovering orphaned capture '{filename}' ({frame_count} frames)")
                self._assemble_video_from(dir_path, filename, frame_count, suffix="_recovered")
                self._prune_old_videos()
            shutil.rmtree(dir_path, ignore_errors=True)

        # Handle the youngest candidate
        if youngest_age <= _MAX_ORPHAN_AGE_SEC:
            log.info(
                f"Timelapse: found persisted capture '{youngest_filename}' "
                f"({youngest_frames} frames, {youngest_age / 3600:.1f}h ago) — "
                f"resumable for {_RESUME_WINDOW_SEC // 60} min"
            )
            self._resume_dir = youngest_dir
            self._resume_filename = youngest_filename
            self._resume_frame_count = youngest_frames
            # Schedule finalize so orphaned frames are eventually assembled
            self._schedule_finalize(youngest_dir, youngest_filename, youngest_frames)
        else:
            if youngest_frames >= 2:
                log.info(f"Timelapse: assembling stale capture '{youngest_filename}' ({youngest_frames} frames, {youngest_age / 3600:.1f}h old)")
                self._assemble_video_from(youngest_dir, youngest_filename, youngest_frames, suffix="_recovered")
                self._prune_old_videos()
            shutil.rmtree(youngest_dir, ignore_errors=True)

    def _assemble_video(self, suffix=""):
        """Assemble current capture into an MP4 video."""
        self._assemble_video_from(self._current_dir, self._current_filename, self._frame_count, suffix=suffix)

    def _assemble_video_from(self, dir_path, filename, frame_count, suffix=""):
        """Assemble frames from dir_path into an MP4 video (no self state read)."""
        if not self._save_persistent:
            log.info("Timelapse: persistent save disabled, skipping assembly")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in (filename or "print"))
        output_name = f"{safe_name}_{ts}{suffix}.mp4"
        output_path = os.path.join(self._captures_dir, output_name)

        # Calculate fps to make ~30s videos, min 1fps max 30fps
        fps = max(1, min(30, math.ceil(frame_count / 30)))

        input_pattern = os.path.join(dir_path, "frame_%05d.jpg")

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
                log.info(f"Timelapse: assembled {output_name} ({frame_count} frames, {size_mb:.1f}MB)")
            else:
                stderr = result.stderr.decode(errors="ignore").strip()
                log.warning(f"Timelapse: assembly failed: {stderr}")
        except (subprocess.TimeoutExpired, OSError) as err:
            log.warning(f"Timelapse: assembly failed: {err}")

    def _cleanup_temp(self):
        """Remove current capture's temporary frame directory."""
        self._cleanup_dir(self._current_dir)
        self._current_dir = None
        self._current_filename = None
        self._frame_count = 0

    def _cleanup_dir(self, dir_path):
        """Remove a temporary frame directory."""
        if dir_path and os.path.isdir(dir_path):
            try:
                shutil.rmtree(dir_path)
            except OSError as err:
                log.warning(f"Timelapse: cleanup failed: {err}")

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
