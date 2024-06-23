# Speech-Recognition-Bot
_ _ _
## Templates


```bash
pip install -r requirements.txt
```

```bash
export TOKEN=TOKEN
export SERVER_HOST=SERVER-HOST
export SERVER_PORT=SERVER-PORT
```

```bash
python src/bot.py
```

## Docker
```bash
sudo docker build -f Dockerfile -t bot_speech_to_text_image . # => Docker Build
```

```bash
sudo docker run -it -d --env-file .env --restart unless-stopped  -v /{full path to project}/logs/:/app/logs/ --name bot_speech_to_text bot_speech_to_text_image # => Docker Run
```

## Docker-Compose
```bash
docker-compose up
````

## Bash
```bash
sh run-bot-recogniton-docker-procss.sh
```

## Pre-commit hooks
```bash
pre-commit run --all-files
```

Alternative way:
```bash
bash pre-commit.sh
```
