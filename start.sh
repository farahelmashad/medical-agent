#!/bin/bash


if [ -n "$GOOGLE_CREDENTIALS_B64" ]; then
    echo "$GOOGLE_CREDENTIALS_B64" | base64 -d > /app/credentials.json
else
    echo "WARNING: GOOGLE_CREDENTIALS_B64 not set"
fi

if [ -n "$GMAIL_TOKEN_B64" ]; then
    echo "$GMAIL_TOKEN_B64" | base64 -d > /app/token.json
else
    echo "WARNING: GMAIL_TOKEN_B64 not set"
fi

uvicorn main:app --host 0.0.0.0 --port 8000 &

sleep 5

streamlit run frontend.py \
    --server.port 7860 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.fileWatcherType none
