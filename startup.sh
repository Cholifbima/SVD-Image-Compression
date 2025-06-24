#!/bin/bash

echo "🚀 Starting SVD Image Compression App"
echo "Current directory: $(pwd)"
echo "Python path: $PYTHONPATH"

# Change to app directory first
cd /home/site/wwwroot/src/app
echo "Changed to directory: $(pwd)"

# Set Python path to include our source
export PYTHONPATH="/home/site/wwwroot/src:$PYTHONPATH"
echo "Python path set to: $PYTHONPATH"

# Create necessary directories
mkdir -p /tmp/svd_uploads /tmp/svd_cache
echo "Created upload directories"

# Set Flask environment
export FLASK_APP=app.py
export FLASK_ENV=production

# Test imports before starting
python -c "import sys; sys.path.append('..'); from svd import compress_image; from utils import allowed_file; print('✅ Imports successful')" || exit 1

# Start with verbose logging
echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --timeout 600 --workers 1 --access-logfile - --error-logfile - --log-level info app:app 