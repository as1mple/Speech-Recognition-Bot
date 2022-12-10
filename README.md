# Speech-Recognition-Bot

## Templates

```bash
export TOKEN=YOUR-TOKEN
```

```bash
python src/bot.py
```

## Docker
```bash
sudo docker build -f Dockerfile -t speech_to_text_bot . # => Docker Build
```

```bash
sudo docker run -e TOKEN=YOUR-TOKEN speech_to_text_bot # => Docker Run
```
