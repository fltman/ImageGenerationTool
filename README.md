# Bildvariant Generator

[![Support me on Patreon](https://img.shields.io/badge/Patreon-Support%20my%20work-FF424D?style=flat&logo=patreon&logoColor=white)](https://www.patreon.com/AndersBjarby)

En Flask-webbapp för att ladda upp en eller flera bilder, beskriva en önskad förändring i en prompt och få tillbaka AI-genererade varianter. Bilderna genereras med OpenAI och varianterna skapas parallellt med en trådpool, med löpande progress.

## Funktioner

- Ladda upp en eller flera bilder (PNG/JPG, upp till 50 MB)
- Beskriv förändringen i en textprompt och välj antal varianter
- Parallell generering med `gpt-4.1` och `image_generation`-verktyget
- Progress-spårning per jobb och en resultatsida med nedladdning

## Kom igång

```bash
pip install flask flask-sqlalchemy gunicorn openai psycopg2-binary requests werkzeug email-validator
export OPENAI_API_KEY=sk-...
export SESSION_SECRET=valfri-hemlighet

# Utveckling
python app.py             # startar på http://0.0.0.0:5000

# Produktion
gunicorn main:app
```

## Teknik

Python, Flask, Gunicorn, OpenAI Python SDK. Bootstrap-baserat gränssnitt.
