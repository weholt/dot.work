import os
import zipfile
import requests
from pathlib import Path
from dotenv import dotenv_values
from gitignore_parser import parse_gitignore

def load_api_url():
    config_path = Path.home() / ".zipparu"
    if not config_path.exists():
        raise FileNotFoundError(f"{config_path} not found")
    config = dotenv_values(config_path)
    url = config.get("API_URL")
    if not url:
        raise ValueError("API_URL missing in .zipparu")
    return url

def should_include(filepath, ignore_matcher):
    if ignore_matcher:
        try:
            return not ignore_matcher(filepath)
        except Exception:
            return True
    return True

def zip_folder(folder_path, output_path):
    gitignore_path = Path(folder_path) / ".gitignore"
    ignore_matcher = parse_gitignore(gitignore_path) if gitignore_path.exists() else None

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for name in files:
                file_path = Path(root) / name
                rel_path = file_path.relative_to(folder_path)
                if should_include(str(file_path), ignore_matcher):
                    zipf.write(file_path, rel_path)

def upload_zip(zip_path, api_url):
    with open(zip_path, "rb") as f:
        resp = requests.post(api_url, files={"file": (zip_path.name, f, "application/zip")})
    resp.raise_for_status()
    print(f"Uploaded successfully: {resp.status_code}")

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: zipparu <folder_path>")
        return
    folder = Path(sys.argv[1]).resolve()
    if not folder.is_dir():
        raise NotADirectoryError(folder)

    zip_name = f"{folder.name}.zip"
    output_path = Path.cwd() / zip_name
    zip_folder(folder, output_path)
    api_url = load_api_url()
    upload_zip(output_path, api_url)