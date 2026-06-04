#!/bin/bash
mkdir -p /app/data
gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 app:app
