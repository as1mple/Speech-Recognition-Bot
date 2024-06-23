#!/bin/bash

cd Speech-Recognition-Bot/
sudo docker build -f Dockerfile -t bot_speech_to_text_image . # => Docker Build
sudo docker run -it -d --env-file .env --restart unless-stopped  -v /Projects/Speech-Recognition-Bot/logs/:/app/logs --name bot_speech_to_text bot_speech_to_text_image  # => Docker Run