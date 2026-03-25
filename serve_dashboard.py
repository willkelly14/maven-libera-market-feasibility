#!/usr/bin/env python3
"""
Serves the dashboard with a local HTTP server that supports
saving changes back to disk via API endpoints.

Usage:
    .venv/bin/python serve_dashboard.py
    # Opens http://localhost:8050 in your browser
"""

import json
import os
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    print("PyYAML not found. Run: .venv/bin/pip install pyyaml")
    sys.exit(1)

import build_dashboard

BASE_DIR = build_dashboard.BASE_DIR
CONTEXT_DIR = build_dashboard.CONTEXT_DIR
DOCS_DIR = build_dashboard.DOCS_DIR
FACT_DB_DIR = build_dashboard.FACT_DB_DIR
CONSULT_DIR = build_dashboard.CONSULT_DIR
PORT = 8050


class DashboardHandler(SimpleHTTPRequestHandler):
    """Serves dashboard.html and handles save API calls."""

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/dashboard.html"):
            # Rebuild dashboard fresh on each load so saves are reflected
            build_dashboard.main()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(build_dashboard.OUTPUT_FILE, "rb") as f:
                self.wfile.write(f.read())
        else:
            super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
            return

        handlers = {
            "/api/save-context": self._save_context,
            "/api/save-claude": self._save_claude,
            "/api/save-doc-status": self._save_doc_status,
            "/api/save-fact-status": self._save_fact_status,
            "/api/create-context": self._create_context,
            "/api/delete-context": self._delete_context,
            "/api/rename-context": self._rename_context,
        }

        handler = handlers.get(path)
        if handler:
            handler(data)
        else:
            self._respond(404, {"error": "Unknown endpoint"})

    def _respond(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

    def _save_context(self, data):
        filename = data.get("filename", "")
        content = data.get("content", "")
        if not filename:
            self._respond(400, {"error": "Missing filename"})
            return
        # Sanitize filename
        safe_name = os.path.basename(filename)
        filepath = os.path.join(CONTEXT_DIR, safe_name)
        os.makedirs(CONTEXT_DIR, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Saved context file: {safe_name}")
        self._respond(200, {"ok": True})

    def _create_context(self, data):
        filename = data.get("filename", "")
        content = data.get("content", "")
        if not filename:
            self._respond(400, {"error": "Missing filename"})
            return
        safe_name = os.path.basename(filename)
        if not safe_name.endswith(".md"):
            safe_name += ".md"
        filepath = os.path.join(CONTEXT_DIR, safe_name)
        os.makedirs(CONTEXT_DIR, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Created context file: {safe_name}")
        self._respond(200, {"ok": True, "filename": safe_name})

    def _delete_context(self, data):
        filename = data.get("filename", "")
        if not filename:
            self._respond(400, {"error": "Missing filename"})
            return
        safe_name = os.path.basename(filename)
        filepath = os.path.join(CONTEXT_DIR, safe_name)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"  Deleted context file: {safe_name}")
        self._respond(200, {"ok": True})

    def _rename_context(self, data):
        old_filename = data.get("old_filename", "")
        new_filename = data.get("new_filename", "")
        if not old_filename or not new_filename:
            self._respond(400, {"error": "Missing old_filename or new_filename"})
            return
        old_safe = os.path.basename(old_filename)
        new_safe = os.path.basename(new_filename)
        if not new_safe.endswith(".md"):
            new_safe += ".md"
        old_path = os.path.join(CONTEXT_DIR, old_safe)
        new_path = os.path.join(CONTEXT_DIR, new_safe)
        if not os.path.exists(old_path):
            self._respond(404, {"error": f"File {old_safe} not found"})
            return
        if os.path.exists(new_path):
            self._respond(409, {"error": f"File {new_safe} already exists"})
            return
        os.rename(old_path, new_path)
        print(f"  Renamed context file: {old_safe} → {new_safe}")
        self._respond(200, {"ok": True, "filename": new_safe})

    def _save_claude(self, data):
        content = data.get("content", "")
        claude_path = os.path.join(BASE_DIR, "CLAUDE.md")
        with open(claude_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("  Saved CLAUDE.md")
        self._respond(200, {"ok": True})

    def _save_doc_status(self, data):
        doc_id = data.get("id", "")
        new_status = data.get("status", "")
        if not doc_id or not new_status:
            self._respond(400, {"error": "Missing id or status"})
            return

        index_path = os.path.join(DOCS_DIR, "documents_index.yaml")
        if not os.path.exists(index_path):
            self._respond(404, {"error": "documents_index.yaml not found"})
            return

        with open(index_path, "r", encoding="utf-8") as f:
            docs = yaml.safe_load(f.read())

        if not docs or not isinstance(docs, list):
            self._respond(500, {"error": "Invalid documents index"})
            return

        found = False
        for doc in docs:
            if isinstance(doc, dict) and doc.get("id") == doc_id:
                doc["status"] = new_status
                found = True
                break

        if not found:
            self._respond(404, {"error": f"Document {doc_id} not found"})
            return

        with open(index_path, "w", encoding="utf-8") as f:
            yaml.dump(docs, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"  Saved doc status: {doc_id} → {new_status}")
        self._respond(200, {"ok": True})

    def _save_fact_status(self, data):
        fact_id = data.get("id", "")
        new_status = data.get("status", "")
        fact_file = data.get("file", "")
        if not fact_id or not new_status or not fact_file:
            self._respond(400, {"error": "Missing id, status, or file"})
            return

        safe_file = os.path.basename(fact_file)
        filepath = os.path.join(FACT_DB_DIR, safe_file)
        if not os.path.exists(filepath):
            self._respond(404, {"error": f"Fact file {safe_file} not found"})
            return

        with open(filepath, "r", encoding="utf-8") as f:
            facts = yaml.safe_load(f.read())

        if not facts or not isinstance(facts, list):
            self._respond(500, {"error": "Invalid fact file"})
            return

        found = False
        for fact in facts:
            if isinstance(fact, dict) and fact.get("id") == fact_id:
                fact["verification_status"] = new_status
                fact["verified"] = (new_status == "verified")
                found = True
                break

        if not found:
            self._respond(404, {"error": f"Fact {fact_id} not found in {safe_file}"})
            return

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(facts, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"  Saved fact status: {fact_id} → {new_status}")
        self._respond(200, {"ok": True})

    def log_message(self, format, *args):
        # Only log API calls, not static file requests
        msg = format % args
        if "/api/" in msg:
            print(f"  API: {msg}")


def main():
    # Build the dashboard first
    print("Building dashboard...")
    build_dashboard.main()

    class ReusableHTTPServer(HTTPServer):
        allow_reuse_address = True
    server = ReusableHTTPServer(("localhost", PORT), DashboardHandler)
    url = f"http://localhost:{PORT}"
    print(f"\nDashboard server running at {url}")
    print("Press Ctrl+C to stop.\n")
    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        server.shutdown()


if __name__ == "__main__":
    main()
