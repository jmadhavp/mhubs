# -*- coding: utf-8 -*-
"""
service.py - MovieHub Background Auto-Updater Service for Kodi.
Runs automatically on Kodi startup to check GitHub repository for updates and installs them.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "lib"))

try:
    import xbmc
    import xbmcgui
    _KODI = True
except ImportError:
    xbmc = xbmcgui = None
    _KODI = False

from updater import check_and_apply_update


class MovieHubService:
    def __init__(self):
        if _KODI:
            self.monitor = xbmc.Monitor()
        else:
            self.monitor = None

    def run(self):
        if _KODI:
            xbmc.log("[plugin.video.moviehub] Service started. Checking for background updates...", xbmc.LOGINFO)
            # Startup check (delay 5 seconds for smooth Kodi startup)
            if not self.monitor.waitForAbort(5):
                try:
                    check_and_apply_update(silent_if_latest=True)
                except Exception as e:
                    xbmc.log("[plugin.video.moviehub] Auto-updater error: %s" % e, xbmc.LOGERROR)

            # Check every 6 hours (21600 seconds)
            while not self.monitor.abortRequested():
                if self.monitor.waitForAbort(21600):
                    break
                try:
                    check_and_apply_update(silent_if_latest=True)
                except Exception as e:
                    xbmc.log("[plugin.video.moviehub] Auto-updater error: %s" % e, xbmc.LOGERROR)
        else:
            print("MovieHub Service running in standalone mode.")
            check_and_apply_update(silent_if_latest=False)


if __name__ == "__main__":
    service = MovieHubService()
    service.run()
