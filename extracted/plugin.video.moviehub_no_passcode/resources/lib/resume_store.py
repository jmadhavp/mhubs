import os
import json
import time

ADDON_ID = "plugin.video.moviehub"

try:
    import xbmc
    _KODI = True
except ImportError:
    xbmc = None
    _KODI = False


def _profile_dir():
    if _KODI:
        try:
            from xbmc import translatePath
            return translatePath("special://profile/addon_data/%s/" % ADDON_ID)
        except Exception:
            return os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.abspath(__file__))


def _path():
    base = _profile_dir()
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        pass
    return os.path.join(base, "resume.json")


def load():
    try:
        p = _path()
        if not os.path.exists(p):
            return {}
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def save(data):
    try:
        p = _path()
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        if os.path.exists(p):
            os.remove(p)
        os.rename(tmp, p)
        return True
    except Exception:
        return False


def register_playable(playable_url, meta):
    if not playable_url:
        return
    data = load()
    item = data.get(playable_url) or {}
    item.update(meta or {})
    item["playable_url"] = playable_url
    item.setdefault("position", 0.0)
    item.setdefault("total", 0.0)
    item["updated"] = time.time()
    data[playable_url] = item
    save(data)


def update_position(playable_url, position, total=None):
    if not playable_url:
        return
    try:
        position = float(position or 0.0)
    except Exception:
        position = 0.0
    if position < 0:
        position = 0.0
    data = load()
    item = data.get(playable_url) or {"playable_url": playable_url}
    item["position"] = position
    if total is not None:
        try:
            item["total"] = float(total or 0.0)
        except Exception:
            pass
    item["updated"] = time.time()
    data[playable_url] = item
    save(data)


def clear_item(playable_url):
    if not playable_url:
        return
    data = load()
    if playable_url in data:
        del data[playable_url]
        save(data)


def get_resume_items(limit=50, min_seconds=60):
    data = load()
    items = []
    for u, v in data.items():
        try:
            pos = float(v.get("position") or 0.0)
        except Exception:
            pos = 0.0
        if pos < float(min_seconds):
            continue
        if not v.get("embed"):
            continue
        items.append(v)
    items.sort(key=lambda x: x.get("updated", 0), reverse=True)
    return items[:limit]
