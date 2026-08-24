# -*- coding: utf-8 -*-
"""
updater.py - Core Auto-Update engine for MovieHub Kodi Addon.
Checks GitHub repository (https://jmadhavp.github.io/mhubs/) on startup and automatically updates the addon.
"""
import os
import re
import sys
import ssl
import time
import zipfile
import shutil
import urllib.request

from common import log, notify, get_setting, _KODI

REPO_ADDONS_XML = "https://jmadhavp.github.io/mhubs/addons.xml"
REPO_ZIP_BASE = "https://jmadhavp.github.io/mhubs/plugin.video.moviehub/"
ADDON_ID = "plugin.video.moviehub"


def parse_version_tuple(ver_str):
    try:
        return tuple(int(x) for x in re.findall(r'\d+', str(ver_str)))
    except Exception:
        return (0, 0, 0)


def get_installed_version():
    if _KODI:
        try:
            import xbmcaddon
            return xbmcaddon.Addon(id=ADDON_ID).getAddonInfo("version")
        except Exception:
            pass
    here = os.path.dirname(os.path.abspath(__file__))
    addon_xml = os.path.abspath(os.path.join(here, "..", "..", "addon.xml"))
    if os.path.exists(addon_xml):
        with open(addon_xml, "r", encoding="utf-8") as f:
            m = re.search(r'<addon\b[^>]*\bversion=["\']([^"\']+)["\']', f.read())
            if m:
                return m.group(1)
    return "0.0.0"


def get_remote_version_info():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {"User-Agent": "Kodi/MovieHub-AutoUpdater"}

    req = urllib.request.Request(REPO_ADDONS_XML, headers=headers)
    res = urllib.request.urlopen(req, context=ctx, timeout=10)
    xml_data = res.read().decode("utf-8", errors="ignore")

    # Find plugin.video.moviehub block in remote addons.xml
    m = re.search(r'<addon\s+id=["\']plugin\.video\.moviehub["\'][^>]*version=["\']([^"\']+)["\']', xml_data)
    if not m:
        m = re.search(r'<addon[^>]*version=["\']([^"\']+)["\'][^>]*id=["\']plugin\.video\.moviehub["\']', xml_data)

    if not m:
        return None, None

    remote_ver = m.group(1)
    zip_url = f"{REPO_ZIP_BASE}{ADDON_ID}-{remote_ver}.zip"
    return remote_ver, zip_url


def get_addon_install_dir():
    if _KODI:
        try:
            import xbmc
            return xbmc.translatePath(f"special://home/addons/{ADDON_ID}/")
        except Exception:
            try:
                import xbmcvfs
                return xbmcvfs.translatePath(f"special://home/addons/{ADDON_ID}/")
            except Exception:
                pass
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


def check_and_apply_update(silent_if_latest=False):
    auto_update_enabled = get_setting("auto_update_enabled", True)
    if auto_update_enabled is False:
        return False

    current_ver = get_installed_version()
    log(f"Auto-updater checking remote version (Current: {current_ver})...")

    try:
        remote_ver, zip_url = get_remote_version_info()
    except Exception as e:
        log(f"Auto-updater check error: {e}", "error")
        if not silent_if_latest:
            notify("Could not connect to update server", "MovieHub")
        return False

    if not remote_ver:
        log("Auto-updater: Remote version info not found.", "debug")
        return False

    if parse_version_tuple(remote_ver) <= parse_version_tuple(current_ver):
        log(f"Auto-updater: Already at latest version v{current_ver}.")
        if not silent_if_latest:
            notify(f"MovieHub is up to date (v{current_ver})", "MovieHub")
        return False

    # Update available!
    notify(f"Update Available: v{remote_ver}! Downloading...", "MovieHub Update", duration=5000)
    log(f"Downloading update v{remote_ver} from {zip_url}...")

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        headers = {"User-Agent": "Kodi/MovieHub-AutoUpdater"}

        req = urllib.request.Request(zip_url, headers=headers)
        res = urllib.request.urlopen(req, context=ctx, timeout=30)
        zip_data = res.read()

        import tempfile
        temp_zip = os.path.join(tempfile.gettempdir(), f"{ADDON_ID}-{remote_ver}.zip")
        with open(temp_zip, "wb") as f:
            f.write(zip_data)

        install_dir = get_addon_install_dir()
        log(f"Extracting update v{remote_ver} to {install_dir}...")

        temp_extract = os.path.join(tempfile.gettempdir(), f"{ADDON_ID}_extract")
        if os.path.exists(temp_extract):
            shutil.rmtree(temp_extract, ignore_errors=True)
        os.makedirs(temp_extract, exist_ok=True)

        with zipfile.ZipFile(temp_zip, "r") as z:
            z.extractall(temp_extract)

        # Locate root of extracted files
        src_root = temp_extract
        if not os.path.exists(os.path.join(temp_extract, "addon.xml")):
            for item in os.listdir(temp_extract):
                sub = os.path.join(temp_extract, item)
                if os.path.isdir(sub) and os.path.exists(os.path.join(sub, "addon.xml")):
                    src_root = sub
                    break

        # Overwrite files into install_dir
        for root, dirs, files in os.walk(src_root):
            rel_path = os.path.relpath(root, src_root)
            dest_folder = os.path.join(install_dir, rel_path) if rel_path != "." else install_dir
            os.makedirs(dest_folder, exist_ok=True)
            for file in files:
                if file.endswith(".pyc") or "__pycache__" in root or file.endswith(".zip"):
                    continue
                shutil.copy2(os.path.join(root, file), os.path.join(dest_folder, file))

        # Cleanup temp
        try:
            os.remove(temp_zip)
            shutil.rmtree(temp_extract, ignore_errors=True)
        except Exception:
            pass

        notify(f"MovieHub updated to v{remote_ver}! Please restart Kodi to apply.", "MovieHub Update", duration=7000)
        log(f"MovieHub successfully updated to v{remote_ver}!")
        return True

    except Exception as e:
        log(f"Auto-update installation failed: {e}", "error")
        notify(f"Update to v{remote_ver} failed: {e}", "MovieHub Error", duration=5000)
        return False
