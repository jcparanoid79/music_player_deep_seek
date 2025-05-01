import json
from unittest.mock import AsyncMock, patch

import pytest

from src.metadata.web_metadata import (
    cache_metadata,
    fetch_metadata,
    get_cached_metadata,
    search_artwork,
)


@pytest.fixture
def sample_metadata():
    return {
        'artist': 'Test Artist',
        'title': 'Test Song',
        'album': 'Test Album',
        'artwork_url': 'https://example.com/artwork.jpg',
        'lyrics': 'Test lyrics\nSecond line'
    }


@pytest.fixture
def cache_dir(tmp_path):
    cache_dir = tmp_path / 'cache'
    cache_dir.mkdir()
    with patch('src.metadata.web_metadata.CACHE_DIR', cache_dir):
        yield cache_dir


@pytest.mark.asyncio
async def test_search_artwork():
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            'releases': [{
                'id': 'test-id',
                'title': 'Test Album'
            }]
        }
        mock_get = mock_session.return_value.__aenter__.return_value.get
        mock_get.return_value = mock_response

        result = await search_artwork('Test Artist', 'Test Album')
        assert result == 'https://coverartarchive.org/release/test-id/front'


@pytest.mark.asyncio
async def test_fetch_metadata():
    with patch('src.metadata.web_metadata.search_artwork') as mock_artwork:
        mock_artwork.return_value = 'https://example.com/artwork.jpg'

        metadata = await fetch_metadata(
            artist='Test Artist',
            title='Test Song',
            album='Test Album'
        )

        assert metadata['artwork_url'] == 'https://example.com/artwork.jpg'


def test_cache_metadata(cache_dir, sample_metadata):
    cache_metadata(sample_metadata)

    artist_title = f"{sample_metadata['artist']}_{sample_metadata['title']}"
    cache_key = artist_title.lower().replace(' ', '_')
    cache_file = cache_dir / f"{cache_key}.json"

    assert cache_file.exists()
    with cache_file.open('r') as f:
        cached_data = json.load(f)
    assert cached_data == sample_metadata


def test_get_cached_metadata(cache_dir, sample_metadata):
    # First cache the metadata
    cache_metadata(sample_metadata)

    # Then try to retrieve it
    result = get_cached_metadata('Test Artist', 'Test Song')
    assert result == sample_metadata


def test_get_cached_metadata_missing(cache_dir):
    result = get_cached_metadata('Nonexistent Artist', 'Nonexistent Song')
    assert result is None
