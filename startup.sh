#!/bin/bash

echo "🚀 Starting SVD Image Compression App"

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=production
export PYTHONPATH="/home/site/wwwroot/src:$PYTHONPATH"

# Change to app directory
cd /home/site/wwwroot/src/app

# Create necessary directories
mkdir -p uploads cache

# Start the application with gunicorn
exec gunicorn --bind 0.0.0.0:8000 --timeout 600 --workers 1 --access-logfile - --error-logfile - app:app 