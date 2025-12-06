from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask, jsonify, send_from_directory

from .. import __version__

BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = BASE_DIR / "ui"


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(UI_DIR),
        static_url_path="/",
    )

    @app.get("/api/health")
    def health() -> Any:
        return jsonify({"status": "ok", "version": __version__})

    @app.get("/api/graph")
    def graph() -> Any:
        return jsonify({"nodes": [], "edges": []})

    @app.get("/")
    def index():
        index_path = UI_DIR / "index.html"
        if not index_path.exists():
            return (
                "<h1>HexHound UI not built</h1>"
                "<p>Run 'npm run build' in ui/ and copy the dist output into hexhound/ui/.</p>",
                500,
            )
        return send_from_directory(UI_DIR, "index.html")

    @app.get("/<path:path>")
    def static_proxy(path: str):
        target = UI_DIR / path
        if target.exists():
            return send_from_directory(UI_DIR, path)
        return send_from_directory(UI_DIR, "index.html")

    return app


def run_server(port: int = 8765) -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=port, debug=False)
