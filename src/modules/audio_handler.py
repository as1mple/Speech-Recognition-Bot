from io import BytesIO

import telebot
from groq import Groq
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks

from setting import GROQ_API_KEY


class AudioProcessor:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def process_with_google_speech(
        self, wav_obj: bytes, language: str, message: telebot.types.Message, chunk_length_ms: int = 58000, pause_threshold: float = 2.0
    ) -> str:
        myaudio = AudioSegment.from_file(wav_obj)
        chunks = make_chunks(myaudio, chunk_length_ms)

        # Initialize recognizer class (for recognizing the speech)
        r = sr.Recognizer()
        r.pause_threshold = pause_threshold

        result = ""
        for chunk in chunks:
            wav_chunk = BytesIO()
            chunk.export(wav_chunk, format="wav")
            with sr.AudioFile(wav_chunk) as source:
                audio_text = r.listen(source)
            text = r.recognize_google(audio_text, language=language, show_all=False)
            result = f"{result} {text}"

        return result

    def process_with_whisper(self, wav_obj: BytesIO) -> str:
        transcription = self.client.audio.transcriptions.create(
            file=("tmp.wav", wav_obj),
            model="whisper-large-v3",
        )
        return transcription.text


