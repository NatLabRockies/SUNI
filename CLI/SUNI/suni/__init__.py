from pathlib import Path
import importlib.metadata

REPO_DIR = Path(__file__).parent

__version__ = version = importlib.metadata.version("NLR-SUNI")
