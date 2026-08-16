"""Writes the FastAPI app's OpenAPI schema to openapi.json at the repo
root, so the frontend can generate a typed API client (openapi-typescript)
without needing the server running.
"""
import json
from pathlib import Path

from src.api.main import app

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def main() -> None:
    OUTPUT_PATH.write_text(json.dumps(app.openapi(), indent=2))
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
