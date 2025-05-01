import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast
from urllib.parse import quote

import aiohttp
from bs4 import BeautifulSoup, Tag

CACHE_DIR = Path(__file__).parent.parent / 'static' / 'cache'
CACHE_DIR.mkdir(exist_ok=True)

async def fetch_url(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
        return await response.text()

async def search_artwork(artist: str, album: str) -> Optional[str]:
    search_url = (
        f"https://musicbrainz.org/ws/2/release?"
        f"query={quote(artist)}+{quote(album)}&fmt=json"
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(search_url) as response:
                data = await response.json()
                if 'releases' in data and data['releases']:
                    release = data['releases'][0]
                    if 'id' in release:
                        cover_url = (
                            f"https://coverartarchive.org/release/{release['id']}/front"
                        )
                        async with session.get(cover_url) as img_response:
                            if img_response.status == 200:
                                return cover_url
        except Exception:
            pass
    return None

async def _search_genius_lyrics(artist: str, title: str) -> Optional[str]:
    search_url = (
        f"https://genius.com/api/search/song?"
        f"q={quote(artist)}+{quote(title)}"
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(search_url) as response:
                data = await response.json()
                if 'response' in data and 'hits' in data['response']:
                    for hit in data['response']['hits']:
                        song = hit['result']
                        if song['primary_artist']['name'].lower() == artist.lower():
                            lyrics_url = song['url']
                            html = await fetch_url(session, lyrics_url)
                            soup = BeautifulSoup(html, 'html.parser')
                            lyrics_div = soup.find('div', class_='lyrics')
                            if isinstance(lyrics_div, Tag):
                                return lyrics_div.get_text().strip()
        except Exception:
            pass
    return None

async def _search_azlyrics(artist: str, title: str) -> Optional[str]:
    search_url = (
        f"https://search.azlyrics.com/search.php?"
        f"q={quote(artist)}+{quote(title)}"
    )

    async with aiohttp.ClientSession() as session:
        try:
            html = await fetch_url(session, search_url)
            soup = BeautifulSoup(html, 'html.parser')

            for td in soup.find_all('td', class_='text-left'):
                if not isinstance(td, Tag):
                    continue

                link = td.find('a')
                if link and isinstance(link, Tag):
                    link_text = link.get_text()
                    if artist.lower() in link_text.lower():
                        lyrics_url = cast(str, link.get('href'))
                        if lyrics_url:
                            lyrics_html = await fetch_url(session, lyrics_url)
                            lyrics_soup = BeautifulSoup(lyrics_html, 'html.parser')
                            lyrics_div = lyrics_soup.find('div', class_='lyricsh')
                            if isinstance(lyrics_div, Tag):
                                next_div = lyrics_div.find_next('div')
                                if isinstance(next_div, Tag):
                                    return next_div.get_text().strip()
        except Exception:
            pass
    return None

async def search_lyrics(artist: str, title: str) -> Optional[str]:
    lyrics = await _search_genius_lyrics(artist, title)
    if not lyrics:
        lyrics = await _search_azlyrics(artist, title)
    return lyrics

async def fetch_metadata(
    artist: Optional[str] = None,
    title: Optional[str] = None,
    album: Optional[str] = None
) -> Dict[str, Union[str, List[str], None]]:
    metadata: Dict[str, Union[str, List[str], None]] = {
        "artwork_url": None,
        "lyrics": None,
        'additional_info': str({})
    }

    if artist and album:
        metadata['artwork_url'] = await search_artwork(artist, album)

    if artist and title:
        metadata['lyrics'] = await search_lyrics(artist, title)

    return metadata

def cache_metadata(data: Dict[str, Any]) -> None:
    if "artist" in data and "title" in data:
        artist = str(data.get("artist", ""))
        title = str(data.get("title", ""))
        artist_title = f"{artist}_{title}"
        cache_key = artist_title.lower().replace(" ", "_")
        cache_file = CACHE_DIR / f"{cache_key}.json"

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def get_cached_metadata(artist: str, title: str) -> Optional[Dict[str, Any]]:
    artist_title = f"{artist}_{title}"
    cache_key = artist_title.lower().replace(" ", "_")
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if cache_file.exists():
        with cache_file.open('r', encoding='utf-8') as f:
            return json.load(f)

    return None
