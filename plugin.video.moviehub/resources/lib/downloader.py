# -*- coding: utf-8 -*-
"""
downloader.py - Background download manager for MovieHub addon.

Provides:
- Download files in the background while user browses
- Pause / Resume / Cancel downloads
- Progress tracking with speed and ETA
- Multiple concurrent downloads (configurable)
- Download history tracking
- HLS (m3u8) to MP4 conversion support
"""
import os
import re
import time
import json
import threading
import urllib.request
import urllib.parse
from collections import OrderedDict

from common import log, notify, get_setting, set_setting, human_size, Net, _KODI, xbmc, xbmcgui

ADDON_ID = "plugin.video.moviehub"

# Global download manager instance
_download_manager = None


def _parse_m3u8(m3u8_content, base_url):
    """Parse m3u8 playlist and return list of segment URLs."""
    from urllib.parse import urljoin
    segments = []
    lines = m3u8_content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # This is a segment URL
            seg_url = urljoin(base_url, line)
            segments.append(seg_url)
    return segments


def _download_hls_to_mp4(job, net, headers):
    """Download HLS stream and convert to MP4 by concatenating segments."""
    try:
        # Fetch the master playlist
        req = urllib.request.Request(job.url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=60)
        master_content = resp.read().decode('utf-8', 'ignore')
        final_url = resp.geturl()
        
        # Check if it's a master playlist with multiple qualities
        if '#EXT-X-STREAM-INF' in master_content:
            # Parse quality variants and pick the best (or preferred)
            preferred = get_setting("prefer_quality", "Auto")
            variants = []
            lines = master_content.strip().split('\n')
            for i, line in enumerate(lines):
                if line.startswith('#EXT-X-STREAM-INF'):
                    # Next line should be the variant URL
                    if i + 1 < len(lines):
                        variant_url = lines[i + 1].strip()
                        if variant_url and not variant_url.startswith('#'):
                            variant_url = urllib.parse.urljoin(final_url, variant_url)
                            # Extract resolution from EXT-X-STREAM-INF
                            res_match = re.search(r'RESOLUTION=(\d+)x(\d+)', line)
                            resolution = int(res_match.group(2)) if res_match else 0
                            variants.append((resolution, variant_url))
            
            if variants:
                # Sort by resolution descending
                variants.sort(key=lambda x: x[0], reverse=True)
                # Pick based on preference
                if preferred and preferred != "Auto":
                    wanted = int(re.sub(r'[^0-9]', '', preferred))
                    for res, vurl in variants:
                        if res <= wanted:
                            final_url = vurl
                            break
                    else:
                        final_url = variants[0][1]  # fallback to highest
                else:
                    final_url = variants[0][1]  # highest quality
                
                # Fetch the variant playlist
                req = urllib.request.Request(final_url, headers=headers)
                resp = urllib.request.urlopen(req, timeout=60)
                master_content = resp.read().decode('utf-8', 'ignore')
                final_url = resp.geturl()
        
        # Parse segments from the media playlist
        segments = _parse_m3u8(master_content, final_url)
        if not segments:
            raise Exception("No segments found in HLS playlist")
        
        job.total_bytes = len(segments) * 1024 * 1024  # rough estimate
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(job.dest_path), exist_ok=True)
        temp_path = job.dest_path + ".tmp"
        
        # Check for resume
        resume_pos = 0
        start_segment = 0
        if os.path.exists(temp_path):
            resume_pos = os.path.getsize(temp_path)
            # Estimate which segment we're at (rough)
            start_segment = max(0, resume_pos // (1024 * 1024))
            log("Resuming HLS download from segment ~%d" % start_segment, "debug")
        
        mode = "ab" if resume_pos > 0 else "wb"
        with open(temp_path, mode, 8192) as f:
            if resume_pos > 0:
                job.downloaded_bytes = resume_pos
            
            start_time = time.time()
            
            for i, seg_url in enumerate(segments[start_segment:], start=start_segment):
                if job._stop_event.is_set():
                    job.status = DownloadJob.STATUS_CANCELLED
                    return False
                
                if job._pause_event.is_set():
                    time.sleep(0.5)
                    continue
                
                try:
                    seg_req = urllib.request.Request(seg_url, headers=headers)
                    seg_resp = urllib.request.urlopen(seg_req, timeout=30)
                    seg_data = seg_resp.read()
                    f.write(seg_data)
                    job.downloaded_bytes += len(seg_data)
                    
                    # Update progress
                    if job.total_bytes > 0:
                        job.progress = min(99.9, (job.downloaded_bytes / job.total_bytes) * 100)
                    
                    # Calculate speed and ETA
                    elapsed = time.time() - start_time
                    if elapsed > 1.0:
                        job.speed = job.downloaded_bytes / elapsed
                        if job.speed > 0 and job.total_bytes > 0:
                            remaining = job.total_bytes - job.downloaded_bytes
                            job.eta = int(remaining / job.speed)
                    
                except Exception as e:
                    log("Failed to download segment %d: %s" % (i, e), "error")
                    # Continue with next segment
                    continue
        
        # Rename temp to final
        if os.path.exists(job.dest_path):
            os.remove(job.dest_path)
        os.rename(temp_path, job.dest_path)
        return True
        
    except Exception as e:
        log("HLS download failed: %s" % e, "error")
        raise


def _format_clock(seconds):
    try:
        seconds = int(float(seconds or 0))
    except Exception:
        seconds = 0
    if seconds < 0:
        seconds = 0
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return "%d:%02d:%02d" % (h, m, s)
    return "%02d:%02d" % (m, s)


def get_manager():
    global _download_manager
    if _download_manager is None:
        _download_manager = DownloadManager()
    return _download_manager


class DownloadJob:
    """Represents a single download task."""
    
    STATUS_PENDING = "pending"
    STATUS_DOWNLOADING = "downloading"
    STATUS_PAUSED = "paused"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    
    def __init__(self, url, title, dest_path, referer="", quality="", kind="mp4"):
        self.id = str(int(time.time() * 1000)) + "_" + re.sub(r'[^a-zA-Z0-9]', '_', title)[:30]
        self.url = url
        self.title = title
        self.dest_path = dest_path
        self.referer = referer
        self.quality = quality
        self.kind = kind  # m3u8 or mp4
        self.status = self.STATUS_PENDING
        self.progress = 0.0  # 0-100
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.speed = 0  # bytes per second
        self.eta = 0  # seconds remaining
        self.error = ""
        self.created = time.time()
        self.completed = 0
        self._thread = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "dest_path": self.dest_path,
            "referer": self.referer,
            "quality": self.quality,
            "kind": self.kind,
            "status": self.status,
            "progress": self.progress,
            "downloaded_bytes": self.downloaded_bytes,
            "total_bytes": self.total_bytes,
            "speed": self.speed,
            "eta": self.eta,
            "error": self.error,
            "created": self.created,
            "completed": self.completed,
        }


class DownloadManager:
    """Manages all download jobs with background threading."""
    
    def __init__(self):
        self.jobs = OrderedDict()
        self._lock = threading.Lock()
        self._load_history()
        
    # ---- History persistence ----
    def _history_path(self):
        if _KODI:
            try:
                from xbmc import translatePath
                profile = translatePath("special://profile/addon_data/%s/" % ADDON_ID)
            except Exception:
                profile = os.path.dirname(os.path.abspath(__file__))
        else:
            profile = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(profile, "download_history.json")
    
    def _save_history(self):
        try:
            path = self._history_path()
            data = []
            for j in self.jobs.values():
                if j.status in (DownloadJob.STATUS_COMPLETED, DownloadJob.STATUS_FAILED, DownloadJob.STATUS_CANCELLED):
                    data.append(j.to_dict())
            # Also include active/paused jobs
            for j in self.jobs.values():
                if j.status not in (DownloadJob.STATUS_COMPLETED, DownloadJob.STATUS_FAILED, DownloadJob.STATUS_CANCELLED):
                    data.append(j.to_dict())
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log("save download history error: %s" % e, "debug")
    
    def _load_history(self):
        try:
            path = self._history_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    j = DownloadJob(
                        item["url"], item["title"], item["dest_path"],
                        item.get("referer", ""), item.get("quality", ""), item.get("kind", "mp4")
                    )
                    j.id = item["id"]
                    j.status = item["status"]
                    j.progress = item["progress"]
                    j.downloaded_bytes = item["downloaded_bytes"]
                    j.total_bytes = item["total_bytes"]
                    j.error = item.get("error", "")
                    j.created = item.get("created", time.time())
                    j.completed = item.get("completed", 0)
                    self.jobs[j.id] = j
                log("Loaded %d download history items" % len(data), "debug")
        except Exception as e:
            log("load download history error: %s" % e, "debug")
    
    # ---- Job management ----
    def add_job(self, url, title, dest_path, referer="", quality="", kind="mp4"):
        """Add a new download job and start it."""
        with self._lock:
            j = DownloadJob(url, title, dest_path, referer, quality, kind)
            self.jobs[j.id] = j
            self._start_job(j)
            self._save_history()
        return j
    
    def _start_job(self, job):
        """Start a download thread for the job."""
        if _KODI:
            job._thread = threading.Thread(target=self._download_worker, args=(job,), daemon=True)
            job._thread.start()
        else:
            # Non-Kodi: run synchronously for testing
            self._download_worker(job)
    
    def _download_worker(self, job):
        """Worker that performs the actual download."""
        job.status = DownloadJob.STATUS_DOWNLOADING
        job._pause_event.clear()
        job._stop_event.clear()

        bg = None
        last_percent = -1
        last_ui = 0
        if _KODI:
            try:
                bg = xbmcgui.DialogProgressBG()
                bg.create("MovieHub", job.title)
            except Exception:
                bg = None
        
        net = Net(timeout=60)
        headers = {
            "User-Agent": get_setting("user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"),
            "Accept": "*/*",
        }
        if job.referer:
            headers["Referer"] = job.referer
        
        temp_path = job.dest_path + ".tmp"
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(job.dest_path), exist_ok=True)
            
            # Check if this is an HLS stream
            is_hls = (job.kind == "m3u8" or
                      (job.url or "").lower().split("?")[0].endswith(".m3u8"))
            
            if is_hls:
                # Download HLS and convert to MP4
                log("Starting HLS download for %s" % job.title, "debug")
                try:
                    success = _download_hls_to_mp4(job, net, headers)
                    if not success:
                        job.status = DownloadJob.STATUS_CANCELLED
                        return
                    
                    job.status = DownloadJob.STATUS_COMPLETED
                    job.progress = 100.0
                    job.completed = time.time()
                    job.speed = 0
                    job.eta = 0
                    
                    if bg:
                        try:
                            bg.update(100, "MovieHub", "Completed")
                            time.sleep(0.7)
                        except Exception:
                            pass
                    notify("Download completed: %s" % job.title, "MovieHub", duration=3000)
                except Exception as e:
                    job.status = DownloadJob.STATUS_FAILED
                    job.error = str(e)
                    log("HLS download failed for %s: %s" % (job.title, e), "error")
                    notify("Download failed: %s" % job.title, "MovieHub", duration=3000)
            else:
                # Regular MP4 download
                # Check if partial download exists
                resume_pos = 0
                if os.path.exists(temp_path):
                    resume_pos = os.path.getsize(temp_path)
                    if resume_pos > 0:
                        headers["Range"] = "bytes=%d-" % resume_pos
                        log("Resuming download from byte %d" % resume_pos, "debug")
                
                # Make the request
                try:
                    req = urllib.request.Request(job.url, headers=headers)
                    resp = urllib.request.urlopen(req, timeout=60)
                    
                    total = int(resp.headers.get("Content-Length", 0)) + resume_pos
                    job.total_bytes = total
                    
                    mode = "ab" if resume_pos > 0 else "wb"
                    with open(temp_path, mode, 8192) as f:
                        if resume_pos > 0:
                            job.downloaded_bytes = resume_pos
                        
                        start_time = time.time()
                        chunk_size = 65536  # 64KB chunks
                        
                        while True:
                            if job._stop_event.is_set():
                                job.status = DownloadJob.STATUS_CANCELLED
                                self._save_history()
                                return
                            
                            if job._pause_event.is_set():
                                time.sleep(0.5)
                                continue
                            
                            chunk = resp.read(chunk_size)
                            if not chunk:
                                break
                            
                            f.write(chunk)
                            job.downloaded_bytes += len(chunk)
                            
                            if total > 0:
                                job.progress = min(99.9, (job.downloaded_bytes / total) * 100)
                            
                            # Calculate speed and ETA
                            elapsed = time.time() - start_time
                            if elapsed > 1.0:
                                job.speed = job.downloaded_bytes / elapsed
                                if job.speed > 0 and total > 0:
                                    remaining = total - job.downloaded_bytes
                                    job.eta = int(remaining / job.speed)

                            if bg:
                                now = time.time()
                                pct = int(job.progress or 0)
                                if pct != last_percent and (now - last_ui) >= 0.5:
                                    last_percent = pct
                                    last_ui = now
                                    try:
                                        speed = human_size(job.speed) + "/s" if job.speed else ""
                                        eta = _format_clock(job.eta) if job.eta else ""
                                        extra = ""
                                        if speed:
                                            extra += "  " + speed
                                        if eta:
                                            extra += "  ETA " + eta
                                        msg = "%s / %s%s" % (human_size(job.downloaded_bytes), human_size(total or 0), extra)
                                        bg.update(pct, "MovieHub", msg)
                                    except Exception:
                                        pass
                    
                    # Rename temp to final
                    if os.path.exists(job.dest_path):
                        os.remove(job.dest_path)
                    os.rename(temp_path, job.dest_path)
                    
                    job.status = DownloadJob.STATUS_COMPLETED
                    job.progress = 100.0
                    job.completed = time.time()
                    job.speed = 0
                    job.eta = 0
                    
                    if bg:
                        try:
                            bg.update(100, "MovieHub", "Completed")
                            time.sleep(0.7)
                        except Exception:
                            pass
                    notify("Download completed: %s" % job.title, "MovieHub", duration=3000)
                    
                except Exception as e:
                    job.status = DownloadJob.STATUS_FAILED
                    job.error = str(e)
                    log("Download failed for %s: %s" % (job.title, e), "error")
                    notify("Download failed: %s" % job.title, "MovieHub", duration=3000)
        
        except Exception as e:
            job.status = DownloadJob.STATUS_FAILED
            job.error = str(e)
            log("Download setup failed for %s: %s" % (job.title, e), "error")
        
        finally:
            if bg:
                try:
                    bg.close()
                except Exception:
                    pass
            self._save_history()
    
    def pause_job(self, job_id):
        """Pause a download."""
        with self._lock:
            j = self.jobs.get(job_id)
            if j and j.status == DownloadJob.STATUS_DOWNLOADING:
                j._pause_event.set()
                j.status = DownloadJob.STATUS_PAUSED
                self._save_history()
                return True
        return False
    
    def resume_job(self, job_id):
        """Resume a paused download."""
        with self._lock:
            j = self.jobs.get(job_id)
            if j and j.status == DownloadJob.STATUS_PAUSED:
                j._pause_event.clear()
                j.status = DownloadJob.STATUS_DOWNLOADING
                self._save_history()
                return True
        return False
    
    def cancel_job(self, job_id):
        """Cancel a download."""
        with self._lock:
            j = self.jobs.get(job_id)
            if j:
                j._stop_event.set()
                j.status = DownloadJob.STATUS_CANCELLED
                # Clean up temp file
                temp_path = j.dest_path + ".tmp"
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                self._save_history()
                return True
        return False
    
    def remove_job(self, job_id):
        """Remove a completed/failed job from history."""
        with self._lock:
            j = self.jobs.pop(job_id, None)
            if j:
                self._save_history()
                return True
        return False
    
    def get_job(self, job_id):
        return self.jobs.get(job_id)
    
    def get_active_jobs(self):
        return [j for j in self.jobs.values() 
                if j.status in (DownloadJob.STATUS_DOWNLOADING, DownloadJob.STATUS_PAUSED, DownloadJob.STATUS_PENDING)]
    
    def get_completed_jobs(self):
        return [j for j in self.jobs.values() 
                if j.status == DownloadJob.STATUS_COMPLETED]
    
    def get_all_jobs(self):
        return list(self.jobs.values())
    
    def get_download_speed(self, job_id):
        """Get formatted download speed string."""
        j = self.jobs.get(job_id)
        if j and j.speed > 0:
            return human_size(j.speed) + "/s"
        return ""
    
    def get_download_eta(self, job_id):
        """Get formatted ETA string."""
        j = self.jobs.get(job_id)
        if j and j.eta > 0:
            m, s = divmod(j.eta, 60)
            h, m = divmod(m, 60)
            if h > 0:
                return "%dh %02dm %02ds" % (h, m, s)
            return "%02d:%02d" % (m, s)
        return ""

    def show_downloads_dialog(self):
        """Show a Kodi dialog listing all downloads with management options."""
        if not _KODI:
            return
        
        while True:
            active = self.get_active_jobs()
            completed = self.get_completed_jobs()
            
            items = []
            actions = []  # (action_type, job_id)
            
            # Active downloads section
            if active:
                items.append("[COLOR gold]═══ ACTIVE DOWNLOADS ═══[/COLOR]")
                actions.append(("header", None))
                
                for j in active:
                    status_icon = "⏸" if j.status == DownloadJob.STATUS_PAUSED else "⬇"
                    prog_bar = self._progress_bar(j.progress)
                    speed_str = self.get_download_speed(j.id)
                    eta_str = self.get_download_eta(j.id)
                    
                    label = "%s %s\n  %s %d%%  %s  ETA: %s" % (
                        status_icon, j.title, prog_bar, int(j.progress), speed_str, eta_str
                    )
                    items.append(label)
                    actions.append(("active", j.id))
                
                items.append("")  # separator
                actions.append(("header", None))
            
            # Completed downloads section
            if completed:
                items.append("[COLOR green]═══ COMPLETED ═══[/COLOR]")
                actions.append(("header", None))
                
                for j in completed[-10:]:  # Show last 10
                    size = human_size(j.total_bytes) if j.total_bytes > 0 else "?"
                    items.append("✅ %s (%s)" % (j.title, size))
                    actions.append(("completed", j.id))
            
            if not items:
                items.append("[COLOR gray]No downloads yet[/COLOR]")
                actions.append(("header", None))
            
            items.append("")
            items.append("[B]Close[/B]")
            actions.append(("close", None))
            
            selected = xbmcgui.Dialog().select("MovieHub - Downloads", items)
            if selected < 0 or selected >= len(actions):
                break
            
            action, job_id = actions[selected]
            if action == "header":
                continue
            elif action == "close":
                break
            elif action == "active":
                self._show_job_menu(job_id)
            elif action == "completed":
                self._show_completed_menu(job_id)
    
    def _progress_bar(self, percent, width=20):
        """Create a text progress bar."""
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return bar
    
    def _show_job_menu(self, job_id):
        """Show context menu for an active/paused download."""
        if not _KODI:
            return
        j = self.jobs.get(job_id)
        if not j:
            return
        
        options = []
        actions = []
        
        if j.status == DownloadJob.STATUS_DOWNLOADING:
            options.append("⏸ Pause")
            actions.append("pause")
        elif j.status == DownloadJob.STATUS_PAUSED:
            options.append("▶ Resume")
            actions.append("resume")
        
        options.append("⏹ Cancel")
        actions.append("cancel")
        options.append("✖ Remove from list")
        actions.append("remove")
        
        selected = xbmcgui.Dialog().select("Manage: %s" % j.title, options)
        if selected < 0:
            return
        
        action = actions[selected]
        if action == "pause":
            self.pause_job(job_id)
        elif action == "resume":
            self.resume_job(job_id)
        elif action == "cancel":
            if xbmcgui.Dialog().yesno("Cancel Download", "Cancel '%s'?" % j.title):
                self.cancel_job(job_id)
        elif action == "remove":
            self.remove_job(job_id)
    
    def _show_completed_menu(self, job_id):
        """Show context menu for a completed download."""
        if not _KODI:
            return
        j = self.jobs.get(job_id)
        if not j:
            return
        
        options = ["✖ Remove from list"]
        actions = ["remove"]
        
        # Add play option if file exists
        if os.path.exists(j.dest_path):
            options.insert(0, "▶ Play")
            actions.insert(0, "play")
        
        selected = xbmcgui.Dialog().select("Completed: %s" % j.title, options)
        if selected < 0:
            return
        
        action = actions[selected]
        if action == "play":
            self._play_downloaded_file(j)
        elif action == "remove":
            self.remove_job(job_id)
    
    def _play_downloaded_file(self, job):
        """Play a downloaded video file using Kodi's player."""
        if not _KODI:
            return
        if not os.path.exists(job.dest_path):
            notify("File not found: %s" % job.title, "MovieHub")
            return
        
        li = xbmcgui.ListItem(job.title, path=job.dest_path)
        li.setInfo("video", {"title": job.title})
        xbmcplugin.setResolvedUrl(0, True, li)
    
    @staticmethod
    def get_download_path():
        """Get the download directory path."""
        path = get_setting("download_path", "")
        if not path:
            # Default: userdata/addon_data/plugin.video.moviehub/downloads/
            if _KODI:
                try:
                    from xbmc import translatePath
                    profile = translatePath("special://profile/addon_data/%s/" % ADDON_ID)
                    path = os.path.join(profile, "downloads")
                except Exception:
                    path = os.path.join(os.path.expanduser("~"), "Downloads", "MovieHub")
            else:
                path = os.path.join(os.path.expanduser("~"), "Downloads", "MovieHub")
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            pass
        return path


# ---------------------------------------------------------------------------
# Kodi Service Monitor for background downloads
# ---------------------------------------------------------------------------
class DownloadMonitor:
    """Monitors Kodi's shutdown to properly cancel active downloads."""
    
    def __init__(self):
        if _KODI:
            try:
                self._monitor = xbmc.Monitor()
            except Exception:
                self._monitor = None
    
    def wait_for_abort(self):
        """Wait for Kodi to abort (shutdown). Cancel active downloads."""
        if not _KODI or not self._monitor:
            return
        
        while not self._monitor.abortRequested():
            if self._monitor.waitForAbort(1):
                break
        
        # Cancel all active downloads on shutdown
        mgr = get_manager()
        for j in mgr.get_active_jobs():
            if j.status == DownloadJob.STATUS_DOWNLOADING:
                j._stop_event.set()
                j.status = DownloadJob.STATUS_CANCELLED
        mgr._save_history()

