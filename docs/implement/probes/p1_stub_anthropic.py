#!/usr/bin/env python3
"""A minimal Anthropic Messages API stub, so P1 can complete a run without a provider key.

Answers  — nothing. It is not a check. It stands in for the one hop in P1 that
           needs a credential, so that every other hop — dispatch, checkpointing,
           the deepagents middleware chain, the run lifecycle — is exercised for
           real against Postgres rather than mocked.

Does not — model anything. It replies "OK" to every request, ignores the prompt,
           the tools and the system message, and reports one input token. A run
           that completes against this stub proves the *path* works. It proves
           nothing whatever about what a real model would do, and P1's recorded
           result says so in those words.

Refuses  — nothing, which is why it binds 127.0.0.1 only. It accepts any API key.

Speaks both shapes `langchain-anthropic` uses: a JSON body, and the SSE event
sequence when the request carries `"stream": true`. Point a client at it with
`ANTHROPIC_BASE_URL=http://127.0.0.1:8787` and any non-empty `ANTHROPIC_API_KEY`.

Nothing checks this file. It is outside the traceability perimeter (`src/**`,
`services/**`, `apps/**`) and has no tests.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

REPLY = "OK"

# The Anthropic streaming sequence, in order. `message_start` carries the model
# back so the caller's response metadata shows what it asked for.
_SSE = [
    ("message_start", {"type": "message_start", "message": {
        "id": "msg_stub", "type": "message", "role": "assistant", "model": "stub",
        "content": [], "stop_reason": None, "stop_sequence": None,
        "usage": {"input_tokens": 1, "output_tokens": 0}}}),
    ("content_block_start", {"type": "content_block_start", "index": 0,
                             "content_block": {"type": "text", "text": ""}}),
    ("content_block_delta", {"type": "content_block_delta", "index": 0,
                             "delta": {"type": "text_delta", "text": REPLY}}),
    ("content_block_stop", {"type": "content_block_stop", "index": 0}),
    ("message_delta", {"type": "message_delta",
                       "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                       "usage": {"output_tokens": 1}}),
    ("message_stop", {"type": "message_stop"}),
]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("stub %s - %s\n" % (self.path, fmt % args))

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        model = body.get("model", "stub")

        if body.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            for name, payload in _SSE:
                if name == "message_start":
                    payload["message"]["model"] = model
                self.wfile.write(f"event: {name}\ndata: {json.dumps(payload)}\n\n".encode())
                self.wfile.flush()
            self.close_connection = True
            return

        payload = json.dumps({
            "id": "msg_stub", "type": "message", "role": "assistant", "model": model,
            "content": [{"type": "text", "text": REPLY}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
