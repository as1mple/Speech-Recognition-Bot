import requests


def save_to_database(
    host: str, port: str, chat_id: str, utcnow: str, text: str, speech_bytes: str
):
    """Save to database."""
    json_data = {
        "user_id": chat_id,
        "text": text,
        "speech_bytes": speech_bytes.decode("ISO-8859-1"),
        "timestamp": utcnow,
    }

    response = requests.post(f"http://{host}:{port}/add/data", json=json_data)
    return response
