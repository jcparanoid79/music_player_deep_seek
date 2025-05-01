# System Architecture

## High-Level Component Diagram

```mermaid
graph TD
    UI[UI Layer - PyQt] --> |User Events| Service
    Service[Service Layer] --> |Audio Control| Core
    Core[Core Layer] --> |File Operations| Storage[(Audio Files)]
    Core --> |Audio Output| Sound[Sound Device]
```

## Data Flow Diagram

```mermaid
graph LR
    AF[Audio File] --> |Read| Parser[File Parser]
    Parser --> |Chunks| Buffer[Audio Buffer]
    Buffer --> |Stream| Engine[Audio Engine]
    Engine --> |Output| Device[Sound Device]
    UI[User Interface] --> |Commands| Engine
```

## Module Structure

```
src/
├── ui/
│   ├── main_window.py
│   ├── playlist_view.py
│   └── controls.py
├── service/
│   ├── audio_service.py
│   └── playlist_service.py
├── core/
│   ├── audio_engine.py
│   ├── file_handler.py
│   └── metadata.py
└── main.py
```

## Key Components

### UI Layer

- Main Window: Primary application interface
- Playlist View: Track list management
- Controls: Playback interface

### Service Layer

- Audio Service: Manages playback state including automatic track progression
- Playlist Service: Handles track organization

### Core Layer

- Audio Engine: Low-level audio processing with automatic track transition handling
- File Handler: Audio file operations
- Metadata: Track information management

## Technology Stack

- **Frontend**: PyQt6
- **Audio Processing**: sounddevice, pydub
- **Testing**: pytest
- **Code Quality**: Black, Ruff
- **Build/Package**: uv, pyproject.toml
