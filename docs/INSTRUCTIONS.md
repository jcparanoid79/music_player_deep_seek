# Development Setup Instructions

## Prerequisites

- Python 3.10 or higher
- uv package manager
- Git

## Initial Setup

1. Clone the repository:

```bash
git clone [repository-url]
cd music-player-deep-seek
```

2. Set up virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
uv pip install -r requirements.in
```

## Development Workflow

### Running the Application

```bash
python -m src.main
```

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

- We use Black for code formatting
- Ruff for linting
- Type hints are required for all functions

### Git Workflow

1. Create feature branch: `git checkout -b feature/name`
2. Make changes
3. Run tests: `python -m pytest`
4. Commit changes: `git commit -m "descriptive message"`
5. Push branch: `git push origin feature/name`

## Player Features

- **Continuous Playback**: The player automatically plays the next track in the playlist when the current track ends
- Manual controls are still available for play/pause/next/previous
- Supports both sequential and shuffle playback modes

## Common Commands

- Format code: `black src/ tests/`
- Run linter: `ruff check src/ tests/`
- Run tests with coverage: `pytest --cov=src tests/`
