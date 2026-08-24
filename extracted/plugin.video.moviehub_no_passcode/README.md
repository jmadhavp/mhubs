# MovieHub — Free Movies for Kodi

MovieHub is a Kodi video addon that lets you browse and stream a curated
catalogue of movies and web series. Access is protected by a **4-digit
subscription passcode** that is **locked to a single device** — one code works
on only one Kodi installation.

## Install

**Via repository (recommended, auto-updates):**
Kodi's "Add source" needs a browsable web address, so use **GitHub Pages**.

1. On GitHub, repo `teenpatti007/1` → **Settings → Pages** → Deploy from a
   branch → **main** → **/docs** → Save.
2. Kodi → **Settings (gear) → File manager → Add source → `<None>`**.
3. Enter:
   ```
   https://teenpatti007.github.io/1/
   ```
4. Name it `MovieHub Repo`, then **OK**.
5. **Settings → Add-ons → Install from zip file → MovieHub Repo** → install
   `repository.moviehub.zip`.
6. **Settings → Add-ons → Install from repository → MovieHub Repository →
   Video add-ons → MovieHub → Install**.

**Via ZIP (no auto-update):**
1. Download `plugin.video.moviehub.zip` onto the Kodi device.
2. **Settings → Add-ons → Install from zip file** → select the zip.
3. MovieHub appears under **Video → MovieHub**.

## First launch

Open **MovieHub** and enter the **4-digit access code** you were given. The code
is linked to this device and is re-checked on every launch. A code already used
on another device is rejected — contact your provider for a fresh code.

## Using MovieHub

- **Latest** — newest movies, with a **`>> Next Page`** item at the bottom.
- **Genres / Categories** — browse by category (also supports Next Page).
- **Search** — find a movie by name.
- **Play** — pick a title, choose a source, and it resolves and plays. HLS
  (`.m3u8`) uses `inputstream.adaptive`; direct MP4s play natively.

## Settings

Open **MovieHub → (long-press / context menu) → Settings**.

| Setting | Default | What it does |
|---------|---------|--------------|
| Preferred quality | Auto | Auto / 1080p / 720p / 480p / 360p for source picking |
| Maximum sources | 20 | How many stream sources to list per movie |
| Use inputstream.adaptive | On | Use `inputstream.adaptive` for HLS playback |
| Resolve timeout (s) | 25 | How long to wait when resolving a stream |
| Enable debug logging | Off | Write extra info to the Kodi log |

## Troubleshooting

- **"Cannot connect to server"** — make sure GitHub Pages is enabled and the
  Kodi source is the site root URL `https://teenpatti007.github.io/1/` (GitHub Pages source must be set to /docs)
  (not a raw file link).
- **HLS won't play** — ensure `inputstream.adaptive` is installed/enabled and
  *Use InputStream Adaptive* is On.
- **No sources / "unresolved"** — the source site may be down or blocked by
  your ISP; try another source or a VPN.
- **Code rejected** — codes are single-device; ask your provider for a new one.

## Disclaimer

MovieHub is a personal streaming tool for public movie websites. Stream
availability, quality, and legality depend on your jurisdiction and the source
sites, which change often. The author is not affiliated with any source site.
Streaming copyrighted content may be illegal in your country — use at your own
risk, for personal use only.
