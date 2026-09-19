#!/usr/bin/env python3
"""The host half of P4: a signing sidecar that never yields its key.

P4 asks whether a sandboxed process can get a commit signed by a key it cannot
read. Something has to hold that key and sign on request. `ASM-17` names
`vouch-bridge` for this job; `vouch-bridge` is a C2PA image and audio signing
service and does not sign git objects at all, so this file stands in for the
component that does not exist yet. See the campaign document, P4.

**This is a probe artifact and not a product.** It is the smallest thing that
makes the question answerable. A real sidecar needs at minimum: an audit log
that survives restart, rate limiting, a policy over *what* it agrees to sign
rather than signing any bytes presented, and a key in an HSM or an agent rather
than a file. Do not deploy this.

The contract is deliberately narrow. The sidecar accepts a payload and returns
an SSH signature over it. It never returns the private key, it never reads a
path the caller names, and `GET /pubkey` hands out only the public half.

Stdlib only, so it runs with no virtualenv on the host.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

KEY: Path
TOKEN: str
NAMESPACE = "git"
signed_count = 0


class Handler(BaseHTTPRequestHandler):
    server_version = "p4-sidecar/0"

    def log_message(self, fmt: str, *args) -> None:
        # One line per request, on stderr, so the probe transcript shows every
        # signature this key produced. Accountability is the whole point of
        # moving the key out of the sandbox; a sidecar that signs silently has
        # given the property back.
        sys.stderr.write("sidecar %s - %s\n" % (self.address_string(), fmt % args))

    def _reply(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _authorised(self) -> bool:
        if not TOKEN:
            return True
        got = self.headers.get("Authorization", "")
        return got.startswith("Bearer ") and got[len("Bearer ") :] == TOKEN

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's spelling
        if self.path == "/health":
            self._reply(200, {"status": "ok", "signed": signed_count})
        elif self.path == "/pubkey":
            pub = KEY.with_suffix(KEY.suffix + ".pub") if KEY.suffix else Path(str(KEY) + ".pub")
            self._reply(200, {"pubkey": pub.read_text().strip()})
        else:
            self._reply(404, {"error": "no such endpoint"})

    def do_POST(self) -> None:  # noqa: N802
        global signed_count
        if self.path != "/sign":
            self._reply(404, {"error": "no such endpoint"})
            return
        if not self._authorised():
            self._reply(401, {"error": "bad or missing bearer token"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        try:
            req = json.loads(self.rfile.read(length) or b"{}")
            payload = base64.b64decode(req["payload_b64"])
        except Exception as exc:  # noqa: BLE001 - any malformed body is one answer
            self._reply(400, {"error": f"unreadable request: {exc}"})
            return

        # The namespace is fixed rather than taken from the caller. A caller who
        # can choose it can ask for a signature that verifies in a context the
        # operator never agreed to.
        with tempfile.TemporaryDirectory(prefix="p4sign_") as tmp:
            blob = Path(tmp) / "payload"
            blob.write_bytes(payload)
            proc = subprocess.run(
                ["ssh-keygen", "-Y", "sign", "-n", NAMESPACE, "-f", str(KEY), str(blob)],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                self._reply(500, {"error": f"ssh-keygen failed: {proc.stderr.strip()}"})
                return
            signature = (blob.parent / (blob.name + ".sig")).read_text()

        signed_count += 1
        self._reply(200, {"signature": signature, "bytes": len(payload)})


def main() -> int:
    global KEY, TOKEN
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--key", required=True, help="path to the SSH private key, on the host only")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=21777)
    ap.add_argument("--token", default="", help="bearer token the caller must present")
    args = ap.parse_args()

    KEY = Path(args.key).expanduser().resolve()
    TOKEN = args.token
    if not KEY.is_file():
        print(f"no key at {KEY}", file=sys.stderr)
        return 2

    srv = HTTPServer((args.host, args.port), Handler)
    print(f"p4-sidecar listening on {args.host}:{args.port}, key {KEY}", file=sys.stderr)
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
