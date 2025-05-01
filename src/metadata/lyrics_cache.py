import json
import os
from typing import Optional

CACHE_DIR = os.path.join(os.path.dirname(__file__), "lyrics_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def get_cache_key(artist: str, title: str) -> str:
    """Generate a consistent cache key for lyrics."""
    return f"{artist.lower()}_{title.lower()}.json"


def get_cached_lyrics(artist: str, title: str) -> Optional[str]:
    """Get lyrics from local cache if available."""
    try:
        cache_file = os.path.join(CACHE_DIR, get_cache_key(artist, title))
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("lyrics")
    except Exception:
        pass
    return None


def cache_lyrics(artist: str, title: str, lyrics: str) -> None:
    """Cache lyrics locally."""
    try:
        cache_file = os.path.join(CACHE_DIR, get_cache_key(artist, title))
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"artist": artist, "title": title, "lyrics": lyrics}, f)
    except Exception as e:
        print(f"Error caching lyrics: {e}")
