# Set up test environment

## Locally (uvicorn)

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

## Docker container

cd /Users/nikitadmitrieff/Desktop/Projects/hackathon/mcp-mistral-hackathon
docker build -t fastapi-app .
docker run --rm -p 8000:8000 fastapi-app