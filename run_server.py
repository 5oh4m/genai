"""
Launcher script for AEGIS-AI Adversarial Cyber Defense & Fraud Lab.
Bootstraps dependencies, initializes model state, and launches Uvicorn server.
"""

import sys
import os
import uvicorn

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app, initialize_default_system

if __name__ == "__main__":
    print("================================================================")
    print("       AEGIS-AI // ADVERSARIAL CYBER DEFENSE COMMAND CENTER      ")
    print("================================================================")
    print(" Initializing in-memory simulation engine & Blue Team pipeline...")
    initialize_default_system()
    print(" Server launching on http://127.0.0.1:8000")
    print(" Open http://127.0.0.1:8000 in your browser to access the HUD.")
    print("================================================================")
    uvicorn.run(app, host="127.0.0.1", port=8000)
