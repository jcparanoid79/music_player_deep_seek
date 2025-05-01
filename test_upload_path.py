import os

from src.routes import UPLOAD_FOLDER

print(f"Upload folder path: {UPLOAD_FOLDER}")
print(f"Directory exists: {os.path.exists(UPLOAD_FOLDER)}")
print(
    f"Files in directory: {os.listdir(UPLOAD_FOLDER) if os.path.exists(UPLOAD_FOLDER) else 'Directory does not exist'}"
)
