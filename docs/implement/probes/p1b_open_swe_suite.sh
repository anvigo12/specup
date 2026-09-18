#!/usr/bin/env bash
#
# P1b — Does Open SWE's own test suite pass in the environment P1 composed?
#
# Answers  — whether Open SWE is intact under the dependency set SpecUP resolves
#            for it, and what the Elastic-2.0 exclusion actually costs. It runs
#            the suite TWICE, because the pair is the check:
#              1. as Open SWE declares it, with `langgraph-api` present
#              2. with `langgraph-api`, `langgraph-runtime-inmem` and
#                 `langgraph-cli` uninstalled — the licence-critical shape
#
# Does not — exercise a model, a sandbox, GitHub, or any network service beyond
#            the Postgres it starts. Open SWE's suite is hermetic apart from the
#            PostgreSQL regressions, which this script enables rather than skips.
#
# **This is not a probe.** It has no pre-registered falsifier, so its output is
# evidence and never an `answered`. `record.py` will not take it, by design.
#
# Exit 0 both runs matched the recorded result, 1 they did not, 2 a setup fault.
#
# Prerequisite: `p1.sh` has run, so $SPIKE/run/.venv and the two clones exist.

set -uo pipefail

SPIKE="${SPIKE:-$(git rev-parse --show-toplevel)/workspace/spike-0.1.3/P1}"
VENV="$SPIKE/run/.venv"
PY="$VENV/bin/python"

# What was recorded on 2026-09-18. A different number is a finding, not a bug in
# this script — print it and stop rather than adjusting these.
EXPECT_WITH=3434          # passed, with langgraph-api present
EXPECT_WITHOUT_PASS=3433  # passed, with it removed
EXPECT_WITHOUT_FAIL=1     # and this one fails: the dev-server checkpoint import

fault() { echo "setup fault: $*" >&2; exit 2; }
step()  { echo; echo "── $* ──"; }

[[ -x "$PY" ]] || fault "no venv at $VENV — run p1.sh first"
[[ -d "$SPIKE/open-swe" ]] || fault "no open-swe checkout at $SPIKE/open-swe"

# Open SWE declares these in its `dev` extra; p1.sh does not install them
# because the probe proper does not need them.
step "dev extras, exactly as open-swe/pyproject.toml declares them"
uv pip install --python "$PY" \
    "ty==0.0.78" "pytest>=9.1.1" "pytest-asyncio>=1.4.0" "ruff>=0.16.4" "Pygments>=2.21.0" \
    >/dev/null 2>&1 || fault "could not install the dev extras"

step "postgres, so the 308 PostgreSQL regressions run instead of skipping"
(cd "$SPIKE/aegra" && docker compose up -d postgres >/dev/null 2>&1) \
    || fault "docker compose failed to start postgres"
PG=$(cd "$SPIKE/aegra" && docker compose ps -q postgres)
for _ in $(seq 60); do
    docker exec "$PG" pg_isready -U user -d aegra >/dev/null 2>&1 && break
    sleep 1
done
docker exec "$PG" pg_isready -U user -d aegra >/dev/null 2>&1 || fault "postgres not ready"
docker exec "$PG" psql -U user -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='openswe_tests'" | grep -q 1 \
    || docker exec "$PG" psql -U user -d postgres -c "CREATE DATABASE openswe_tests" >/dev/null

# The scheme matters and the default is wrong. tests/analytics/conftest.py calls
# create_async_engine() on whatever this variable holds; a bare `postgresql://`
# makes SQLAlchemy pick the SYNC psycopg2 dialect, and psycopg2 appears nowhere
# in Open SWE's pyproject.toml or uv.lock, so all 308 error out. Naming the
# async driver explicitly is the whole fix.
export TEST_ANALYTICS_POSTGRES_URI="postgresql+asyncpg://user:password@localhost:5432/openswe_tests"

run_suite() {  # $1 = label, writes "<passed> <failed>" to stdout
    local out
    out=$(cd "$SPIKE/open-swe" && "$PY" -m pytest -q -p no:cacheprovider 2>&1 | tail -3)
    echo "$out" | tail -1 >&2
    local passed failed
    passed=$(grep -oE '[0-9]+ passed' <<<"$out" | grep -oE '[0-9]+' | head -1)
    failed=$(grep -oE '[0-9]+ failed' <<<"$out" | grep -oE '[0-9]+' | head -1)
    echo "${passed:-0} ${failed:-0}"
}

step "run 1 of 2 — as Open SWE declares itself (langgraph-api present)"
uv pip install --python "$PY" "langgraph-cli[inmem]>=0.4.31" "langgraph-api>=0.13.3,<0.14" \
    >/dev/null 2>&1 || fault "could not restore langgraph-api"
read -r WITH_PASS WITH_FAIL <<<"$(run_suite with)"

step "run 2 of 2 — with the Elastic-2.0 package excluded"
uv pip uninstall --python "$PY" langgraph-api langgraph-runtime-inmem langgraph-cli \
    >/dev/null 2>&1 || fault "could not remove langgraph-api"
read -r WITHOUT_PASS WITHOUT_FAIL <<<"$(run_suite without)"

step "verdict"
printf "  with langgraph-api:    %s passed, %s failed  (recorded: %s, 0)\n" \
    "$WITH_PASS" "$WITH_FAIL" "$EXPECT_WITH"
printf "  without langgraph-api: %s passed, %s failed  (recorded: %s, %s)\n" \
    "$WITHOUT_PASS" "$WITHOUT_FAIL" "$EXPECT_WITHOUT_PASS" "$EXPECT_WITHOUT_FAIL"

rc=0
[[ "$WITH_PASS"    == "$EXPECT_WITH"         && "$WITH_FAIL"    == "0" ]] || rc=1
[[ "$WITHOUT_PASS" == "$EXPECT_WITHOUT_PASS" && "$WITHOUT_FAIL" == "$EXPECT_WITHOUT_FAIL" ]] || rc=1

if [[ $rc -ne 0 ]]; then
    echo
    echo "The numbers moved. That is a finding about Open SWE or about the" >&2
    echo "resolution, and it belongs in the campaign document — not in these" >&2
    echo "constants." >&2
fi
exit $rc
