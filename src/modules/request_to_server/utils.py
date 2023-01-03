import base64
import requests


def save_to_database(
    host: str, port: str, chat_id: str, utcnow: str, text: str, language: str, speech_bytes: str, description: str
):
    """Save to database."""
    json_data = {
        "user_id": chat_id,
        "text": text,
        "description": description,
        "speech_bytes": base64.b64encode(speech_bytes).decode(),
        "language": language,
        "timestamp": utcnow,
    }

    response = requests.post(f"http://{host}:{port}/add/data", json=json_data)
    return response
