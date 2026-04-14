#!/bin/bash

echo "==> Decoding secrets..."

if [ -n "$GOOGLE_CREDENTIALS_B64" ]; then
    echo "$GOOGLE_CREDENTIALS_B64" | base64 -d > /app/credentials.json
    echo "==> credentials.json written"
else
    echo "WARNING: GOOGLE_CREDENTIALS_B64 not set"
fi

if [ -n "$GMAIL_TOKEN_B64" ]; then
    echo "$GMAIL_TOKEN_B64" | base64 -d > /app/token.json
    echo "==> token.json written"
else
    echo "WARNING: GMAIL_TOKEN_B64 not set"
fi

echo "==> Starting FastAPI backend on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 &

echo "==> Waiting for backend to be ready..."
sleep 5

echo "==> Starting Streamlit frontend on port 7860..."
streamlit run frontend.py \
    --server.port 7860 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.fileWatcherType none