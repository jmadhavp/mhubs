import os
import re
import hashlib
import zipfile
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
GITHUB_USER = "jmadhavp"
REPO_NAME = "mhubs"
BASE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/"

def get_addon_info(addon_xml_path):
    if not os.path.exists(addon_xml_path):
        return None, None
    with open(addon_xml_path, "r", encoding="utf-8") as f:
        content = f.read()
    m_id = re.search(r'<addon\b[^>]*\bid=["\']([^"\']+)["\']', content)
    m_ver = re.search(r'<addon\b[^>]*\bversion=["\']([^"\']+)["\']', content)
    addon_id = m_id.group(1) if m_id else None
    addon_ver = m_ver.group(1) if m_ver else None
    return addon_id, addon_ver

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

def generate():
    print("=== Kodi Repository Generator ===")
    
    addons = []
    
    for item in os.listdir(ROOT_DIR):
        item_path = os.path.join(ROOT_DIR, item)
        if os.path.isdir(item_path) and not item.startswith(".") and item not in ["extracted"]:
            xml_path = os.path.join(item_path, "addon.xml")
            addon_id, addon_ver = get_addon_info(xml_path)
            if addon_id and addon_ver:
                addons.append((addon_id, addon_ver, item_path))

    if not addons:
        print("No addons found!")
        return

    # Clean old zip files in addon subdirectories
    for addon_id, addon_ver, addon_path in addons:
        for f in os.listdir(addon_path):
            if f.endswith(".zip"):
                os.remove(os.path.join(addon_path, f))
        
        zip_name = f"{addon_id}-{addon_ver}.zip"
        zip_dest = os.path.join(addon_path, zip_name)
        zip_folder(addon_path, zip_dest, addon_id)
        print(f"[{addon_id}] Created {zip_name}")
        
        # If repository addon, also place zip at top level for easy direct download
        if addon_id.startswith("repository."):
            top_zip = os.path.join(ROOT_DIR, f"{addon_id}-{addon_ver}.zip")
            shutil.copy2(zip_dest, top_zip)
            print(f"[{addon_id}] Copied to top-level: {addon_id}-{addon_ver}.zip")

    # Generate addons.xml
    addons_xml_path = os.path.join(ROOT_DIR, "addons.xml")
    addons_content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'

    for addon_id, addon_ver, addon_path in addons:
        xml_file = os.path.join(addon_path, "addon.xml")
        with open(xml_file, "r", encoding="utf-8") as f:
            content = f.read()
            content = re.sub(r'<\?xml[^>]+\?>', '', content).strip()
            addons_content += content + "\n"

    addons_content += '</addons>\n'

    with open(addons_xml_path, "w", encoding="utf-8") as f:
        f.write(addons_content)

    # Generate addons.xml.md5
    md5_hash = hashlib.md5(addons_content.encode('utf-8')).hexdigest()
    addons_md5_path = os.path.join(ROOT_DIR, "addons.xml.md5")
    with open(addons_md5_path, "w", encoding="utf-8") as f:
        f.write(md5_hash)

    print(f"Generated addons.xml & addons.xml.md5 (MD5: {md5_hash})")

    # Update index.html
    repo_zip = [f"{aid}-{aver}.zip" for aid, aver, _ in addons if aid.startswith("repository.")]
    plugin_zips = [f"{aid}/{aid}-{aver}.zip" for aid, aver, _ in addons if not aid.startswith("repository.")]
    
    repo_zip_str = repo_zip[0] if repo_zip else "repository.moviehub-1.0.0.zip"
    
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
        <h1>🎬 MovieHub Repository <span class="badge">v1.0.0</span></h1>
        <p>Official Repository for MovieHub Kodi Addon with automatic updates.</p>

        <a href="{repo_zip_str}" class="btn">⬇ Download Repository ZIP</a>

        <h3>Kodi Source URL</h3>
        <p>Add this URL to your Kodi File Manager:</p>
        <div class="code-box">{BASE_URL}</div>

        <h3>Installation Steps</h3>
        <ol>
            <li>In Kodi, go to <strong>Settings &gt; File Manager &gt; Add Source</strong>.</li>
            <li>Enter the URL above (<code>{BASE_URL}</code>) and name it <strong>MovieHub Repo</strong>.</li>
            <li>Go to <strong>Settings &gt; Add-ons &gt; Install from zip file</strong>.</li>
            <li>Select <strong>MovieHub Repo</strong> and choose <code>{repo_zip_str}</code>.</li>
            <li>Once installed, select <strong>Install from repository &gt; MovieHub Repository &gt; Video add-ons &gt; MovieHub - Free Movies</strong>.</li>
        </ol>

        <div class="files">
            <strong>Repository Files:</strong>
            <ul>
                <li><a href="{repo_zip_str}">{repo_zip_str}</a></li>
                <li><a href="addons.xml">addons.xml</a></li>
                <li><a href="addons.xml.md5">addons.xml.md5</a></li>
                {"".join(f'<li><a href="{pz}">{pz}</a></li>' for pz in plugin_zips)}
            </ul>
        </div>
    </div>
</body>
</html>
"""
    with open(os.path.join(ROOT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Updated index.html")

if __name__ == "__main__":
    generate()
