# Music Player Deep Seek

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A Python-based music player application with playlist management and automatic track sequencing.

## Features

- Play audio files in various formats
- Automatic playlist progression
- Intuitive user interface
- Playlist management
- Cross-platform compatibility

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/music_player_deep_seek.git
cd music_player_deep_seek
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies:

```bash
pip install -e .
```

## Usage

Run the application:

```bash
python src/main.py
```

### Controls

- Play/Pause: Spacebar
- Next Track: Right Arrow
- Previous Track: Left Arrow
- Volume Up/Down: Up/Down Arrows

## Project Structure

```
music_player_deep_seek/
├── src/                  # Main application source
│   ├── core/             # Core functionality
│   ├── static/           # Static files (JS, CSS)
│   ├── templates/        # HTML templates
│   └── __init__.py       # Package initialization
├── tests/                # Test files
├── docs/                 # Documentation
├── pyproject.toml        # Project configuration
└── README.md             # This file
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
