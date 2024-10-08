import os

SERVER_HOST: str = os.getenv("SERVER_HOST", "localhost")
SERVER_PORT: str = os.getenv("SERVER_PORT", "8000")

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MAX_CAPTION_LENGTH = 1024
