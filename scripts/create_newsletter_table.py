import os, sys
sys.path.insert(0, r"c:/Users/Codewithme/jewelry-gh")
from backend.app import create_app
from backend.extensions import db

app = create_app()
with app.app_context():
    db.create_all()  # safe: only creates tables that do not exist yet
    print("newsletter_subscribers table ensured")
