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
sudo docker build -f Dockerfile -t speech_to_text_bot . # => Docker Build
```

```bash
sudo docker run -d --restart unless-stopped -e TOKEN=YOUR-TOKEN -e SERVER_HOST=YOUR-HOST -e SERVER_HOST=YOUR-PORT -v /{full path to project}/logs/:/app/logs/ speech_to_text_bot # => Docker Run
```

## Docker-Compose
```bash
docker-compose up
````