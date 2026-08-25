"""
Launcher script for AEGIS-AI — AI Agent Red Team vs Blue Team Payment Security Lab.
Checks environment, initializes database, and launches Uvicorn server.
"""

import os
import sys
import shutil

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_env():
    """Check for .env file and guide the user through setup if needed."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    example_path = os.path.join(os.path.dirname(__file__), ".env.example")

    if not os.path.exists(env_path):
        print("\n" + "=" * 64)
        print("  ⚠️  No .env file found!")
        print("=" * 64)

        if os.path.exists(example_path):
            shutil.copy(example_path, env_path)
            print(f"  Created .env from .env.example")
        else:
            print(f"  Please create a .env file. See .env.example for template.")

        print()
        print("  To get started, you need:")
        print("  1. An OpenRouter API key → https://openrouter.ai/keys")
        print("  2. PostgreSQL running (optional, defaults to SQLite) → docker compose up -d")
        print()
        print("  Add your OPENROUTER_API_KEY to .env, then restart the server.")
        print("=" * 64 + "\n")

    from dotenv import load_dotenv
    load_dotenv(env_path)

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        print("\n  ⚠️  OPENROUTER_API_KEY is empty in .env")
        print("  Get one at: https://openrouter.ai/keys")
        print("  The server will start but attacks will fail.\n")


def main():
    import uvicorn
    from backend.app import app

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    print()
    print("=" * 64)
    print("  AEGIS-AI // AI AGENT RED TEAM vs BLUE TEAM SECURITY LAB")
    print("=" * 64)
    print(f"  Server: http://{host}:{port}")
    print(f"  API Docs: http://{host}:{port}/docs")
    print(f"  WebSocket: ws://{host}:{port}/ws/stream")
    print("=" * 64)
    print()

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    check_env()
    main()
