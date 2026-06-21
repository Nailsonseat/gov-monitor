import time
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from src.database import init_db, SessionLocal
from src.ingestion.signals import SIGNAL_EXTRACTORS
from src.pipeline.scoring import calculate_confidence
from src.schemas.models import NormalizedMetric
from src.pipeline.synthesizer import generate_llm_intelligence


def run_pipeline():
    # ... (Keep your exact existing run_pipeline logic here) ...
    print("Verifying Database Engine State & Initialization...")
    init_db()
    # ...


# --- THE RENDER HEALTH CHECK DECOY ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pipeline Daemon is Active")


def run_dummy_server():
    # Render dynamically assigns a port via the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"Dummy web server listening on port {port} to satisfy Render health checks...")
    server.serve_forever()
# -------------------------------------


if __name__ == "__main__":
    UPDATE_INTERVAL_SECONDS = 86400

    # Spin off the dummy web server in a background thread
    server_thread = threading.Thread(target=run_dummy_server, daemon=True)
    server_thread.start()

    print("Initiating Continuous Pipeline Daemon...")
    while True:
        try:
            run_pipeline()
        except Exception as e:
            print(f"CRITICAL: Pipeline cycle failed: {e}")

        print(f"Cycle complete. Daemon sleeping for {UPDATE_INTERVAL_SECONDS} seconds...")
        time.sleep(UPDATE_INTERVAL_SECONDS)
