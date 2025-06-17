import os

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename: str) -> bool:
    """Return True if filename has an allowed image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS 