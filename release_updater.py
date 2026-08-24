# -*- coding: utf-8 -*-
"""
release_updater.py - Automated Release & Version Bump Tool for MovieHub Repository

Usage:
  1. Interactive mode:
     python release_updater.py

  2. Command line mode with zip file:
     python release_updater.py "C:\path\to\new_addon.zip"

  3. Command line mode with version bump:
     python release_updater.py --bump 2.0.7
"""

import os
import sys
import re
import shutil
import zipfile
import hashlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.join(ROOT_DIR, "plugin.video.moviehub")
REPO_DIR = os.path.join(ROOT_DIR, "repository.moviehub")
SERVICE_DIR = os.path.join(ROOT_DIR, "service.moviehub.updater")
PLUGIN_XML = os.path.join(PLUGIN_DIR, "addon.xml")
REPO_XML = os.path.join(REPO_DIR, "addon.xml")
SERVICE_XML = os.path.join(SERVICE_DIR, "addon.xml")

GITHUB_USER = "jmadhavp"
REPO_NAME = "mhubs"
BASE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/"


def get_addon_version(xml_path):
    if not os.path.exists(xml_path):
        return None
    with open(xml_path, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'<addon\b[^>]*\bversion=["\']([^"\']+)["\']', content)
    return m.group(1) if m else None


def set_addon_version(xml_path, new_ver):
    with open(xml_path, "r", encoding="utf-8") as f:
        content = f.read()
    updated = re.sub(
        r'(<addon\b[^>]*\bversion=["\'])[^"\']+(["\'])',
        r'\g<1>' + new_ver + r'\g<2>',
        content,
        count=1
    )
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(updated)


def bump_version_string(current_ver):
    parts = current_ver.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    except Exception:
        return current_ver + ".1"


def extract_zip_to_plugin(zip_path):
    print(f"📦 Extracting updated ZIP: {zip_path}")
    temp_extract = os.path.join(ROOT_DIR, "_temp_extract")
    if os.path.exists(temp_extract):
        shutil.rmtree(temp_extract)
    os.makedirs(temp_extract, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract)

    # Locate the addon files (whether at root or inside a folder)
    source_folder = temp_extract
    if os.path.exists(os.path.join(temp_extract, "addon.xml")):
        source_folder = temp_extract
    else:
        # Check subdirectories
        subdirs = [os.path.join(temp_extract, d) for d in os.listdir(temp_extract) if os.path.isdir(os.path.join(temp_extract, d))]
        for sd in subdirs:
            if os.path.exists(os.path.join(sd, "addon.xml")):
                source_folder = sd
                break

    new_xml = os.path.join(source_folder, "addon.xml")
    new_ver = get_addon_version(new_xml)

    # Sync files into PLUGIN_DIR
    for root, dirs, files in os.walk(source_folder):
        rel_root = os.path.relpath(root, source_folder)
        target_root = os.path.join(PLUGIN_DIR, rel_root) if rel_root != "." else PLUGIN_DIR
        os.makedirs(target_root, exist_ok=True)
        for file in files:
            if file.endswith('.pyc') or '__pycache__' in root or file.endswith('.zip'):
                continue
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_root, file)
            shutil.copy2(src_file, dst_file)

    shutil.rmtree(temp_extract, ignore_errors=True)
    print("✅ Plugin source directory updated successfully.")
    return new_ver


def rebuild_repository(bump_all=False):
    print("\n🔄 Rebuilding Repository Package & Metadata...")

    # Load versions
    plugin_ver = get_addon_version(PLUGIN_XML)
    repo_ver = get_addon_version(REPO_XML)
    service_ver = get_addon_version(SERVICE_XML)

    if bump_all:
        plugin_ver = bump_version_string(plugin_ver)
        repo_ver = bump_version_string(repo_ver)
        service_ver = bump_version_string(service_ver)
        set_addon_version(PLUGIN_XML, plugin_ver)
        set_addon_version(REPO_XML, repo_ver)
        set_addon_version(SERVICE_XML, service_ver)
    print(f"   - MovieHub Plugin Version: {plugin_ver}")
    print(f"   - Repository Version: {repo_ver}")
    print(f"   - Updater Service Version: {service_ver}")

    # Remove old zips inside plugin folder
    for f in os.listdir(PLUGIN_DIR):
        if f.endswith(".zip"):
            os.remove(os.path.join(PLUGIN_DIR, f))

    # Remove old zips inside repo folder
    for f in os.listdir(REPO_DIR):
        if f.endswith(".zip"):
            os.remove(os.path.join(REPO_DIR, f))

    # Remove old zips inside service folder
    for f in os.listdir(SERVICE_DIR):
        if f.endswith(".zip"):
            os.remove(os.path.join(SERVICE_DIR, f))

    # Zip helper
    def zip_folder(source_folder, zip_filepath, archive_folder_name):
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as ziph:
            for root, dirs, files in os.walk(source_folder):
                for file in files:
                    if file.endswith('.pyc') or '__pycache__' in root or file.endswith('.zip'):
                        continue
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, source_folder)
                    arcname = os.path.join(archive_folder_name, rel_path)
                    ziph.write(file_path, arcname)

    # 1. Zip plugin
    plugin_zip_name = f"plugin.video.moviehub-{plugin_ver}.zip"
    plugin_zip_path = os.path.join(PLUGIN_DIR, plugin_zip_name)
    zip_folder(PLUGIN_DIR, plugin_zip_path, "plugin.video.moviehub")
    print(f"   ✅ Created {plugin_zip_name}")

    # 2. Zip repo
    repo_zip_name = f"repository.moviehub-{repo_ver}.zip"
    repo_zip_path = os.path.join(REPO_DIR, repo_zip_name)
    zip_folder(REPO_DIR, repo_zip_path, "repository.moviehub")

    # Copy repo zip to root
    top_repo_zip = os.path.join(ROOT_DIR, repo_zip_name)
    shutil.copy2(repo_zip_path, top_repo_zip)
    print(f"   ✅ Created {repo_zip_name} (in repo dir & root)")

    # 3. Zip service
    service_zip_name = f"service.moviehub.updater-{service_ver}.zip"
    service_zip_path = os.path.join(SERVICE_DIR, service_zip_name)
    zip_folder(SERVICE_DIR, service_zip_path, "service.moviehub.updater")
    print(f"   ✅ Created {service_zip_name}")

    # 3. Generate addons.xml
    addons_xml_path = os.path.join(ROOT_DIR, "addons.xml")
    addons_content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'

    for addon_path in [REPO_DIR, PLUGIN_DIR, SERVICE_DIR]:
        xml_file = os.path.join(addon_path, "addon.xml")
        if os.path.exists(xml_file):
            with open(xml_file, "r", encoding="utf-8") as f:
                content = f.read()
                content = re.sub(r'<\?xml[^>]+\?>', '', content).strip()
                addons_content += content + "\n"

    addons_content += '</addons>\n'

    with open(addons_xml_path, "w", encoding="utf-8") as f:
        f.write(addons_content)

    # 4. Generate addons.xml.md5
    md5_hash = hashlib.md5(addons_content.encode('utf-8')).hexdigest()
    addons_md5_path = os.path.join(ROOT_DIR, "addons.xml.md5")
    with open(addons_md5_path, "w", encoding="utf-8") as f:
        f.write(md5_hash)

    print(f"   ✅ Generated addons.xml & addons.xml.md5 (MD5: {md5_hash})")

    # 5. Generate index.html
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MovieHub Kodi Repository</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 750px;
            width: 100%;
            background-color: #1e293b;
            padding: 32px;
            border-radius: 12px;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);
            border: 1px solid #334155;
        }}
        h1 {{
            color: #38bdf8;
            margin-top: 0;
            font-size: 2rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .badge {{
            background: #0284c7;
            color: #fff;
            font-size: 0.85rem;
            padding: 3px 8px;
            border-radius: 4px;
        }}
        .btn {{
            display: inline-block;
            background: #0284c7;
            color: #fff;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin: 15px 0;
            transition: background 0.2s;
        }}
        .btn:hover {{
            background: #0369a1;
        }}
        .code-box {{
            background: #090d16;
            padding: 14px 18px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 1.1rem;
            color: #f1f5f9;
            border: 1px solid #475569;
            word-break: break-all;
        }}
        ol {{
            line-height: 1.8;
            padding-left: 20px;
        }}
        li strong {{
            color: #38bdf8;
        }}
        .files {{
            margin-top: 25px;
            background: #0f172a;
            padding: 15px;
            border-radius: 8px;
        }}
        .files ul {{
            list-style: none;
            padding: 0;
            margin: 5px 0 0 0;
        }}
        .files li {{
            padding: 5px 0;
        }}
        .files a {{
            color: #38bdf8;
            text-decoration: none;
        }}
        .files a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 MovieHub Repository <span class="badge">v{repo_ver}</span></h1>
        <p>Official Repository for MovieHub Kodi Addon with automatic updates.</p>

        <a href="{repo_zip_name}" class="btn">⬇ Download Repository ZIP</a>

        <h3>Kodi Source URL</h3>
        <p>Add this URL to your Kodi File Manager:</p>
        <div class="code-box">{BASE_URL}</div>

        <h3>Installation Steps</h3>
        <ol>
            <li>In Kodi, go to <strong>Settings &gt; File Manager &gt; Add Source</strong>.</li>
            <li>Enter the URL above (<code>{BASE_URL}</code>) and name it <strong>MovieHub Repo</strong>.</li>
            <li>Go to <strong>Settings &gt; Add-ons &gt; Install from zip file</strong>.</li>
            <li>Select <strong>MovieHub Repo</strong> and choose <code>{repo_zip_name}</code>.</li>
            <li>Once installed, select <strong>Install from repository &gt; MovieHub Repository &gt; Video add-ons &gt; MovieHub - Free Movies</strong>.</li>
        </ol>

        <div class="files">
            <strong>Latest Release:</strong> MovieHub v{plugin_ver}<br>
            <strong>Repository Files:</strong>
            <ul>
                <li><a href="{repo_zip_name}">{repo_zip_name}</a></li>
                <li><a href="addons.xml">addons.xml</a></li>
                <li><a href="addons.xml.md5">addons.xml.md5</a></li>
                <li><a href="plugin.video.moviehub/{plugin_zip_name}">plugin.video.moviehub/{plugin_zip_name}</a></li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
    with open(os.path.join(ROOT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    print("   ✅ Updated index.html")
    print(f"\n🚀 Release Update Complete for MovieHub v{plugin_ver}!")
    print("\nNext Steps to publish to GitHub:")
    print("  git add .")
    print(f'  git commit -m "Release MovieHub v{plugin_ver}"')
    print("  git push origin main")


def main():
    current_ver = get_addon_version(PLUGIN_XML) or "2.0.6"
    print("==================================================")
    print("   🎬 MovieHub Repository Release Updater")
    print(f"   Current Plugin Version: v{current_ver}")
    print("==================================================")

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--bump":
            new_ver = sys.argv[2] if len(sys.argv) > 2 else bump_version_string(current_ver)
            print(f"--> Bumping plugin version to v{new_ver}")
            set_addon_version(PLUGIN_XML, new_ver)
            rebuild_repository()
            return
        elif arg == "--bump-all":
            print("--> Bumping ALL versions (plugin, repo, service)")
            rebuild_repository(bump_all=True)
            return
        elif os.path.exists(arg) and arg.endswith(".zip"):
            extract_zip_to_plugin(arg)
            # Ask if user wants to bump version
            zip_ver = get_addon_version(PLUGIN_XML)
            if zip_ver == current_ver:
                new_ver = bump_version_string(current_ver)
                print(f"--> Auto-bumping version from v{current_ver} to v{new_ver}")
                set_addon_version(PLUGIN_XML, new_ver)
            rebuild_repository()
            return

    # Interactive mode
    print("\nSelect an option:")
    print(" [1] Import & update from a new Addon ZIP file")
    print(" [2] Automatically bump plugin version (e.g. v2.0.6 -> v2.0.7)")
    print(" [3] Set custom plugin version number")
    print(" [4] Bump ALL versions (plugin + repo + service)")
    print(" [5] Re-build repository metadata only")
    choice = input("\nEnter choice [1-5]: ").strip()

    if choice == "1":
        zip_path = input("Enter full path to new addon ZIP file: ").strip('"\' ')
        if os.path.exists(zip_path) and zip_path.endswith(".zip"):
            extracted_ver = extract_zip_to_plugin(zip_path)
            if extracted_ver == current_ver:
                suggested = bump_version_string(current_ver)
                do_bump = input(f"ZIP has version v{extracted_ver}. Bump to v{suggested}? [Y/n]: ").strip().lower()
                if do_bump in ("", "y", "yes"):
                    set_addon_version(PLUGIN_XML, suggested)
            rebuild_repository()
        else:
            print("❌ File not found or not a valid .zip file.")
    elif choice == "2":
        new_ver = bump_version_string(current_ver)
        print(f"--> Bumping plugin version to v{new_ver}")
        set_addon_version(PLUGIN_XML, new_ver)
        rebuild_repository()
    elif choice == "3":
        custom_ver = input(f"Enter new version number (current: v{current_ver}): ").strip()
        if custom_ver:
            set_addon_version(PLUGIN_XML, custom_ver)
            rebuild_repository()
    elif choice == "4":
        print("--> Bumping ALL versions (plugin + repo + service)")
        rebuild_repository(bump_all=True)
    elif choice == "5":
        rebuild_repository()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()
