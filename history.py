import json
from pathlib import Path
from datetime import datetime

HISTORY_FILE = "download_history.json"

def load_history():
    history_file = Path(HISTORY_FILE)
    if history_file.exists():
        with open(history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("download_history", [])
    return []

def save_history(history):
    history_file = Path(HISTORY_FILE)
    data = {"download_history": history}
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def find_entry(title, artist):
    history = load_history()
    for entry in history:
        if entry.get("title") == title and entry.get("artist") == artist:
            return entry
    return None

def add_entry(title, artist, url, filepath):
    history = load_history()
    entry = {
        "title": title,
        "artist": artist,
        "url": url,
        "file": str(filepath)
    }
    history.append(entry)
    save_history(history)