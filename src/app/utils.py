import os
import hashlib
import json
import time

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename: str) -> bool:
    """Return True if filename has an allowed image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_hash(filepath: str) -> str:
    """Generate SHA-256 hash of file for cache key."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return ""


def load_cache(cache_file: str) -> dict:
    """Load cache data from JSON file."""
    if not os.path.exists(cache_file):
        return {}
    
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_cache(cache_file: str, cache_data: dict) -> bool:
    """Save cache data to JSON file."""
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving cache: {e}")
        return False


def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """Remove files older than max_age_hours from directory."""
    if not os.path.exists(directory):
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    removed_count = 0
    
    try:
        for filename in os.listdir(directory):
            if filename.endswith('.json'):  # Skip cache metadata files
                continue
                
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    os.remove(filepath)
                    removed_count += 1
                    print(f"Removed old file: {filename}")
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    return removed_count


def cleanup_cache_entries(cache_file: str, cache_folder: str) -> int:
    """Remove cache entries for files that no longer exist."""
    cache_data = load_cache(cache_file)
    if not cache_data:
        return 0
    
    removed_count = 0
    keys_to_remove = []
    
    for cache_key, entry in cache_data.items():
        cached_file_path = os.path.join(cache_folder, entry.get("output_filename", ""))
        if not os.path.exists(cached_file_path):
            keys_to_remove.append(cache_key)
            removed_count += 1
    
    for key in keys_to_remove:
        del cache_data[key]
    
    if keys_to_remove:
        save_cache(cache_file, cache_data)
        print(f"Removed {removed_count} stale cache entries")
    
    return removed_count


def get_cache_size(cache_folder: str) -> tuple:
    """Get cache folder size and file count."""
    if not os.path.exists(cache_folder):
        return 0, 0
    
    total_size = 0
    file_count = 0
    
    try:
        for dirpath, dirnames, filenames in os.walk(cache_folder):
            for filename in filenames:
                if not filename.endswith('.json'):
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
                    file_count += 1
    except Exception:
        pass
    
    return total_size, file_count