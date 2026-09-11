"""Run the Flask app on a chosen port (used for clean restarts)."""
import sys, os
sys.path.insert(0, r"c:/Users/Codewithme/jewelry-gh")
os.environ["PYTHONPATH"] = r"c:/Users/Codewithme/jewelry-gh"
os.chdir(r"c:/Users/Codewithme/jewelry-gh")
port = int(os.environ.get("PORT", "5000"))
from backend.app import create_app
app = create_app()
app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
