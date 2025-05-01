import io  # Import io for BytesIO  # Import io for BytesIO
import logging  # Add logging import here
import mimetypes  # To guess mime type  # To guess mime type
import os
import re
import urllib.parse  # Import urllib.parse
from typing import (  # Added Any, Dict, List, Optional, Tuple
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)

import mutagen
from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from mutagen import File as MutagenFile  # type: ignore

# Type ignore for mutagen imports that Pylance doesn't recognize
from mutagen import MutagenError  # type: ignore
from pydub import AudioSegment  # Import AudioSegment
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "static", "uploads"
)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

import requests  # For fetching lyrics page
from bs4 import BeautifulSoup  # For parsing lyrics page

from .metadata.web_metadata import fetch_metadata

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    try:
        # Verify template exists before rendering
        template_dir = current_app.template_folder
        if not template_dir:
            raise RuntimeError("Flask template_folder is not configured")

        template_path = os.path.join(template_dir, "player.html")
        if not os.path.exists(template_path):
            raise RuntimeError(f"Template not found at: {template_path}")

        return render_template("player.html")
    except Exception as e:
        error_msg = f"Template rendering error: {str(e)}"
        print(error_msg)
        return error_msg, 500


@bp.route("/static/uploads/<filename>")
def uploaded_file(filename):
    """Serve uploaded files."""
    # Decode the filename from the URL
    decoded_filename = urllib.parse.unquote(filename)
    # Apply secure_filename to find the actual file on the filesystem
    secure_name_on_disk = secure_filename(decoded_filename)
    # Serve the file using the secure filename
    return send_from_directory(UPLOAD_FOLDER, secure_name_on_disk)


@bp.route("/api/upload", methods=["POST"])
def upload_file() -> Response | Tuple[Response, int]:
    """Handle file uploads."""
    if "files" not in request.files:
        return jsonify({"error": "No files part"}), 400

    files = request.files.getlist("files")
    if not files or not any(f.filename for f in files):
        return jsonify({"error": "No selected files"}), 400

    results = []
    for file in files:
        if file and file.filename:
            # Use secure_filename for saving the file to the filesystem
            safe_filename = secure_filename(file.filename)
            safe_filename = secure_filename(file.filename)
            original_filepath = os.path.join(UPLOAD_FOLDER, safe_filename)
            logging.info(f"Attempting to save original file to: {original_filepath}")
            try:
                file.save(original_filepath)
                # Add check immediately after save
                if os.path.exists(original_filepath):
                    logging.info(
                        f"Successfully saved original file: {original_filepath}"
                    )
                else:
                    logging.error(
                        f"Original file not found immediately after saving: {original_filepath}"
                    )
                    continue  # Skip to the next file if original save failed
            except Exception as save_err:
                logging.error(
                    f"Error during file.save for {original_filepath}: {save_err}"
                )
                continue  # Skip to the next file if original save failed

            # Determine the final filename and path for playback
            final_filename = file.filename  # Default to original filename
            final_filepath = original_filepath  # Default to original filepath
            needs_conversion = False

            # Check if conversion is needed (e.g., FLAC to MP3)
            # Use original filename for extension check as secure_filename might change it
            original_extension = os.path.splitext(file.filename)[1].lower()
            if original_extension == ".flac":
                needs_conversion = True
                # Define the new filename and path for the converted file
                # Use the secure filename base to avoid issues, add .mp3 extension
                base_filename = os.path.splitext(safe_filename)[0]
                final_filename = f"{base_filename}.mp3"
                final_filepath = os.path.join(UPLOAD_FOLDER, final_filename)
                logging.info(
                    f"Converting FLAC to MP3: {original_filepath} -> {final_filepath}"
                )

                try:
                    # Load the FLAC file and export as MP3
                    audio = AudioSegment.from_file(original_filepath, format="flac")
                    audio.export(final_filepath, format="mp3")
                    logging.info(
                        f"Successfully converted and saved MP3: {final_filepath}"
                    )
                    # Optionally remove the original FLAC file after successful conversion
                    # os.remove(original_filepath)
                    # logging.info(f"Removed original FLAC file: {original_filepath}")

                except Exception as convert_err:
                    logging.error(
                        f"Error during FLAC to MP3 conversion for {original_filepath}: {convert_err}"
                    )
                    # If conversion fails, maybe still add the original FLAC? Or skip?
                    # For now, let's skip this file if conversion fails.
                    continue  # Skip to the next file

            # URL encode the *final* filename for the URL generation/response path
            encoded_final_filename = urllib.parse.quote(final_filename)
            results.append(
                {
                    "status": "success",
                    "filename": file.filename,  # Send original filename back for display
                    "path": f"/static/uploads/{encoded_final_filename}",  # Use encoded *final* for path
                    # The URL should point to the *final* file using its encoded name
                    "url": url_for(
                        "main.uploaded_file",
                        filename=encoded_final_filename,
                        _external=True,
                    ),
                    "original_filename": file.filename,  # Store original filename
                    "saved_filename": safe_filename,  # Store secure filename
                    "converted_to": (
                        "mp3" if needs_conversion else None
                    ),  # Indicate if converted
                }
            )
    return jsonify({"status": "success", "files": results})


@bp.route("/api/metadata", methods=["GET"])
def get_file_metadata() -> Response | Tuple[Response, int]:
    """Get metadata for a file using direct filesystem access."""

    # Configure root logger to ensure debug messages are shown
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    for handler in root_logger.handlers:
        handler.setLevel(logging.DEBUG)

    filename_encoded = request.args.get("filename")
    if not filename_encoded:
        return jsonify({"error": "Missing filename parameter"}), 400

    try:
        # Decode the filename received from the query parameter to get the original name
        filename_decoded = urllib.parse.unquote(filename_encoded)
        # Apply secure_filename to the decoded name to get the name used on the filesystem
        filename_secure = secure_filename(filename_decoded)
        filepath = os.path.join(UPLOAD_FOLDER, filename_secure)

        logging.debug(f"Received encoded filename: {filename_encoded}")
        logging.debug(f"Decoded original filename: {filename_decoded}")
        logging.debug(f"Secure filename for filesystem: {filename_secure}")
        logging.debug(f"Constructed filepath for existence check: {filepath}")
        logging.debug(f"Checking existence of: {filepath}")

        if not os.path.exists(filepath):
            logging.error(f"File not found at: {filepath}")
            # List directory contents for debugging
            try:
                dir_contents = os.listdir(UPLOAD_FOLDER)
                logging.debug(f"Contents of {UPLOAD_FOLDER}: {dir_contents}")
            except Exception as list_err:
                logging.error(f"Could not list directory {UPLOAD_FOLDER}: {list_err}")
            return jsonify({"error": "File not found"}), 404
        else:
            logging.debug(f"File confirmed to exist at: {filepath}")

        # Default values
        metadata = {
            "filename": filename_decoded,  # Use decoded filename
            "path": f"/static/uploads/{filename_encoded}",  # Use encoded filename for path
            "size": os.path.getsize(filepath),
            "type": mimetypes.guess_type(filepath)[0] or "application/octet-stream",
            "title": os.path.splitext(filename_decoded)[0],  # Fallback title
            "artist": "Unknown Artist",
            "album": "Unknown Album",
            "duration": 0,
            "album_art": url_for(
                "static", filename="img/default-album.png"
            ),  # Default art
        }

        try:
            # Use Mutagen with the direct filepath
            audio = MutagenFile(filepath, easy=True)
            if audio:
                # Extract basic tags if available
                metadata["title"] = str(audio.get("title", [metadata["title"]])[0])
                metadata["artist"] = str(audio.get("artist", [metadata["artist"]])[0])
                metadata["album"] = str(audio.get("album", [metadata["album"]])[0])

                # Try multiple tag formats if still unknown
                if metadata["artist"] == "Unknown Artist":
                    logging.debug(f"Checking extended tags for {filename_decoded}")
                    checked_tags = [
                        "TPE1",
                        "ARTIST",
                        "TPE2",
                        "ALBUMARTIST",
                        "TPE3",
                        "©ART",
                        "PERFORMER",
                        "BAND",
                        "ORCHESTRA",
                        "COMPOSER",
                    ]
                    for tag in checked_tags:
                        if audio.get(tag):
                            metadata["artist"] = str(audio[tag][0])
                            logging.debug(
                                f"Using artist from {tag} tag: {metadata['artist']}"
                            )
                            break
                    else:
                        metadata["artist"] = "Unknown Artist"

                if metadata["title"] == os.path.splitext(filename_decoded)[0]:
                    for tag in ["TIT2", "©nam", "TITLE"]:
                        if audio.get(tag):
                            metadata["title"] = str(audio[tag][0])
                            break

                if metadata["artist"] == "Unknown Artist" and audio.get("TPE2"):
                    metadata["artist"] = str(audio["TPE2"][0])

                if audio.info and hasattr(audio.info, "length"):
                    metadata["duration"] = round(audio.info.length)

        except MutagenError as e:
            logging.error(f"Mutagen error reading {filename_decoded}: {e}")
        except Exception as e:
            logging.error(f"Error processing metadata for {filename_decoded}: {e}")

        # Fallback filename parsing (remains the same)
        filename_no_ext = os.path.splitext(filename_decoded)[0]
        original_title = os.path.splitext(filename_decoded)[0]

        if "_-_" in filename_no_ext and filename_no_ext.count("_-_") >= 2:
            parts = filename_no_ext.rsplit("_-_", 2)
            if len(parts) == 3:
                metadata["artist"] = parts[0].replace("_", " ").strip()
                track_match = re.search(r"_(\d{2,3})(?:_|$)", parts[1])
                if track_match:
                    title_part = parts[1].split(track_match.group(0), 1)[-1]
                    metadata["title"] = title_part.replace("_", " ").strip()
                    metadata["track"] = int(track_match.group(1))
                else:
                    metadata["title"] = parts[1].replace("_", " ").strip()
                return jsonify(metadata)

        if " - " in filename_no_ext:
            parts = filename_no_ext.split(" - ", 1)
            if len(parts) == 2:
                if metadata["artist"] == "Unknown Artist":
                    metadata["artist"] = parts[0].replace("_", " ").strip()
                if metadata["title"] == original_title:
                    metadata["title"] = parts[1].replace("_", " ").strip()
                if metadata["artist"] != "Unknown Artist":
                    return jsonify(metadata)

        if "_" in filename_no_ext:
            parts = filename_no_ext.split("_", 2)
            if len(parts) >= 2:
                if any(c.isalpha() for c in parts[0]):
                    if metadata["artist"] == "Unknown Artist":
                        metadata["artist"] = parts[0].strip()
                    if metadata["title"] == original_title and len(parts) > 1:
                        metadata["title"] = " ".join(parts[1:]).strip()
            if len(parts) == 2:
                if metadata["artist"] == "Unknown Artist":
                    metadata["artist"] = parts[0].strip()
                if metadata["title"] == original_title:
                    metadata["title"] = parts[1].strip()

        if metadata["title"] == original_title:
            track_num_patterns = [
                (r"^(\d{2,3})\s(.+)$", " "),
                (r"^Track\s?(\d+)\s(.+)$", " "),
                (r"^(\d{2,3})-(.+)$", "-"),
            ]
            for pattern, sep in track_num_patterns:
                match = re.match(pattern, filename_no_ext)
                if match:
                    metadata["title"] = match.group(2).strip()
                    break

        logging.debug("\n=== Metadata Extraction Report ===")
        logging.debug(f"File: {filename_decoded}")
        logging.debug(
            f"Mutagen tags found: {audio.tags if audio and audio.tags else 'No audio tags'}"
        )
        logging.debug(f"Initial filename parse: {filename_no_ext}")
        logging.debug(f"Final metadata: {metadata}")
        logging.debug(
            f"Artist detection: {'Success' if metadata['artist'] != 'Unknown Artist' else 'Failed'}"
        )
        logging.debug(
            f"Title detection: {'Success' if metadata['title'] != original_title else 'Failed'}"
        )
        logging.debug("==================================\n")

        return jsonify(metadata)

    except Exception as e:
        logging.error(f"Outer error getting metadata for {filename_decoded}: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/api/metadata/fetch", methods=["GET"])
def get_metadata() -> Response:
    """Fetch metadata for a track."""
    artist: Optional[str] = request.args.get("artist")
    title = request.args.get("title")
    album = request.args.get("album")

    import asyncio

    metadata = asyncio.run(fetch_metadata(artist=artist, title=title, album=album))
    return jsonify(metadata)


# --- Lyrics Fetching ---


@bp.route("/api/delete", methods=["DELETE"])
def delete_file() -> Response | Tuple[Response, int]:
    """Delete an uploaded file."""
    path = request.args.get("path")
    if not path:
        return jsonify({"error": "Missing path parameter"}), 400

    try:
        # Decode filename from path before using it
        filename_encoded = os.path.basename(path)
        filename_decoded = urllib.parse.unquote(filename_encoded)
        filepath = os.path.join(UPLOAD_FOLDER, filename_decoded)

        if not os.path.exists(filepath):
            logging.error(f"Delete failed: File not found at {filepath}")
            return jsonify({"error": "File not found"}), 404

        os.remove(filepath)
        logging.info(f"Deleted file: {filepath}")
        return jsonify(
            {"status": "success", "filename": filename_decoded}
        )  # Return decoded

    except Exception as e:
        logging.error(f"Error deleting file {path}: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/api/clear_uploads", methods=["POST"])
def clear_uploads() -> Response | Tuple[Response, int]:
    """Delete all files in the uploads directory."""
    import logging

    logging.info(f"Attempting to clear uploads directory: {UPLOAD_FOLDER}")
    try:
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                os.remove(filepath)
                logging.info(f"Deleted file: {filepath}")
        logging.info("Uploads directory cleared successfully.")
        return jsonify({"status": "success", "message": "Uploads directory cleared"})
    except Exception as e:
        logging.error(f"Error clearing uploads directory: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/api/lyrics", methods=["GET"])
def get_lyrics() -> Response | Tuple[Response, int]:
    """Fetch lyrics for a track with multiple fallback sources."""
    artist = request.args.get("artist", "").strip()
    title = request.args.get("title", "").strip()

    if not title or artist == "Unknown Artist":
        return jsonify({"lyrics": "No lyrics available for unknown artist"}), 200

    # Try local cache first
    try:
        from .metadata.lyrics_cache import get_cached_lyrics

        cached = get_cached_lyrics(artist, title)
        if cached:
            return jsonify({"lyrics": cached})
    except ImportError:
        pass  # Cache might not be implemented

    # Try Lyrics.ovh as primary source
    try:
        url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            lyrics = data.get("lyrics")
            if lyrics:
                try:
                    from .metadata.lyrics_cache import cache_lyrics

                    cache_lyrics(artist, title, lyrics)
                except ImportError:
                    pass  # Cache might not be implemented
                return jsonify({"lyrics": lyrics})
    except requests.exceptions.RequestException as e:
        logging.warning(f"Lyrics.ovh request failed: {e}")

    # Try local file parsing as fallback
    try:
        from .metadata.local_lyrics import parse_local_lyrics

        local_lyrics = parse_local_lyrics(artist, title)
        if local_lyrics:
            return jsonify({"lyrics": local_lyrics})
    except ImportError:
        pass  # Local lyrics might not be implemented

    return jsonify({"lyrics": "No lyrics found"}), 404
