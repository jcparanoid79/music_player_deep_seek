import os
import re
from typing import Optional

LYRICS_DIR = os.path.join(os.path.dirname(__file__), "local_lyrics")
os.makedirs(LYRICS_DIR, exist_ok=True)


def parse_local_lyrics(artist: str, title: str) -> Optional[str]:
    """Parse lyrics from local text files."""
    try:
        # Try exact match first
        filename = f"{artist} - {title}.txt".replace("/", "_")
        filepath = os.path.join(LYRICS_DIR, filename)

        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()

        # Try fuzzy matching
        for filename in os.listdir(LYRICS_DIR):
            if re.search(re.escape(title), filename, re.IGNORECASE):
                filepath = os.path.join(LYRICS_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read()

    except Exception as e:
        print(f"Error parsing local lyrics: {e}")

    return None
