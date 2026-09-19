#!/usr/bin/env bash
# P4 — ASM-17. Can a sandboxed process get a commit signed by a key it cannot read?
#
# Falsified when the private key has to enter the sandbox, or when the sidecar cannot be reached
# from inside under a policy that denies reading the key.
#
# READ THIS BEFORE TRUSTING THE EXIT CODE. The assumption names `vouch-bridge` as the sidecar.
# `vouch-bridge` is real -- it ships as a console script in `vouch-protocol` -- but it is a C2PA
# image and audio signing service whose own FastAPI description is "C2PA image signing, QR badge
# overlay, and audio watermarking service", and it mints an ephemeral certificate chain per
# request. It does not sign git objects and it holds no long-lived key. So this probe supplies
# its own sidecar (p4_sidecar.py) and its own git-side shim (p4_bridge_client.py). What it
# answers is whether the TOPOLOGY holds on this substrate. It does not answer whether any
# shipped component implements it, and the answer to that today is no.
#
# The assumption also says "a local socket". An OpenShell sandbox is a container and
# `openshell sandbox create` has no mount or volume flag, so a host unix socket is not in the
# sandbox's filesystem at all. Egress is a transparent L7 proxy. The sidecar therefore has to be
# an HTTP endpoint on an address the proxy can route to, and step 6 shows the unix socket is
# absent rather than merely denied.
#
# Exit codes: 0 the topology held completely, 1 falsified, 2 setup fault.

set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
SPIKE="${SPIKE:-$ROOT/workspace/spike-0.1.3/P4}"
IMAGE="${IMAGE:-p4-signing-sandbox:latest}"
BASE="${BASE:-ghcr.io/nvidia/openshell-community/sandboxes/base:latest}"
OPENSHELL="${OPENSHELL:-openshell}"
PORT="${PORT:-21777}"
SANDBOX=p4-sign

# Inside the sandbox.
REPO=/sandbox/repo
DECOY=/sandbox/secrets/agent_key      # a copy of the private key, deliberately inside the
                                      # container and deliberately outside every allowed path

note()  { printf '\n== %s\n' "$*"; }
fault() { printf 'SETUP FAULT: %s\n' "$*" >&2; cleanup; exit 2; }
fail()  { printf '\nFALSIFIED: %s\n' "$*" >&2; cleanup; exit 1; }

SIDECAR_PID=""
cleanup() {
  [[ -n "$SIDECAR_PID" ]] && kill "$SIDECAR_PID" 2>/dev/null
  return 0
}
trap cleanup EXIT

command -v "$OPENSHELL" >/dev/null || fault "$OPENSHELL is not on PATH"
command -v docker       >/dev/null || fault "docker is not on PATH"
command -v ssh-keygen   >/dev/null || fault "ssh-keygen is not on PATH"
"$OPENSHELL" status >/dev/null 2>&1 || fault "the OpenShell gateway is not reachable"

note "OpenShell $("$OPENSHELL" --version)"

# ---------------------------------------------------------------- the key, on the host only
# workspace/.gitignore is '*', so this never reaches the repository. The probe asserts that
# rather than trusting it, because "the key is not in the repo" is the claim under test.
KEYDIR="$SPIKE/hostkey"
KEY="$KEYDIR/p4_signing"
rm -rf "$KEYDIR" && mkdir -p "$KEYDIR" || fault "cannot write $KEYDIR"
ssh-keygen -t ed25519 -N '' -C 'p4-probe-key' -f "$KEY" >/dev/null 2>&1 || fault "ssh-keygen failed"
git -C "$ROOT" check-ignore -q "$KEY" || fault "$KEY is NOT git-ignored - refusing to continue"
note "host key $KEY (git-ignored: yes)"

TOKEN="p4-$(head -c 18 /dev/urandom | base64 | tr -d '/+=')"
HOSTIP="${HOSTIP:-$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' | head -1)}"
[[ -n "$HOSTIP" ]] || fault "cannot determine a host IP the sandbox proxy can route to"

# The DID the commit trailer will claim. did:key is self-describing, so the check at step 7 is
# that the trailer names the SAME key that signed -- which is the failure that matters. A
# trailer naming some other identity is worse than no trailer.
DID="$(python3 - "$KEY.pub" <<'PY'
import base64, sys
raw = base64.b64decode(open(sys.argv[1]).read().split()[1])
# SSH wire format: string "ssh-ed25519", string <32-byte key>
off = 0
def field():
    global off
    n = int.from_bytes(raw[off:off+4], "big"); off += 4
    v = raw[off:off+n]; off += n
    return v
field()
pub = field()
data = b"\xed\x01" + pub
A = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
n = int.from_bytes(data, "big")
s = ""
while n:
    n, r = divmod(n, 58)
    s = A[r] + s
s = "1" * (len(data) - len(data.lstrip(b"\x00"))) + s
print("did:key:z" + s)
PY
)" || fault "could not derive did:key"
note "agent identity $DID"

# ---------------------------------------------------------------- the sidecar, on the host
note "starting the signing sidecar on $HOSTIP:$PORT"
python3 "$ROOT/docs/implement/probes/p4_sidecar.py" \
  --key "$KEY" --host 0.0.0.0 --port "$PORT" --token "$TOKEN" \
  >"$SPIKE/sidecar.log" 2>&1 &
SIDECAR_PID=$!
for _ in $(seq 1 25); do
  curl -sS -m 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break
  kill -0 "$SIDECAR_PID" 2>/dev/null || fault "sidecar died: $(tail -3 "$SPIKE/sidecar.log")"
  sleep 0.4
done
curl -sS -m 3 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 || fault "sidecar never became healthy"

# ---------------------------------------------------------------- the image
# The decoy is a real copy of the private key placed INSIDE the container. Without it, step 5
# would pass because of container isolation and prove nothing about the policy. The question is
# whether the policy denies a key that is right there, which is the arrangement that actually
# occurs when a repository holding vouch/ is uploaded into a sandbox.
note "building $IMAGE"
rm -rf "$SPIKE/image" && mkdir -p "$SPIKE/image/repo" "$SPIKE/image/secrets" || fault "cannot write $SPIKE"
cp "$KEY" "$SPIKE/image/secrets/agent_key"
cp "$KEY.pub" "$SPIKE/image/repo/signer.pub"
cp "$ROOT/docs/implement/probes/p4_bridge_client.py" "$SPIKE/image/bridge-client"
printf 'def build():\n    return "ok"\n' > "$SPIKE/image/repo/app.py"
# The base image does not run as root, so the modes are set here and COPY preserves them.
chmod 0600 "$SPIKE/image/secrets/agent_key"
chmod 0755 "$SPIKE/image/bridge-client"

# The decoy is owned by the SANDBOX user, not by root, and that is the whole point of it.
# Owned by root at 0600 it is unreadable because of ordinary Unix permissions, and the probe
# would report DENIED while proving nothing at all about the policy. Owned by uid 998 the only
# thing left that can refuse the read is Landlock. An earlier run of this probe made exactly
# that mistake, and p4-policy-union.yaml is the control that caught it.
cat > "$SPIKE/image/Dockerfile" <<DOCKER
FROM $BASE
COPY --chown=998:998 repo    $REPO
COPY --chown=998:998 secrets /sandbox/secrets
COPY --chown=0:0     bridge-client /usr/local/bin/p4-bridge-client
DOCKER
docker pull "$BASE" >/dev/null 2>&1 || true
docker build -q -t "$IMAGE" "$SPIKE/image" >/dev/null || fault "docker build failed"

# ---------------------------------------------------------------- the policy
# Filesystem: an allowlist. /sandbox itself is NOT listed, because P2 established that rights are
# the union of every matching hierarchy -- listing the parent would hand back what /sandbox/secrets
# is meant to withhold.
# Network: one endpoint, and `binaries` attributes egress to the interpreter that runs the bridge.
cat > "$SPIKE/p4-policy.yaml" <<YAML
version: 1
filesystem_policy:
  include_workdir: false
  read_only: [/usr, /lib, /lib64, /bin, /sbin, /etc, /proc, /dev/urandom]
  read_write: [$REPO, /tmp, /dev/null]
landlock:
  compatibility: hard_requirement
process:
  run_as_user: sandbox
  run_as_group: sandbox
network_policies:
  sidecar:
    name: p4-signing-sidecar
    endpoints:
      - host: $HOSTIP
        port: $PORT
        protocol: rest
        enforcement: enforce
        access: full
    binaries:
      - { path: "/usr/bin/python3*" }
      - { path: "/usr/local/bin/p4-bridge-client" }
YAML

note "booting $SANDBOX under the policy"
"$OPENSHELL" sandbox delete "$SANDBOX" >/dev/null 2>&1
"$OPENSHELL" sandbox create --name "$SANDBOX" --detach --no-tty --from "$IMAGE" \
  --policy "$SPIKE/p4-policy.yaml" \
  --env "P4_SIDECAR_URL=http://$HOSTIP:$PORT" \
  --env "P4_SIDECAR_TOKEN=$TOKEN" \
  --no-credential-warnings >/dev/null 2>&1
"$OPENSHELL" sandbox list 2>/dev/null | grep -q "$SANDBOX.*Ready" || fault "$SANDBOX did not reach Ready"

inside() { "$OPENSHELL" sandbox exec --name "$SANDBOX" --no-tty --timeout 60 -- sh -c "$1" 2>/dev/null; }

# ---------------------------------------------------------------- 5: the key must not be readable
note "5  the private key is in the container and must still be unreadable"
read_decoy="$(inside "head -c 40 $DECOY >/dev/null 2>&1 && echo READ || echo DENIED" | tail -1)"
read_ctrl="$(inside "head -c 10 $REPO/app.py >/dev/null 2>&1 && echo READ || echo DENIED" | tail -1)"
printf '    %-34s %s\n' "decoy key ($DECOY)" "$read_decoy"
printf '    %-34s %s\n' "control  ($REPO/app.py)" "$read_ctrl"
[[ "$read_ctrl"  == "READ"   ]] || fault "the control file is unreadable - the policy is wrong, not the finding"
[[ "$read_decoy" == "DENIED" ]] || fail  "the sandbox read the private key at $DECOY"

# 5b. The denial above has to be the POLICY's doing and not ordinary Unix permissions. Boot the
# same image, change one line -- list the parent /sandbox read_only -- and the same read must
# succeed. If it does not, the decoy is unreadable for a reason that has nothing to do with
# containment and step 5 is worthless.
note "5b control - the same read under a policy that lists the parent /sandbox"
cat > "$SPIKE/p4-policy-union.yaml" <<YAML
version: 1
filesystem_policy:
  include_workdir: false
  read_only: [/usr, /lib, /lib64, /bin, /sbin, /etc, /proc, /dev/urandom, /sandbox]
  read_write: [$REPO, /tmp, /dev/null]
landlock:
  compatibility: hard_requirement
process:
  run_as_user: sandbox
  run_as_group: sandbox
YAML
"$OPENSHELL" sandbox delete p4-union >/dev/null 2>&1
"$OPENSHELL" sandbox create --name p4-union --detach --no-tty --from "$IMAGE" \
  --policy "$SPIKE/p4-policy-union.yaml" >/dev/null 2>&1
"$OPENSHELL" sandbox list 2>/dev/null | grep -q "p4-union.*Ready" || fault "p4-union did not reach Ready"
union_read="$("$OPENSHELL" sandbox exec --name p4-union --no-tty --timeout 40 -- \
  sh -c "head -c 40 $DECOY >/dev/null 2>&1 && echo READ || echo DENIED" 2>/dev/null | tail -1)"
printf '    %-34s %s\n' "same key, parent listed" "$union_read"
"$OPENSHELL" sandbox delete p4-union >/dev/null 2>&1
[[ "$union_read" == "READ" ]] || fault \
  "the decoy is unreadable even when the policy permits it - Unix permissions are denying it, not Landlock, so step 5 proves nothing"

# ---------------------------------------------------------------- 6: the local socket claim
note "6  ASM-17 says 'a local socket'. Show what is actually there"
printf '    %s\n' "$(inside "ls -la /run/user/1000/ 2>&1 | head -3 || true" | tail -2)"
printf '    host socket visible inside: %s\n' "$(inside "test -S /run/user/1000/gcr/ssh && echo YES || echo NO" | tail -1)"

# ---------------------------------------------------------------- 7: sign through the bridge
note "7  produce a signed commit from inside, through the sidecar"
sign_out="$(inside "cd $REPO && \
  export HOME=/tmp && \
  git init -q -b main 2>/dev/null; \
  git config user.name 'P4 Agent' && \
  git config user.email 'agent@p4.invalid' && \
  git config gpg.format ssh && \
  git config user.signingkey $REPO/signer.pub && \
  git config gpg.ssh.program /usr/local/bin/p4-bridge-client && \
  git add -A && \
  git commit -q -S -m 'P4: signed without the key' --trailer 'Vouch-DID=$DID' 2>&1 | tail -3; \
  git log -1 --format='COMMIT %H' 2>/dev/null")"
printf '%s\n' "$sign_out" | sed 's/^/    /'
grep -q '^COMMIT ' <<<"$sign_out" || fail "no commit was produced from inside the sandbox: $sign_out"

# ---------------------------------------------------------------- 8: a control on the egress
note "8  egress control - an endpoint the policy does not name"
deny="$(inside "curl -sS -m 8 http://$HOSTIP:$((PORT+1))/health 2>&1 | head -1" | tail -1)"
printf '    %s\n' "$deny"
grep -q 'policy_denied' <<<"$deny" || printf '    NOTE: expected policy_denied and did not see it\n'

# ---------------------------------------------------------------- 9: verify outside
note "9  verify the signature outside the sandbox"
VERIFY="$SPIKE/verify"
rm -rf "$VERIFY" && mkdir -p "$VERIFY"
"$OPENSHELL" sandbox exec --name "$SANDBOX" --no-tty --timeout 60 -- \
  sh -c "cd $REPO && git cat-file commit HEAD" \
  >"$VERIFY/commit.raw" 2>/dev/null
# Strip anything the exec wrapper prints before the object itself.
python3 - "$VERIFY/commit.raw" "$VERIFY/commit.txt" <<'PY'
import pathlib, sys
lines = pathlib.Path(sys.argv[1]).read_text().splitlines()
start = next((i for i, l in enumerate(lines) if l.startswith("tree ")), 0)
pathlib.Path(sys.argv[2]).write_text("\n".join(lines[start:]) + "\n")
PY
printf '%s@p4.invalid %s\n' 'agent' "$(cat "$KEY.pub")" > "$VERIFY/allowed-signers"

# Re-verify by extracting the signature and the signed payload from the commit object itself.
python3 - "$VERIFY/commit.txt" "$VERIFY" <<'PY'
import sys, pathlib
body = pathlib.Path(sys.argv[1]).read_text().splitlines()
out = pathlib.Path(sys.argv[2])
sig, payload, in_sig = [], [], False
for line in body:
    if line.startswith("gpgsig "):
        in_sig = True
        sig.append(line[len("gpgsig "):])
        continue
    if in_sig:
        if line.startswith(" "):
            sig.append(line[1:])
            continue
        in_sig = False
    payload.append(line)
(out / "commit.sig").write_text("\n".join(sig) + "\n")
(out / "commit.payload").write_text("\n".join(payload) + "\n")
print("    signature lines:", len(sig))
PY

principal="$(ssh-keygen -Y find-principals -s "$VERIFY/commit.sig" -f "$VERIFY/allowed-signers" 2>/dev/null | head -1)"
if [[ -n "$principal" ]]; then
  ssh-keygen -Y verify -n git -f "$VERIFY/allowed-signers" -I "$principal" -s "$VERIFY/commit.sig" \
    <"$VERIFY/commit.payload" 2>&1 | sed 's/^/    /'
  verified=${PIPESTATUS[0]}
else
  verified=1
fi
[[ "$verified" == "0" ]] || fail "the signature produced through the sidecar does not verify"

# ---------------------------------------------------------------- 10: the trailer names the signer
note "10  the Vouch-DID trailer must name the key that signed"
trailer="$(grep -m1 '^Vouch-DID: ' "$VERIFY/commit.payload" | sed 's/^Vouch-DID: //')"
printf '    trailer %s\n    signer  %s\n' "${trailer:-<absent>}" "$DID"
[[ "$trailer" == "$DID" ]] || fail "the trailer does not name the signing key"

note "signatures the sidecar issued: $(curl -sS -m 3 "http://127.0.0.1:$PORT/health" | python3 -c 'import json,sys; print(json.load(sys.stdin)["signed"])' 2>/dev/null)"
printf '\nANSWERED: the key stayed on the host, the sandbox could not read a copy sitting\n'
printf 'inside its own filesystem, and the commit it produced verifies against the public key.\n'
printf 'The sidecar is this probe, not a shipped component. See the campaign document, P4.\n'
exit 0
