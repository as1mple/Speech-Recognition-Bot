FROM python:3.8

RUN apt-get update && \
    apt-get install ffmpeg libsm6 libxext6  -y && \
    apt-get clean

COPY requirements.txt ./requirements.txt

RUN python -m pip install -U pip && \
    python -m pip install -r requirements.txt && \
    python -m pip cache purge

COPY ./ /app/
WORKDIR /app/

CMD python src/bot.py
