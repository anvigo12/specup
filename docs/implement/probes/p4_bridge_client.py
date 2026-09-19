#!/usr/bin/env python3
"""The sandbox half of P4: enough of `ssh-keygen -Y sign` to fool git.

git signs an SSH-format commit by running, literally:

    <gpg.ssh.program> -Y sign -n git -f <user.signingkey> <payload-file>

and then reading `<payload-file>.sig`. That is the whole contract, and it is
why the key never has to be in here: this program accepts the same arguments,
forwards the payload to the sidecar over the one HTTP endpoint the sandbox
policy permits, and writes the signature the sidecar returns.

`-f <key>` is accepted and **ignored**. The sidecar decides which key signs.
A bridge that let the caller name the key would hand the sandbox back the
choice the topology exists to take away from it.

What the sandbox does hold is the bearer token, and that is the honest
reduction rather than a loophole: it is permission to ask for a signature
while the sandbox is running, not possession of the key afterwards. Revoking
it is restarting the sidecar. Compare that with a key file, which is still a
key file tomorrow.

Stdlib only. Reads P4_SIDECAR_URL and P4_SIDECAR_TOKEN from the environment.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request

URL = os.environ.get("P4_SIDECAR_URL", "")
TOKEN = os.environ.get("P4_SIDECAR_TOKEN", "")


def die(msg: str) -> None:
    print(f"p4-bridge-client: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main(argv: list[str]) -> int:
    # Parse the shape git uses. Only signing goes to the sidecar; every other
    # mode is delegated to the real ssh-keygen, because git calls this same
    # program for verification too (-Y find-principals, -Y check-novalidate)
    # and a shim that refuses those reports a bad signature over a signature
    # that is perfectly good.
    if "-Y" not in argv:
        os.execvp("ssh-keygen", ["ssh-keygen", *argv])
    mode = argv[argv.index("-Y") + 1]
    if mode != "sign":
        os.execvp("ssh-keygen", ["ssh-keygen", *argv])
    if not URL:
        die("P4_SIDECAR_URL is unset")

    # The payload is the one positional argument: the last token that is not a
    # flag and is not a flag's value.
    flags_with_values = {"-Y", "-n", "-f", "-I", "-s", "-O"}
    positional: list[str] = []
    skip = False
    for i, tok in enumerate(argv):
        if skip:
            skip = False
            continue
        if tok in flags_with_values:
            skip = True
            continue
        if tok.startswith("-"):
            continue
        positional.append(tok)
    if not positional:
        die(f"no payload file in: {' '.join(argv)}")
    payload_path = positional[-1]

    with open(payload_path, "rb") as fh:
        payload = fh.read()

    body = json.dumps(
        {"namespace": "git", "payload_b64": base64.b64encode(payload).decode()}
    ).encode()
    req = urllib.request.Request(
        URL.rstrip("/") + "/sign",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        die(f"sidecar refused: HTTP {exc.code} {exc.read()[:200]!r}")
    except Exception as exc:  # noqa: BLE001 - the probe wants the reason, whatever it is
        die(f"sidecar unreachable: {exc}")

    signature = out.get("signature")
    if not signature:
        die(f"sidecar returned no signature: {out}")

    with open(payload_path + ".sig", "w") as fh:
        fh.write(signature)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
