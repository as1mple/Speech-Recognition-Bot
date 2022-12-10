import os
import shutil

import logging
from pydub import AudioSegment
from pydub.utils import make_chunks

import speech_recognition as sr


def get_text_with_speech(wav_file_name: str, language) -> str:
    split_dir = "tmp"  # name of a temporary directory
    chunk_length_ms = 58000  # max duration of a split segment of the input .wav file, ms
    pause_threshold = 2.0  # max duration of a pause fragment in the input .wav file, s

    result = ""
    shutil.rmtree(split_dir, ignore_errors=True)
    os.mkdir(split_dir)

    myaudio = AudioSegment.from_file(wav_file_name)

    chunks = make_chunks(myaudio, chunk_length_ms)

    # Export all the individual chunks as wav files
    for i, chunk in enumerate(chunks):
        chunk_name = "tmp/chunk{0}.wav".format(i)
        chunk.export(chunk_name, format="wav")

    # Initialize recognizer class (for recognizing the speech)
    r = sr.Recognizer()
    r.pause_threshold = pause_threshold

    # Setup source directory
    dl = os.listdir(split_dir)
    dl.sort()
    os.chdir(split_dir)

    for f in dl:
        fs = f.split(".")
        if fs[1] == "wav":
            with sr.AudioFile(f) as source:
                audio_text = r.listen(source)
            try:
                text = r.recognize_google(audio_text, language=language, show_all=False)
                result = f"{result} {text}"
            except Exception as e:
                logging.error("Invalid speech.")

    os.chdir("..")
    shutil.rmtree(split_dir)
    return result
