#!/usr/bin/env bash
#
# P1 — Do Open SWE's five graphs run unchanged under Aegra?  (ASM-03)
#
# Answers  — whether Aegra loads, compiles and runs the five graphs Open SWE
#            declares in its own `langgraph.json`, with Open SWE's source tree
#            left byte-identical.
#
# Does not — say whether the graphs do anything useful. It completes ONE run
#            against a stub model. See `p1_stub_anthropic.py`.
#
# Falsifies P1 when — any of the five graphs needs a change to Open SWE's source
#            to load or to complete one run. A change to `aegra.json`, to
#            configuration or to an environment variable is not a falsifier;
#            those are the files this stack owns. The falsifier was committed in
#            `../test-specup-agent-shape-assumptions.md` before this ran.
#
# Exit 0 the probe answered, 1 the probe was falsified, 2 a setup fault — the
# same three codes the validators use, where 2 is an operator error.
#
# Everything it creates lives under $SPIKE, which is inside `workspace/` and so
# is ignored by git in its entirety. Nothing is ever written into `open-swe/`.

set -uo pipefail

SPIKE="${SPIKE:-$(git rev-parse --show-toplevel)/workspace/spike-0.1.3/P1}"
PORT="${PORT:-2026}"
STUB_PORT="${STUB_PORT:-8787}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The two commits P1 was answered against. Override to re-read against newer
# upstreams — and if the answer changes, that is a new result, not this one.
OPEN_SWE_SHA="${OPEN_SWE_SHA:-8aac7c52b707c7247b38de20e2e6389adf3281d9}"
AEGRA_SHA="${AEGRA_SHA:-c07ad0d24164a18e139537ac3ab0e05358a990eb}"

fail()  { echo "FALSIFIED: $*" >&2; exit 1; }
fault() { echo "setup fault: $*" >&2; exit 2; }
step()  { echo; echo "── $* ──"; }

cleanup() {
    [[ -n "${SERVER_PID:-}" ]] && kill "$SERVER_PID" 2>/dev/null
    [[ -n "${STUB_PID:-}"   ]] && kill "$STUB_PID"   2>/dev/null
    return 0
}
trap cleanup EXIT

command -v uv     >/dev/null || fault "uv is not installed"
command -v docker >/dev/null || fault "docker is not installed"
command -v curl   >/dev/null || fault "curl is not installed"

mkdir -p "$SPIKE/run/logs" || fault "cannot create $SPIKE"
cd "$SPIKE" || fault "cannot enter $SPIKE"

# ---------------------------------------------------------------- checkouts --
step "checkouts"
for pair in "open-swe https://github.com/langchain-ai/open-swe.git $OPEN_SWE_SHA" \
            "aegra    https://github.com/aegra/aegra.git          $AEGRA_SHA"; do
    # shellcheck disable=SC2086
    set -- $pair
    if [[ ! -d "$1/.git" ]]; then
        git clone "$2" "$1" >/dev/null 2>&1 || fault "clone of $1 failed"
    fi
    git -C "$1" fetch --depth 1 origin "$3" >/dev/null 2>&1
    git -C "$1" checkout --quiet "$3" 2>/dev/null || fault "$1 has no commit $3"
    echo "  $1 $(git -C "$1" rev-parse HEAD)"
done

# The five entrypoints, read out of Open SWE's own langgraph.json rather than
# retyped here. Retyping them is how a probe starts testing its author's memory.
step "the five graphs, as Open SWE declares them"
GRAPHS_JSON=$(python3 - "$SPIKE/open-swe/langgraph.json" <<'PY'
import json, sys
graphs = json.load(open(sys.argv[1]))["graphs"]
out = {}
for gid, ref in graphs.items():
    module, export = ref.split(":", 1)
    # Aegra resolves a graph reference as a FILE PATH; Open SWE writes it as a
    # module path. Rewriting it is a change to aegra.json, which this stack owns.
    out[gid] = "../open-swe/" + module.replace(".", "/") + ".py:" + export
    print(f"  {gid:10s} {ref}", file=sys.stderr)
print(json.dumps({"dependencies": ["../open-swe"], "graphs": out}, indent=2))
PY
) || fault "could not read open-swe/langgraph.json"
echo "$GRAPHS_JSON" > run/aegra.json
EXPECTED=$(python3 -c "import json;print(' '.join(sorted(json.load(open('$SPIKE/run/aegra.json'))['graphs'])))")
COUNT=$(wc -w <<<"$EXPECTED")
[[ "$COUNT" -eq 5 ]] || fault "expected 5 graphs in langgraph.json, found $COUNT ($EXPECTED)"

# ------------------------------------------------------------- environment ---
step "one interpreter for both projects"
cat > run/pyproject.toml <<'EOF'
[project]
name = "specup-p1-probe"
version = "0"
requires-python = ">=3.14"
dependencies = ["aegra-api", "open-swe-agent"]

[tool.uv.sources]
aegra-api = { path = "../aegra/libs/aegra-api", editable = true }
open-swe-agent = { path = "../open-swe", editable = true }

[tool.uv]
# Verbatim from open-swe/pyproject.toml. uv reads these from the workspace root,
# not from a path dependency, so they have to be restated to resolve at all.
override-dependencies = ["deepagents==0.7.13", "wcmatch>=11.0"]
constraint-dependencies = ["langgraph-api>=0.13.3,<0.14"]
EOF
(cd run && uv sync --python 3.14 >logs/uv-sync.log 2>&1) \
    || { tail -20 run/logs/uv-sync.log >&2; fail "aegra-api and open-swe-agent do not resolve together"; }
echo "  $(run/.venv/bin/python -V)"

cat > run/.env <<EOF
AEGRA_CONFIG=aegra.json
POSTGRES_DB=aegra
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=password
POSTGRES_PORT=5432
POSTGRES_USER=user
AUTH_TYPE=noop
HOST=127.0.0.1
PORT=$PORT
LOG_LEVEL=INFO
ENV_MODE=LOCAL
REDIS_BROKER_ENABLED=false
CRON_ENABLED=false
# A stub, not a provider. P1 tests the path, not the model.
ANTHROPIC_API_KEY=stub-not-a-real-key
ANTHROPIC_BASE_URL=http://127.0.0.1:$STUB_PORT
EOF

# ---------------------------------------------------------------- services ---
step "postgres and redis, from Aegra's own compose"
cp -n aegra/.env.example aegra/.env 2>/dev/null
(cd aegra && docker compose up -d postgres redis >/dev/null 2>&1) \
    || fault "docker compose failed; is another service holding 5432 or 6379?"
for _ in $(seq 60); do
    docker exec "$(cd aegra && docker compose ps -q postgres)" pg_isready -U user -d aegra >/dev/null 2>&1 && break
    sleep 1
done
docker exec "$(cd aegra && docker compose ps -q postgres)" pg_isready -U user -d aegra >/dev/null 2>&1 \
    || fault "postgres did not become ready"
echo "  postgres and redis ready"

# ------------------------------------------------------------------- server --
step "the stub model, then the server"
(cd run && ./.venv/bin/python "$HERE/p1_stub_anthropic.py" "$STUB_PORT" >logs/stub.log 2>&1) & STUB_PID=$!
(cd run && set -a && . ./.env && set +a && \
    exec ./.venv/bin/python -m uvicorn aegra_api.main:app \
        --host 127.0.0.1 --port "$PORT" >logs/server.log 2>&1) & SERVER_PID=$!

for _ in $(seq 120); do
    curl -sf -m 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break
    sleep 1
done
curl -sf -m 5 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 || {
    grep -iE "not found|Traceback|Error" run/logs/server.log | tail -20 >&2
    fail "the server did not come up with Open SWE's graphs configured"
}
echo "  healthy on $PORT"

# ------------------------------------------------------------------- probe ---
step "step 4 — does the server list all five over the Agent Protocol?"
ASSISTANTS=$(curl -s -X POST "http://127.0.0.1:$PORT/assistants/search" \
    -H 'Content-Type: application/json' -d '{"limit":50}')
LISTED=$(python3 -c "
import json,sys
a=json.loads(sys.stdin.read())
print(' '.join(sorted(x['graph_id'] for x in a)))" <<<"$ASSISTANTS")
echo "  listed:   $LISTED"
echo "  expected: $EXPECTED"
[[ "$LISTED" == "$EXPECTED" ]] || fail "assistants listed ($LISTED) != graphs declared ($EXPECTED)"

step "step 4b — does each one actually compile?"
# An assistant row is a database row. Asking for the graph forces the factory to
# run and the graph to build, which is what "loads" has to mean here.
for gid in $EXPECTED; do
    id=$(python3 -c "
import json,sys
print(next(x['assistant_id'] for x in json.loads(sys.stdin.read()) if x['graph_id']=='$gid'))" <<<"$ASSISTANTS")
    body=$(curl -s -m 60 -w '\n%{http_code}' "http://127.0.0.1:$PORT/assistants/$id/graph")
    code=$(tail -1 <<<"$body")
    [[ "$code" == "200" ]] || fail "graph '$gid' did not build (HTTP $code)"
    echo "  $gid built: $(head -n -1 <<<"$body" | python3 -c "
import json,sys
d=json.load(sys.stdin); print(len(d.get('nodes',[])),'nodes',len(d.get('edges',[])),'edges')")"
done

step "step 5 — one thread to completion on 'chat'"
CHAT_ID=$(python3 -c "
import json,sys
print(next(x['assistant_id'] for x in json.loads(sys.stdin.read()) if x['graph_id']=='chat'))" <<<"$ASSISTANTS")
TH=$(curl -s -X POST "http://127.0.0.1:$PORT/threads" -H 'Content-Type: application/json' -d '{}' \
     | python3 -c "import json,sys;print(json.load(sys.stdin)['thread_id'])")
curl -s -m 180 -X POST "http://127.0.0.1:$PORT/threads/$TH/runs/wait" \
    -H 'Content-Type: application/json' \
    -d "{\"assistant_id\":\"$CHAT_ID\",\"input\":{\"messages\":[{\"type\":\"human\",\"content\":\"Say OK and nothing else.\"}]}}" \
    > run/logs/run-wait.json 2>&1
STATUS=$(curl -s "http://127.0.0.1:$PORT/threads/$TH/runs" | python3 -c "
import json,sys
r=json.load(sys.stdin)[0]
print(r['status'], '|', r.get('error_message') or '')")
echo "  run: $STATUS"
grep -q '^success ' <<<"$STATUS" || fail "the chat run did not complete: $STATUS"

# ----------------------------------------------------------------- the rule --
step "the falsifier itself — did Open SWE's source change?"
DIRTY=$(git -C open-swe status --porcelain)
[[ -z "$DIRTY" ]] || { echo "$DIRTY" >&2; fail "open-swe was modified, which is exactly what ASM-03 denies"; }
echo "  open-swe clean at $(git -C open-swe rev-parse --short HEAD)"

echo
echo "P1 answered: five graphs listed, five built, one run completed, open-swe untouched."
exit 0
