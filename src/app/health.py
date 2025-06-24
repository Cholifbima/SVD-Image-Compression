"""
Health check endpoint for Azure App Service monitoring
"""
from flask import Blueprint, jsonify
import os
import sys

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Basic health check endpoint for Azure monitoring"""
    try:
        # Check if required modules can be imported
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from svd import compress_image
        from utils import allowed_file
        
        # Check if upload directories exist or can be created
        upload_folder = os.environ.get('UPLOAD_FOLDER', '/tmp/svd_uploads')
        cache_folder = os.environ.get('CACHE_FOLDER', '/tmp/svd_cache')
        
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(cache_folder, exist_ok=True)
        
        return jsonify({
            'status': 'healthy',
            'message': 'SVD Image Compression Service is running',
            'checks': {
                'imports': 'OK',
                'directories': 'OK',
                'upload_folder': upload_folder,
                'cache_folder': cache_folder
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': f'Health check failed: {str(e)}',
            'error': str(e)
        }), 500

@health_bp.route('/ready')
def readiness_check():
    """Readiness check for Azure load balancer"""
    return jsonify({
        'status': 'ready',
        'message': 'Service is ready to accept requests'
    }), 200 