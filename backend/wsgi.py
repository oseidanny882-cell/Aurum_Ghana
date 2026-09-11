"""
WSGI entry point for production servers
Run with: gunicorn -w 4 -b 0.0.0.0:5000 backend.wsgi:app
"""
from backend.app import create_app

app = create_app()
