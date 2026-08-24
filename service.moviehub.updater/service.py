# -*- coding: utf-8 -*-
"""
MovieHub Auto-Updater Service Addon

This service runs in the background when Kodi starts and checks
for updates from the GitHub repository. If an update is available,
it downloads and installs it automatically, then notifies the user.
"""

import os
import sys
import time
import hashlib
import urllib.request
import urllib.error
import zipfile
import shutil
import ssl

# Kodi modules
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

ADDON_ID = "service.moviehub.updater"
ADDON_NAME = "MovieHub Auto-Updater"
ADDON_VERSION = "1.0.0"

# GitHub repository configuration
GITHUB_USER = "jmadhavp"
REPO_NAME = "mhubs"
BASE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/"
ADDONS_XML_URL = BASE_URL + "addons.xml"
ADDONS_MD5_URL = BASE_URL + "addons.xml.md5"

# Target addon to update
TARGET_ADDON_ID = "plugin.video.moviehub"
TARGET_ADDON_ZIP_URL = BASE_URL + "plugin.video.moviehub/"

# Local paths
ADDON_DATA_PATH = xbmcvfs.translatePath("special://profile/addon_data/" + ADDON_ID)
ADDONS_PATH = xbmcvfs.translatePath("special://home/addons/")
TARGET_ADDON_PATH = os.path.join(ADDONS_PATH, TARGET_ADDON_ID)
VERSION_FILE = os.path.join(ADDON_DATA_PATH, "last_checked_version.txt")


def log(msg, level=xbmc.LOGINFO):
    """Log a message to Kodi's log file."""
    xbmc.log(f"[{ADDON_ID}] {msg}", level)


def ensure_data_path():
    """Ensure the addon data directory exists."""
    if not os.path.exists(ADDON_DATA_PATH):
        os.makedirs(ADDON_DATA_PATH)


def get_local_addon_version():
    """Get the currently installed version of the target addon."""
    addon_xml = os.path.join(TARGET_ADDON_PATH, "addon.xml")
    if not os.path.exists(addon_xml):
        return None
    try:
        with open(addon_xml, "r", encoding="utf-8") as f:
            content = f.read()
        import re
        m = re.search(r'<addon\b[^>]*\bversion=["\']([^"\']+)["\']', content)
        return m.group(1) if m else None
    except Exception as e:
        log(f"Error reading local addon version: {e}", xbmc.LOGERROR)
        return None


def fetch_url(url, timeout=15):
    """Fetch content from a URL with SSL context."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Kodi/21.0 (MovieHub Updater)",
        "Accept": "*/*",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        log(f"Error fetching {url}: {e}", xbmc.LOGERROR)
        return None


def get_remote_md5():
    """Fetch the remote addons.xml.md5 hash."""
    return fetch_url(ADDONS_MD5_URL)


def get_remote_addons_xml():
    """Fetch the remote addons.xml."""
    return fetch_url(ADDONS_XML_URL)


def parse_addon_version_from_xml(xml_content, addon_id):
    """Parse the version of a specific addon from addons.xml content."""
    import re
    # Find the addon block
    pattern = r'<addon\b[^>]*\bid=["\']' + re.escape(addon_id) + r'["\'][^>]*>'
    m = re.search(pattern, xml_content)
    if not m:
        return None
    # Extract version from the matched tag
    ver_m = re.search(r'version=["\']([^"\']+)["\']', m.group(0))
    return ver_m.group(1) if ver_m else None


def download_file(url, dest_path, timeout=60):
    """Download a file from URL to a local path."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Kodi/21.0 (MovieHub Updater)",
        "Accept": "*/*",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
        return True
    except Exception as e:
        log(f"Error downloading {url}: {e}", xbmc.LOGERROR)
        return False


def install_addon_zip(zip_path):
    """Install a Kodi addon from a zip file."""
    try:
        # Extract the zip to a temp directory
        temp_dir = os.path.join(ADDON_DATA_PATH, "temp_update")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_dir)

        # Find the addon directory inside the extracted files
        addon_source = temp_dir
        if not os.path.exists(os.path.join(temp_dir, "addon.xml")):
            # Check subdirectories
            for item in os.listdir(temp_dir):
                subdir = os.path.join(temp_dir, item)
                if os.path.isdir(subdir) and os.path.exists(os.path.join(subdir, "addon.xml")):
                    addon_source = subdir
                    break

        # Backup current addon
        backup_dir = os.path.join(ADDON_DATA_PATH, "backup")
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        if os.path.exists(TARGET_ADDON_PATH):
            shutil.copytree(TARGET_ADDON_PATH, backup_dir)

        # Remove current addon and replace with new version
        if os.path.exists(TARGET_ADDON_PATH):
            shutil.rmtree(TARGET_ADDON_PATH)
        shutil.copytree(addon_source, TARGET_ADDON_PATH)

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        if os.path.exists(zip_path):
            os.remove(zip_path)

        return True
    except Exception as e:
        log(f"Error installing addon: {e}", xbmc.LOGERROR)
        return False


def save_last_checked_version(version):
    """Save the last checked version to a file."""
    ensure_data_path()
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(version)
    except Exception as e:
        log(f"Error saving version: {e}", xbmc.LOGERROR)


def get_last_checked_version():
    """Get the last checked version from file."""
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return None


def check_for_updates():
    """Main update check logic. Returns True if update was installed."""
    log("Checking for MovieHub updates...")

    # Get local version
    local_version = get_local_addon_version()
    if not local_version:
        log("Could not determine local addon version.", xbmc.LOGWARNING)
        return False

    log(f"Local version: {local_version}")

    # Get remote MD5
    remote_md5 = get_remote_md5()
    if not remote_md5:
        log("Could not fetch remote MD5.", xbmc.LOGWARNING)
        return False

    remote_md5 = remote_md5.strip()
    last_checked = get_last_checked_version()

    # Check if we already checked this version
    if last_checked == remote_md5:
        log("No new updates (MD5 unchanged).")
        return False

    # Get remote addons.xml to find new version
    remote_xml = get_remote_addons_xml()
    if not remote_xml:
        log("Could not fetch remote addons.xml.", xbmc.LOGWARNING)
        return False

    remote_version = parse_addon_version_from_xml(remote_xml, TARGET_ADDON_ID)
    if not remote_version:
        log("Could not parse remote version.", xbmc.LOGWARNING)
        return False

    log(f"Remote version: {remote_version}")

    # Compare versions
    if remote_version == local_version:
        log("Already up to date.")
        save_last_checked_version(remote_md5)
        return False

    log(f"Update available: {local_version} -> {remote_version}")

    # Download the new version
    zip_url = TARGET_ADDON_ZIP_URL + f"{TARGET_ADDON_ID}-{remote_version}.zip"
    zip_path = os.path.join(ADDON_DATA_PATH, f"{TARGET_ADDON_ID}-{remote_version}.zip")

    log(f"Downloading update from: {zip_url}")
    if not download_file(zip_url, zip_path):
        log("Failed to download update.", xbmc.LOGERROR)
        return False

    # Install the update
    log("Installing update...")
    if not install_addon_zip(zip_path):
        log("Failed to install update.", xbmc.LOGERROR)
        return False

    # Save the new MD5
    save_last_checked_version(remote_md5)

    log(f"Successfully updated to version {remote_version}!")
    return True


class MovieHubUpdateService(xbmc.Monitor):
    """Kodi service that checks for updates on startup."""

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        """Main service loop."""
        log(f"Service started (v{ADDON_VERSION})")

        # Wait a bit for Kodi to fully initialize
        xbmc.sleep(5000)

        try:
            updated = check_for_updates()
            if updated:
                # Show notification
                xbmcgui.Dialog().notification(
                    "MovieHub",
                    "Addon updated successfully! Please restart Kodi.",
                    xbmcgui.NOTIFICATION_INFO,
                    8000,
                )
        except Exception as e:
            log(f"Error during update check: {e}", xbmc.LOGERROR)

        # Keep the service running to handle abort
        while not self.abortRequested():
            if self.waitForAbort(60):
                break

        log("Service stopped.")

    def onNotification(self, sender, method, data):
        """Handle Kodi notifications."""
        pass


if __name__ == "__main__":
    service = MovieHubUpdateService()
    service.run()
