#!/usr/bin/env bash
#
# P3 — Does Agent Inbox authenticate against Aegra?  (ASM-04)
#
# Answers  — whether LangChain's Agent Inbox can connect to an Aegra deployment that requires a
#            credential, list the interrupts waiting there, and resume a thread with each of the
#            four HumanResponse verbs.
#
# Does not — say anything about Open SWE. Open SWE calls `interrupt()` nowhere: all 679 of its
#            Python files contain no call site, and its only "interrupt" is
#            `multitask_strategy="interrupt"`, which supersedes a running run. Its plan approval
#            is a TOOL (`agent/tools/approve_plan.py`) writing to its own plan store. So this
#            probe supplies its own graph, and what it settles is whether the INBOX and AEGRA
#            interoperate — not whether the inbox would show anything for an Open SWE run. That
#            second question is answered in the campaign document, and the answer is no.
#
# Falsifies P3 when — the inbox accepts only a LangSmith key, or it connects but the interrupt
#            list does not render, or a HumanResponse does not resume the thread. Committed to
#            `../test-specup-agent-shape-assumptions.md` before this ran.
#
# **"Does not render" needed a definition before the run, because it is not falsifiable as
# written.** Agent Inbox renders something for every payload it cannot parse: `contexts/utils.ts`
# substitutes an interrupt whose action is the sentinel `improper_schema`, and
# `interrupted-inbox-item.tsx:30-31` titles that row with the literal word "Interrupt". A
# screenshot with rows in it is therefore not evidence. This probe requires all three of:
#
#   1. the row title equals the action the graph emitted, and no row is titled "Interrupt";
#   2. the status pill reads "Requires Action", not "Ignore";
#   3. a thread whose config allows only `accept` offers an Accept control and offers neither
#      Respond nor Ignore -- which is the campaign's step 4, "the four booleans honoured".
#
# **It drives the production build, not `next dev`, and that is a finding rather than a
# convenience.** Under `next dev` the thread detail view crashes before any control is reachable:
# `MarkdownText` spreads `className` onto react-markdown's `<Markdown>`, and react-markdown 10
# throws on that prop unconditionally. The same tree, same lockfile, built with `next build` and
# served with `next start`, opens the same thread and renders every control. Both were reproduced
# from a fresh browser profile and a fresh server. Why the two differ is NOT resolved here, and
# the record says so rather than inventing a mechanism.
#
# Exit 0 the probe answered, 1 the probe was falsified, 2 a setup fault.
#
# Everything it creates lives under $SPIKE, inside `workspace/`, which git ignores entirely.

set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
PROBES="$ROOT/docs/implement/probes"
SPIKE="${SPIKE:-$ROOT/workspace/spike-0.1.3/P3}"
AEGRA_DIR="${AEGRA_DIR:-$ROOT/workspace/spike-0.1.3/P1/aegra}"
VENV="${VENV:-$ROOT/workspace/spike-0.1.3/P1/run/.venv}"

AEGRA_PORT="${AEGRA_PORT:-2027}"
APP_PORT="${APP_PORT:-3200}"
CDP_PORT="${CDP_PORT:-9333}"
GRAPH="${GRAPH:-p3_hitl}"

# The commits this was answered against. Override to re-read against newer upstreams -- and if
# the answer changes, that is a new result rather than this one.
INBOX_SHA="${INBOX_SHA:-f1616f3e7998e7e4fd574545b9558554d88d9c49}"
AEGRA_SHA="${AEGRA_SHA:-c07ad0d24164a18e139537ac3ab0e05358a990eb}"

# localStorage is scoped to an ORIGIN. Seeding the inbox's configuration at 127.0.0.1 and then
# loading it at localhost writes to a store the app never reads, and the app then reports
# "No threads found" -- which the falsifier would score as "the list does not render". One
# variable, used for both, so the two can never drift apart.
APP_ORIGIN="http://localhost:$APP_PORT"

note()  { printf '\n== %s\n' "$*"; }
fault() { printf '\nSETUP FAULT: %s\n' "$*" >&2; exit 2; }
fail()  { printf '\nFALSIFIED: %s\n' "$*" >&2; exit 1; }

cleanup() {
    [[ -n "${AEGRA_PID:-}" ]] && kill "$AEGRA_PID" 2>/dev/null
    [[ -n "${APP_PID:-}"   ]] && kill "$APP_PID"   2>/dev/null
    [[ -n "${CHROME_PID:-}" ]] && kill "$CHROME_PID" 2>/dev/null
    return 0
}
trap cleanup EXIT

for tool in docker curl node git; do
    command -v "$tool" >/dev/null || fault "$tool is not installed"
done
command -v google-chrome >/dev/null || fault \
    "google-chrome is not installed. The falsifier's middle clause is a claim about a browser,
     and Agent Inbox is a client-only Next.js app -- there are no API routes and no proxy, so
     nothing about rendering can be read from curl."
[[ -x "$VENV/bin/python" ]] || fault "no interpreter at $VENV -- run p1.sh first, it builds it"

mkdir -p "$SPIKE/run/logs" || fault "cannot create $SPIKE"

# ------------------------------------------------------------------ step 1: record the default --
# The campaign's step 1 says to record what the deployment defaults to BEFORE changing it. It is
# the only part of this probe that is about SpecUP's security posture rather than about the inbox.
note "step 1 - the authentication configuration, as shipped, before this probe changes it"
{
    echo "recorded $(date -u +%Y-%m-%dT%H:%M:%SZ) from aegra $AEGRA_SHA"
    echo
    echo "-- docker-compose.yml, every mention of auth:"
    grep -n -i "auth" "$AEGRA_DIR/docker-compose.yml" || echo "   (none: the compose file never mentions authentication)"
    echo
    echo "-- .env.example:"
    grep -n -B1 -A1 "AUTH_TYPE" "$AEGRA_DIR/.env.example"
    echo
    echo "-- the shipped aegra.json:"
    "$VENV/bin/python" -c "
import json; d=json.load(open('$AEGRA_DIR/aegra.json'))
print('   top-level keys:', sorted(d)); print('   auth key present:', 'auth' in d)"
} | tee "$SPIKE/run/logs/00-auth-defaults-before.txt"

# AUTH_TYPE is theatre on its own and the probe should not pretend otherwise: every branch of
# get_auth_backend() returns the same backend, and authenticate() hands back an authenticated
# "anonymous" user whenever no auth FILE is configured. What turns authentication on is the
# "auth" key in aegra.json, which the shipped file does not have.
grep -q "auth key present: False" "$SPIKE/run/logs/00-auth-defaults-before.txt" || \
    note "NOTE: upstream aegra.json now has an auth key; the default recorded above has changed"

# ------------------------------------------------------------------ step 2: the deployment ------
note "step 2 - postgres and redis, from Aegra's own compose"
(cd "$AEGRA_DIR" && cp -n .env.example .env 2>/dev/null; docker compose up -d postgres redis >/dev/null 2>&1) \
    || fault "docker compose failed; is something else holding 5432 or 6379?"
PG=$(cd "$AEGRA_DIR" && docker compose ps -q postgres)
for _ in $(seq 120); do
    docker exec "$PG" psql -U user -d aegra -tAc 'select 1' >/dev/null 2>&1 && break
    sleep 2
done
docker exec "$PG" psql -U user -d aegra -tAc 'select 1' >/dev/null 2>&1 \
    || fault "postgres did not accept connections"
# A database of its own, so P3's rows cannot be confused with the ones P1 left as "anonymous".
docker exec "$PG" psql -U user -d aegra -tAc "SELECT 1 FROM pg_database WHERE datname='aegra_p3'" \
    | grep -q 1 || docker exec "$PG" psql -U user -d aegra -c "CREATE DATABASE aegra_p3" >/dev/null
echo "  postgres and redis ready"

note "step 3 - configure Aegra for real authentication. Never 'none'."
TOKEN_A="${P3_TOKEN_A:-p3-inbox-$(head -c 18 /dev/urandom | base64 | tr -d '/+=')}"
TOKEN_B="${P3_TOKEN_B:-p3-other-$(head -c 18 /dev/urandom | base64 | tr -d '/+=')}"
printf '%s\n' "$TOKEN_A" > "$SPIKE/run/token-a.txt"; chmod 600 "$SPIKE/run/token-a.txt"

"$VENV/bin/python" - "$PROBES" "$SPIKE" <<'PY' || fault "could not write aegra.json"
import json, pathlib, sys
probes, spike = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
# Absolute paths. Aegra resolves both relative to the config file's directory, and the relative
# route from workspace/spike-0.1.3/P3/run back to docs/implement/probes is four levels of "..",
# which is the kind of string that stops resolving the moment a directory moves.
(spike / "run" / "aegra.json").write_text(json.dumps({
    "dependencies": [str(probes)],
    "graphs": {"p3_hitl": f"{probes / 'p3_graph.py'}:graph"},
    "auth": {"path": f"{probes / 'p3_auth.py'}:auth"},
}, indent=2) + "\n")
PY

cat > "$SPIKE/run/.env" <<EOF
AEGRA_CONFIG=$SPIKE/run/aegra.json
POSTGRES_DB=aegra_p3
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=password
POSTGRES_PORT=5432
POSTGRES_USER=user
AUTH_TYPE=custom
HOST=127.0.0.1
PORT=$AEGRA_PORT
LOG_LEVEL=INFO
ENV_MODE=LOCAL
REDIS_BROKER_ENABLED=false
CRON_ENABLED=false
P3_TOKEN_A=$TOKEN_A
P3_TOKEN_B=$TOKEN_B
P3_AUTH_LOG=$SPIKE/run/logs/auth-observations.jsonl
EOF
chmod 600 "$SPIKE/run/.env"

: > "$SPIKE/run/logs/auth-observations.jsonl"
(cd "$SPIKE/run" && set -a && . ./.env && set +a && \
    exec "$VENV/bin/python" -m uvicorn aegra_api.main:app \
        --host 127.0.0.1 --port "$AEGRA_PORT" >logs/server.log 2>&1) & AEGRA_PID=$!

for _ in $(seq 180); do
    curl -fsS -m 2 "http://127.0.0.1:$AEGRA_PORT/health" >/dev/null 2>&1 && break
    kill -0 "$AEGRA_PID" 2>/dev/null || { tail -20 "$SPIKE/run/logs/server.log" >&2; fault "Aegra exited during startup"; }
    sleep 1
done
curl -fsS -m 5 "http://127.0.0.1:$AEGRA_PORT/health" >/dev/null 2>&1 || fault "Aegra never became healthy"
echo "  Aegra healthy on $AEGRA_PORT with auth from p3_auth.py"

# ------------------------------------------------------------------ step 4: the protocol --------
note "step 4 - replay the requests Agent Inbox makes, and check what Aegra answers"
"$VENV/bin/python" "$PROBES/p3_protocol.py" \
    --base-url "http://127.0.0.1:$AEGRA_PORT" \
    --token-a "$TOKEN_A" --token-b "$TOKEN_B" --graph "$GRAPH" \
    --out "$SPIKE/run/logs/protocol.json" > "$SPIKE/run/logs/protocol-stdout.txt" 2>&1
case $? in
    0) echo "  protocol holds: 401 without a credential, 401 with a wrong one, 200 with the right one" ;;
    1) tail -5 "$SPIKE/run/logs/protocol-stdout.txt" >&2; fail "see $SPIKE/run/logs/protocol-stdout.txt" ;;
    *) tail -5 "$SPIKE/run/logs/protocol-stdout.txt" >&2; fault "the protocol replay could not run" ;;
esac

# ------------------------------------------------------------------ step 5: the fixtures --------
note "step 5 - one interrupted thread per verb, plus a restricted-config control"
"$VENV/bin/python" - "$TOKEN_A" "http://127.0.0.1:$AEGRA_PORT" "$GRAPH" "$SPIKE/run/verb-threads.json" <<'PY' \
    || fault "could not create the fixture threads"
import json, sys, time, urllib.request
tok, base, graph, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base+path, data=data, method=method)
    if data: req.add_header("Content-Type", "application/json")
    req.add_header("x-api-key", tok)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

ALL_ON = {"allow_ignore": True, "allow_respond": True, "allow_edit": True, "allow_accept": True}
specs = [(f"p3_verb_{v}", ALL_ON) for v in ("accept", "edit", "response", "ignore")]
# The control. If the inbox honours the config, this row offers Accept and offers nothing else.
specs.append(("p3_accept_only", {"allow_accept": True, "allow_ignore": False,
                                 "allow_respond": False, "allow_edit": False}))
made = {}
for action, cfg in specs:
    # The thread must be created by RUNNING the assistant, not by a bare POST /threads. Aegra
    # writes graph_id into thread metadata in run_preparation.py, at run creation, and Agent Inbox
    # always sends a metadata filter on graph_id -- so a thread that is created and never run can
    # never match it, and the inbox would show an empty list for a reason unrelated to the schema.
    tid = call("POST", "/threads", {})["thread_id"]
    call("POST", f"/threads/{tid}/runs",
         {"assistant_id": graph, "input": {"action": action, "interrupt_config": cfg}})
    made[action] = tid
for action, tid in made.items():
    for _ in range(60):
        if call("GET", f"/threads/{tid}")["status"] == "interrupted": break
        time.sleep(1)
    else:
        raise SystemExit(f"{action} never reached status interrupted")
    print(f"  {action:18s} {tid}")
json.dump(made, open(out, "w"), indent=2)
PY

# ------------------------------------------------------------------ step 6: the real client -----
note "step 6 - install and BUILD Agent Inbox ($INBOX_SHA)"
[[ -d "$SPIKE/agent-inbox/.git" ]] || \
    git clone --depth 50 https://github.com/langchain-ai/agent-inbox.git "$SPIKE/agent-inbox" >/dev/null 2>&1 \
    || fault "could not clone agent-inbox"
git -C "$SPIKE/agent-inbox" checkout --quiet "$INBOX_SHA" 2>/dev/null \
    || fault "agent-inbox has no commit $INBOX_SHA"

if [[ ! -x "$SPIKE/agent-inbox/node_modules/.bin/next" ]]; then
    # yarn, via corepack, because package.json pins `yarn@1.22.22` and carries a `resolutions`
    # block that npm ignores -- several of its entries are security pins. --frozen-lockfile so the
    # tree is the one upstream committed rather than whatever resolves today.
    (cd "$SPIKE/agent-inbox" && corepack enable >/dev/null 2>&1; \
     corepack yarn install --frozen-lockfile --non-interactive) \
        >"$SPIKE/run/logs/yarn-install.log" 2>&1 || {
            tail -10 "$SPIKE/run/logs/yarn-install.log" >&2; fault "yarn install failed"; }
fi
(cd "$SPIKE/agent-inbox" && node_modules/.bin/next build) >"$SPIKE/run/logs/next-build.log" 2>&1 \
    || { tail -15 "$SPIKE/run/logs/next-build.log" >&2; fault "next build failed"; }
(cd "$SPIKE/agent-inbox" && exec node_modules/.bin/next start -p "$APP_PORT") \
    >"$SPIKE/run/logs/next-start.log" 2>&1 & APP_PID=$!
for _ in $(seq 60); do curl -fsS -m 2 "$APP_ORIGIN/" -o /dev/null 2>/dev/null && break; sleep 2; done
curl -fsS -m 5 "$APP_ORIGIN/" -o /dev/null 2>/dev/null || fault "Agent Inbox did not serve on $APP_PORT"
echo "  Agent Inbox serving the production build on $APP_PORT"

note "step 7 - a browser"
rm -rf "$SPIKE/run/chrome-profile"
(exec google-chrome --headless=new --no-sandbox --disable-gpu \
    --remote-debugging-port="$CDP_PORT" --user-data-dir="$SPIKE/run/chrome-profile" about:blank) \
    >"$SPIKE/run/logs/chrome.log" 2>&1 & CHROME_PID=$!
for _ in $(seq 30); do curl -fsS -m 2 "http://127.0.0.1:$CDP_PORT/json/version" >/dev/null 2>&1 && break; sleep 1; done
curl -fsS -m 5 "http://127.0.0.1:$CDP_PORT/json/version" >/dev/null 2>&1 || fault "Chrome did not expose a CDP endpoint"

# ------------------------------------------------------------------ step 8: does it render? -----
note "step 8 - the four booleans, honoured or not (the restricted-config control)"
P3_CDP_PORT="$CDP_PORT" node "$PROBES/p3_browser.js" \
    --url "$APP_ORIGIN" --deployment "http://127.0.0.1:$AEGRA_PORT" --graph "$GRAPH" \
    --token "$TOKEN_A" --expect p3_accept_only \
    --out "$SPIKE/run/logs/browser-accept-only.json" >/dev/null 2>&1
rc=$?
[[ $rc -eq 2 ]] && fault "the browser driver could not run"
"$VENV/bin/python" - "$SPIKE/run/logs/browser-accept-only.json" <<'PY' || fail "see the message above"
import json, sys
d = json.load(open(sys.argv[1]))
if d["list_empty"]:
    raise SystemExit("the inbox rendered 'No threads found' against interrupted threads")
if d["detail_crashed"]:
    raise SystemExit("the detail view crashed: " + (d["page_errors"] or ["no exception"])[0])
btns = set(d["detail_buttons"])
# Accept is allowed; Ignore and Send Response are not. "Mark as Resolved" is always present and is
# NOT a resume -- it writes thread state as node __end__ -- so it is excluded from the check.
if "Accept" not in btns:
    raise SystemExit("a config allowing accept did not render an Accept control")
for forbidden in ("Ignore", "Send Response", "Submit"):
    if forbidden in btns:
        raise SystemExit(f"a config forbidding it still rendered '{forbidden}' - the four booleans are not honoured")
print(f"  accept-only rendered exactly: {sorted(btns & {'Accept','Ignore','Send Response','Submit'})}")
PY

note "step 9 - each of accept, edit, response and ignore, clicked in the browser"
for verb in accept edit response ignore; do
    P3_CDP_PORT="$CDP_PORT" node "$PROBES/p3_browser.js" \
        --url "$APP_ORIGIN" --deployment "http://127.0.0.1:$AEGRA_PORT" --graph "$GRAPH" \
        --token "$TOKEN_A" --expect "p3_verb_$verb" --act "$verb" \
        --out "$SPIKE/run/logs/browser-ui-$verb.json" >/dev/null 2>&1
    [[ $? -eq 2 ]] && fault "the browser driver could not run for '$verb'"
    "$VENV/bin/python" -c "
import json, sys
d = json.load(open('$SPIKE/run/logs/browser-ui-$verb.json'))
if d['detail_crashed']: sys.exit('the detail view crashed on $verb')
if d.get('clicked') != 'clicked': sys.exit('could not click the $verb control: ' + str(d.get('clicked')))
" || fail "the '$verb' control was not reachable in the inbox"
    echo "  clicked $verb"
done

# The UI's own success toast fires BEFORE the first stream chunk is read, so it is not evidence
# that anything resumed. Aegra is.
note "step 10 - what Aegra and the graph actually recorded"
"$VENV/bin/python" - "$TOKEN_A" "http://127.0.0.1:$AEGRA_PORT" "$SPIKE/run/verb-threads.json" <<'PY' \
    || fail "a HumanResponse sent from the inbox did not resume the thread"
import json, sys, urllib.request
tok, base, path = sys.argv[1], sys.argv[2], sys.argv[3]
def get(p):
    req = urllib.request.Request(base + p); req.add_header("x-api-key", tok)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())
threads = json.load(open(path))
bad = []
for action, tid in threads.items():
    if not action.startswith("p3_verb_"): continue
    verb = action.removeprefix("p3_verb_")
    status = get(f"/threads/{tid}")["status"]
    got = get(f"/threads/{tid}/state").get("values", {}).get("human_response")
    ok = status != "interrupted" and isinstance(got, list) and len(got) == 1 and got[0].get("type") == verb
    print(f"  {action:18s} {status:10s} {json.dumps(got)[:80]}")
    if not ok: bad.append(action)
if bad: raise SystemExit("did not resume, or resumed with the wrong payload: " + ", ".join(bad))
PY

note "step 11 - which header the browser actually used"
"$VENV/bin/python" - "$SPIKE/run/logs/auth-observations.jsonl" <<'PY' || fail "see the message above"
import collections, json, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
browser = [r for r in rows if r.get("origin")]
if not browser:
    raise SystemExit("no request carrying an Origin header reached Aegra - the browser never connected")
headers = collections.Counter(r["credential_header"] for r in browser)
outcomes = collections.Counter(r["outcome"] for r in browser)
print(f"  {len(browser)} browser requests; credential header {dict(headers)}; outcomes {dict(outcomes)}")
if set(outcomes) != {"accepted"}:
    raise SystemExit(f"the browser was not authenticated on every request: {dict(outcomes)}")
if set(headers) != {"x-api-key"}:
    raise SystemExit(f"unexpected credential header from the browser: {dict(headers)}")
PY

echo
echo "P3 answered: the inbox authenticated with an arbitrary key in x-api-key, listed the"
echo "interrupts by their own action names, honoured the four config booleans, and resumed the"
echo "thread with each of accept, edit, response and ignore."
echo "Condition: this is the PRODUCTION build. Under 'next dev' the detail view crashes first."
exit 0
