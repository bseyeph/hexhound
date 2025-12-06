from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
import multiprocessing
import requests
import sys

from flask import Flask, jsonify, send_from_directory, request

from .. import __version__

BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = BASE_DIR / "ui"
ui_process = None


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

    @app.get("/__shutdown__")
    def shutdown():
        func = request.environ.get("werkzeug.server.shutdown")
        if func is None:
            return jsonify({"error": "Not running with Werkzeug"}), 500
        func()
        return jsonify({"status": "shutting down"})

    return app


def stop_server(port: int = 8765):
    global ui_process

    try:
        requests.get(f"http://127.0.0.1:{port}/__shutdown__")
    except Exception:
        pass

    if ui_process is not None and ui_process.is_alive():
        ui_process.terminate()
        ui_process.join(timeout=1)
        ui_process = None


def run_server_process(port: int = 8765):
    global ui_process

    def target():
        sys.stdout = open("hexhound_ui.log", "a")
        sys.stderr = open("hexhound_ui.log", "a")
        run_server(port)

    ui_process = multiprocessing.Process(target=target, daemon=True)
    ui_process.start()


def run_server(port: int = 8765) -> None:
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app = create_app()
    app.run(host="127.0.0.1", port=port, debug=False)
