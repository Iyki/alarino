import sys
import os

# Add the parent of the current script (the repo root) to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main")))
import main
