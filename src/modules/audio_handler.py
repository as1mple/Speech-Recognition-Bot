from io import BytesIO

from groq import Groq
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks

from setting import GROQ_API_KEY


class AudioProcessor:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def process_with_google_speech(
        self, wav_obj: bytes, language: str, logger, message, chunk_length_ms=58000, pause_threshold=2.0
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
            try:
                text = r.recognize_google(audio_text, language=language, show_all=False)
                result = f"{result} {text}"
            except Exception as e:
                logger.error(f"User [{message.chat.id}] => Invalid speech. {str(e)}")

        return result

    def process_with_whisper(self, wav_obj: bytes) -> str:
        transcription = self.client.audio.transcriptions.create(
            file=("tmp.wav", wav_obj),
            model="whisper-large-v3",
        )
        return transcription.text


