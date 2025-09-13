# Set up test environment

## Locally (uvicorn)

"""
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

## Run sur ngrok

run in the cli

"""
ngrok http 8000
"""

then, create an account on ngrok and log your authtoken
ngrok config add-authtoken XXXX