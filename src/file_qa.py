from google.genai import types

from llm import generate

MIME_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "pdf": "application/pdf",
}


def ask_about_file(file_bytes, extension, question):
    mime = MIME_TYPES[extension.lower()]
    return generate([
        types.Part.from_bytes(data=file_bytes, mime_type=mime),
        question,
    ])