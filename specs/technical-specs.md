# Technical Specifications

## Architecture

The music player uses a layered architecture:

- UI Layer: PyQt-based interface
- Service Layer: Audio processing and playback control
- Core Layer: File handling and audio decoding

## Components

### Audio Engine

- Uses `sounddevice` for low-level audio output
- `pydub` for audio file manipulation
- Custom seeking implementation using binary chunks

### Data Flow

1. Audio file loaded into memory buffers
2. Processed through audio engine
3. Streamed to audio output device
4. UI updates based on playback state

## APIs

### Core Audio API

```python
class AudioEngine:
    def play(self, position: float = 0.0) -> None
    def pause() -> None
    def seek(self, position: float) -> None
    def get_metadata() -> dict
```

### Playlist Management API

```python
class PlaylistManager:
    def add_track(self, path: str) -> None
    def remove_track(self, index: int) -> None
    def get_playlist() -> List[Track]
```

## Device Integration

### USB Device Detection

- WebUSB API for device discovery
- Windows path format: `\\?\usb#vid_{vendor_id}&pid_{product_id}#{serial}#`
- Linux path format: `/dev/bus/usb/{bus}/{device}`
- Supported protocols: MTP, USB Mass Storage

### Android Device Integration

- MTP (Media Transfer Protocol) support
- Android path format: `/storage/emulated/0/Music`
- File system access via `libmtp`
- Android Debug Bridge (ADB) fallback

## API Endpoints

### Device Management

```
GET /api/devices
    - List connected USB and Android devices

POST /api/devices/{device_id}/scan
    - Scan device for media files
    - Returns file listing with paths
```

### Metadata Services

```
GET /api/metadata/fetch
    - Parameters: artist, title, album
    - Returns: artwork, lyrics, additional metadata

POST /api/metadata/cache
    - Cache fetched metadata locally
```

## Security Considerations

- USB device whitelisting
- MTP authentication handling
- Secure storage of device credentials
- Rate limiting for web scraping

## Data Flow

1. Device Detection

   - WebUSB event triggers
   - Device path identification
   - Protocol negotiation

2. File System Access

   - Path normalization
   - Permission verification
   - File system traversal

3. Metadata Processing
   - Local file metadata extraction
   - Web service queries
   - Cache management

## Technical Requirements

- Python 3.10+
- Audio buffer size: 2048 samples
- Sample rate: 44.1kHz/48kHz
- Bit depth: 16/24-bit
- Seeking precision: 1ms
