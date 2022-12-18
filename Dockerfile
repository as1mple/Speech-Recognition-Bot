FROM python:3.8

COPY requirements.txt ./requirements.txt

RUN python -m pip install -U pip && \
    python -m pip install -r requirements.txt && \
    python -m pip cache purge

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

COPY ./ /app/
WORKDIR /app/

CMD python src/bot.py
