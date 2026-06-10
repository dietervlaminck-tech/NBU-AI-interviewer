import sys
import os

# Ensure this directory is on the path for sibling module imports
_api_dir = os.path.dirname(os.path.abspath(__file__))
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

from app import app
