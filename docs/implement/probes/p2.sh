#!/usr/bin/env bash
# P2 — ASM-28. Does an OpenShell filesystem policy block a write to the governance tree?
#
# Falsified when the write succeeds, or when the policy language cannot express the exclusion.
# Both halves matter here, and the answer differs between them:
#
#   expressed by SUBTRACTION (read_only nested inside a read_write parent)  -> every write succeeds
#   expressed as an ALLOWLIST (enumerate what may be written)               -> writes denied
#   truncate(2) against the allowlist form                                  -> SUCCEEDS on <= v0.0.116
#
# The third line is the falsifier. It is a property of the OpenShell version, not of the policy:
# v0.0.116 builds the ruleset at Landlock ABI::V2, which predates LANDLOCK_ACCESS_FS_TRUNCATE.
# main and v0.1.0-pre.2+ use ABI::V3. Run this against a newer build and step 5c should flip; when
# it does, re-record P2 with record.py --supersede rather than editing the constants here.
#
# This script does NOT install OpenShell. The installer needs root, and a probe that silently
# acquires root is a worse problem than an unanswered assumption. Install it yourself:
#
#   curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
#   # pin a version with:  ... | OPENSHELL_VERSION=v0.1.0-pre.3 sh
#
# Exit codes: 0 the exclusion held completely, 1 falsified, 2 setup fault.

set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
SPIKE="${SPIKE:-$ROOT/workspace/spike-0.1.3/P2}"
IMAGE="${IMAGE:-p2-governed-tree:latest}"
BASE="${BASE:-ghcr.io/nvidia/openshell-community/sandboxes/base:latest}"
GOV="/sandbox/tree/.specify/governance/allowed-signers"
EXT="/sandbox/tree/.specify/extensions/openup/scripts/python/validate_trace.py"
LNK="/sandbox/tree/src/openup-alias/scripts/python/validate_trace.py"
SRC="/sandbox/tree/src/app.py"

note() { printf '\n== %s\n' "$*"; }
fault() { printf 'SETUP FAULT: %s\n' "$*" >&2; exit 2; }
fail()  { printf '\nFALSIFIED: %s\n' "$*" >&2; exit 1; }

command -v openshell >/dev/null || fault "openshell is not on PATH — install it first, as a human"
command -v docker    >/dev/null || fault "docker is not on PATH"
openshell status >/dev/null 2>&1 || fault "the OpenShell gateway is not reachable — 'openshell status'"

note "OpenShell $(openshell --version), host Landlock ABI $(
  python3 -c 'import ctypes;l=ctypes.CDLL("libc.so.6",use_errno=True);print(l.syscall(444,None,ctypes.c_size_t(0),ctypes.c_uint32(1)))' 2>/dev/null || echo '?'
)"

# ---------------------------------------------------------------- the governed tree
# It has to be baked into the image. --upload runs AFTER the policy binds, so a
# hard_requirement policy naming paths inside an uploaded tree aborts startup first.
note "Building $IMAGE with a SpecUP-governed tree at /sandbox/tree"
rm -rf "$SPIKE/tree" "$SPIKE/image"
mkdir -p "$SPIKE/tree/src" || fault "cannot write $SPIKE"
cp -a "$ROOT/.specify" "$SPIKE/tree/.specify" || fault "no .specify to copy"
mkdir -p "$SPIKE/tree/.specify/extensions/openup/scripts/python"
cp "$ROOT/extensions/openup/scripts/python/validate_trace.py" \
   "$ROOT/extensions/openup/scripts/python/openup_model.py" \
   "$SPIKE/tree/.specify/extensions/openup/scripts/python/" || fault "no validators to copy"
printf 'def build():\n    return "ok"\n' > "$SPIKE/tree/src/app.py"
ln -s ../.specify/extensions/openup "$SPIKE/tree/src/openup-alias"

mkdir -p "$SPIKE/image"
cp -a "$SPIKE/tree" "$SPIKE/image/tree"
cat > "$SPIKE/image/Dockerfile" <<DOCKER
FROM $BASE
COPY --chown=998:998 tree /sandbox/tree
DOCKER
docker pull "$BASE" >/dev/null 2>&1 || true
docker build -q -t "$IMAGE" "$SPIKE/image" >/dev/null || fault "docker build failed"

# ---------------------------------------------------------------- the two policies
# include_workdir defaults to TRUE and would append /sandbox to read_write, granting exactly
# what these files withhold. compatibility defaults to best_effort, which can degrade to no
# enforcement with only a warning. Both are set explicitly, every time.
cat > "$SPIKE/p2-subtraction.yaml" <<'YAML'
version: 1
filesystem_policy:
  include_workdir: false
  read_only: [/usr, /lib, /etc, /dev/urandom, /sandbox, /sandbox/tree/.specify/extensions, /sandbox/tree/.specify/governance]
  read_write: [/tmp, /dev/null, /sandbox/tree]
landlock:
  compatibility: hard_requirement
YAML

cat > "$SPIKE/p2-allowlist.yaml" <<'YAML'
version: 1
filesystem_policy:
  include_workdir: false
  read_only: [/usr, /lib, /etc, /dev/urandom, /sandbox, /sandbox/tree, /sandbox/tree/.specify]
  read_write: [/tmp, /dev/null, /sandbox/tree/src]
landlock:
  compatibility: hard_requirement
YAML

boot() { # boot <name> <policy>
  openshell sandbox delete "$1" >/dev/null 2>&1
  openshell sandbox create --name "$1" --detach --no-tty --from "$IMAGE" --policy "$2" >/dev/null 2>&1
  openshell sandbox list 2>/dev/null | grep -q "$1.*Ready" || fault "sandbox $1 did not reach Ready"
}

append() { # append <sandbox> <path> -> WROTE | DENIED
  openshell sandbox exec --name "$1" --no-tty --timeout 40 -- \
    sh -c "printf '\n# probe\n' >> '$2' 2>/tmp/e && echo WROTE || echo DENIED" 2>/dev/null | tail -1
}

# ---------------------------------------------------------------- step 5a: subtraction
boot p2-sub "$SPIKE/p2-subtraction.yaml"
note "5a  exclusion by SUBTRACTION — read_only nested inside read_write /sandbox/tree"
for p in "$EXT" "$GOV" "$LNK"; do
  printf '    %-62s %s\n' "$p" "$(append p2-sub "$p")"
done
printf '    %-62s %s\n' "(control: /sandbox/outside.txt, in no list)" "$(append p2-sub /sandbox/outside.txt)"
echo "    A nested read_only adds no restriction: rights are the union of every matching hierarchy."

# ---------------------------------------------------------------- step 5b: allowlist
boot p2-allow "$SPIKE/p2-allowlist.yaml"
note "5b  exclusion as an ALLOWLIST — enumerate what may be written"
rc=0
[[ "$(append p2-allow "$SRC")" == WROTE  ]] || { echo "    source file was not writable"; rc=1; }
for p in "$EXT" "$GOV" "$LNK"; do
  r=$(append p2-allow "$p"); printf '    %-62s %s\n' "$p" "$r"
  [[ "$r" == DENIED ]] || rc=1
done
[[ $rc -eq 0 ]] || fail "a protected path was writable even as an allowlist"
echo "    All three denied, symlink included — the case Vouch Shield cannot catch."

# ---------------------------------------------------------------- step 5c: the falsifier
note "5c  truncate(2) against the same allowlist policy"
before=$(openshell sandbox exec --name p2-allow --no-tty --timeout 30 -- wc -c "$GOV" 2>/dev/null | tail -1 | awk '{print $1}')
openshell sandbox exec --name p2-allow --no-tty --timeout 30 -- \
  perl -e "print truncate('$GOV',0) ? \"SUCCEEDED\n\" : \"DENIED\n\"" 2>/dev/null | tail -1
after=$(openshell sandbox exec --name p2-allow --no-tty --timeout 30 -- wc -c "$GOV" 2>/dev/null | tail -1 | awk '{print $1}')
printf '    allowed-signers: %s bytes -> %s bytes\n' "${before:-?}" "${after:-?}"

note "attestation — the ABI the ruleset was actually built at"
openshell logs p2-allow -n 200 2>/dev/null | grep -E "CONFIG:(PROBED|APPLYING|BUILT)" | head -3

openshell sandbox delete p2-sub   >/dev/null 2>&1
openshell sandbox delete p2-allow >/dev/null 2>&1

if [[ "${after:-1}" == "0" ]]; then
  fail "truncate(2) emptied the trust root APV-002 verifies against. The ruleset was built at
  Landlock ABI v2, which predates LANDLOCK_ACCESS_FS_TRUNCATE. Upstream main and v0.1.0-pre.2+
  build at ABI v3; re-run this against one of those and record with --supersede."
fi

note "the exclusion held, truncation included — re-record P2 with record.py --supersede"
exit 0
