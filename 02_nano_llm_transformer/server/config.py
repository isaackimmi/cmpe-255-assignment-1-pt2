"""Application settings and import boundary."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

API_TITLE = "Nano LLM Evidence API"
API_VERSION = "1.1.0"
ALLOWED_ORIGINS = ["http://127.0.0.1:5175", "http://localhost:5175"]
