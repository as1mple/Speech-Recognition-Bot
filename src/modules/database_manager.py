import base64

import requests


def save_to_database(
    host: str,
    port: str,
    name_collection: str,
    chat_id: str,
    utcnow: str,
    text: str,
    language: str,
    speech_bytes: str,
    description: str,
) -> requests.Response:
    """Save to database."""

    response = requests.post(
        f"http://{host}:{port}/add/data",
        json={
            "name_collection": name_collection,
            "user_id": chat_id,
            "text": text,
            "description": description,
            "speech_bytes": base64.b64encode(speech_bytes).decode(),  # type: ignore[arg-type]
            "language": language,
            "timestamp": utcnow,
        },
    )
    return response


def get_save_data(
    host: str, port: str, name_collection: str, time_from: str, time_to: str
) -> dict:
    """Get data from database."""
    params = {
        "name_collection": name_collection,
        "time_from": time_from,
        "time_to": time_to,
    }
    return requests.get(f"http://{host}:{port}/get/data", params=params).json()


def get_files_by_chat_id(host: str, port: str, name_collection: str, chat_id: str) -> dict:
    """Get files by chat id."""
    params = {
        "name_collection": name_collection,
        "user_id": chat_id,
    }
    return requests.get(f"http://{host}:{port}/get/data", params=params).json()
