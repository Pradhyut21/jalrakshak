"""A real local HTTP receiver distinguishes acceptance from failed delivery."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import httpx
import pytest

from backend.app.notifiers import WebhookNotifier


def test_local_receiver_observes_payload_and_failure_raises():
    received = []

    class Receiver(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.path == "/fail":
                self.send_response(503)
            else:
                received.append(payload)
                self.send_response(202)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        result = WebhookNotifier(base + "/notice").send({"message": "SIMULATED test notice"})
        assert result["status"] == "ENDPOINT_ACCEPTED"
        assert received == [{"message": "SIMULATED test notice"}]
        with pytest.raises(httpx.HTTPStatusError):
            WebhookNotifier(base + "/fail").send({"message": "must fail"})
        assert len(received) == 1
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()
