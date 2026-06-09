import sys
import os

# Add project root to Python path so Flask app and its modules can be imported
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Vercel expects a module-level `app` variable that is a WSGI callable
from app import app
