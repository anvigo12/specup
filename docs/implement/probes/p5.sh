#!/usr/bin/env bash
# P5 — ASM-11. Does one model server serve both the embedder and the reranker?
#
# Falsified when two processes are required: because the server cannot host two models at once,
# or because it supports embedding but not reranking.
#
# The serving runtime is Infinity (MIT). It was chosen over Text Embeddings Inference for one
# reason read from upstream rather than assumed: TEI's usage line is
# `text-embeddings-router [OPTIONS] --model-id <MODEL_ID>` -- singular and required, one model per
# process, so TEI cannot answer this question in the affirmative at all. Infinity's own --help
# says "cli options can be overloaded i.e. `v2 --model-id model/id1 --model-id model/id2`".
# If TEI is the runtime a deployment wants, ASM-11 is false for that deployment by construction.
#
# The models are the ones stack 3.6 decided, pinned to their commit digests:
#   Qwen/Qwen3-Embedding-0.6B  apache-2.0  97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3
#   Qwen/Qwen3-Reranker-0.6B   apache-2.0  e61197ed45024b0ed8a2d74b80b4d909f1255473
#
# Both are Qwen3ForCausalLM. That matters for the reranker: it is not a sequence-classification
# cross-encoder, and a generic CrossEncoder loader gives it a randomly initialised score head
# that returns HTTP 200 and meaningless numbers. p5_measure.py therefore reranks two queries over
# a shared corpus and requires each to place its own answer first. Serving is not ranking.
#
# Exit codes: 0 one process served both and the reranker ranked, 1 falsified, 2 setup fault.

set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
SPIKE="${SPIKE:-$ROOT/workspace/spike-0.1.3/P5}"
VENV="${VENV:-$SPIKE/.venv}"
PORT="${PORT:-7997}"
# The decided pair, pinned. Overridable only so the harness itself can be smoke-tested against
# two small models before an hour of downloading -- a probe result must use the defaults.
EMBED_ID="${EMBED_ID:-Qwen/Qwen3-Embedding-0.6B}"
EMBED_REV="${EMBED_REV:-97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3}"
RERANK_ID="${RERANK_ID:-Qwen/Qwen3-Reranker-0.6B}"
RERANK_REV="${RERANK_REV:-e61197ed45024b0ed8a2d74b80b4d909f1255473}"

export HF_HOME="${HF_HOME:-$SPIKE/hf}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"   # the digests are pinned; nothing should be fetched
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"

note()  { printf '\n== %s\n' "$*"; }
fault() { printf 'SETUP FAULT: %s\n' "$*" >&2; exit 2; }
fail()  { printf '\nFALSIFIED: %s\n' "$*" >&2; exit 1; }

[[ -x "$VENV/bin/infinity_emb" ]] || fault "no Infinity in $VENV. Build it:
  uv venv --python 3.13 $SPIKE/.venv
  UV_TORCH_BACKEND=cpu uv pip install --python $SPIKE/.venv 'infinity_emb[torch,server]==0.0.77' 'click<8.2'
  HF_HOME=$SPIKE/hf $SPIKE/.venv/bin/hf download $EMBED_ID  --revision $EMBED_REV
  HF_HOME=$SPIKE/hf $SPIKE/.venv/bin/hf download $RERANK_ID --revision $RERANK_REV"

for m in "$EMBED_ID" "$RERANK_ID"; do
  d="$HF_HOME/hub/models--${m//\//--}"
  [[ -d "$d" ]] || fault "$m is not in $HF_HOME - see the download commands above"
done

note "host: $(nproc) cpus, $(free -g | awk '/^Mem:/{print $2}') GiB RAM, \
accelerator: $("$VENV/bin/python" -c 'import torch;print("cuda" if torch.cuda.is_available() else "none - cpu only")')"

# ---------------------------------------------------------------- one process, two models
# float32 on purpose. This CPU is AVX2-only, with no AVX-512, no VNNI and no CPU bf16, so a
# reduced dtype buys nothing here and costs accuracy. A machine with AMX should re-measure.
note "starting ONE server with both models on port $PORT"
LOG="$SPIKE/server.log"
: > "$LOG"
"$VENV/bin/infinity_emb" v2 \
  --model-id "$EMBED_ID"  --served-model-name embed  --revision "$EMBED_REV" \
  --model-id "$RERANK_ID" --served-model-name rerank --revision "$RERANK_REV" \
  --device cpu --engine torch --dtype float32 --batch-size 4 \
  --no-bettertransformer --port "$PORT" >"$LOG" 2>&1 &
SERVER=$!

cleanup() { kill "$SERVER" 2>/dev/null; wait "$SERVER" 2>/dev/null; }
trap cleanup EXIT

# Model warmup runs before the server reports ready, and two 0.6B models load slowly on a CPU
# like this one, so the budget is generous. A dead server is detected rather than waited out.
deadline=$(( SECONDS + 1800 ))
until curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; do
  kill -0 "$SERVER" 2>/dev/null || { tail -30 "$LOG" >&2; fail "the server exited before becoming ready - see $LOG"; }
  (( SECONDS < deadline )) || { tail -30 "$LOG" >&2; fault "server not ready after 30 minutes"; }
  sleep 5
done
note "ready after ${SECONDS}s"

# ---------------------------------------------------------------- measure and judge
note "measuring"
# Qwen3-Embedding is instruction-aware and its model card documents this exact query prefix.
# Measuring it without one would be running the model outside its documented usage and then
# reporting the result as a property of the server.
QPREFIX="${QPREFIX-Instruct: Given a question about a software governance system, retrieve the passage that answers it
Query: }"
"$VENV/bin/python" "$ROOT/docs/implement/probes/p5_measure.py" \
  --base-url "http://127.0.0.1:$PORT" \
  --embed-model embed --rerank-model rerank --pid "$SERVER" \
  --query-prefix "$QPREFIX"
rc=$?

note "server log, last lines that mention a model"
grep -iE "model|engine|dtype|warmup" "$LOG" | tail -6

case "$rc" in
  0) note "one process served both, and the reranker ranked"; exit 0 ;;
  2) fault "the server was unreachable from the measurement script" ;;
  *) fail "see the FAIL lines above. Two processes, a missing endpoint, or a reranker that
  answers without ranking all land here, and the record must say which." ;;
esac
