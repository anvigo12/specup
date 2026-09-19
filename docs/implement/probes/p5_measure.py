#!/usr/bin/env python3
"""Measure one running model server against P5's question, and refuse a server that only looks alive.

P5 asks whether ONE process serves both the embedder and the reranker. Three things have to be
true, and the third is the one a naive check misses:

  1. Both models are registered on one server.
  2. /embeddings and /rerank both answer.
  3. **The reranker actually ranks.** Qwen3-Reranker is a Qwen3ForCausalLM, not a
     sequence-classification cross-encoder. Loading it through a generic CrossEncoder path gives
     a randomly initialised score head, which returns HTTP 200 and meaningless numbers. A probe
     that stopped at the status code would record `answered` for a server producing noise.

So two queries are reranked over a shared corpus, and each must place its own answer first. One
query is a 1-in-4 guess; two independent ones are 1-in-16, and the script prints every score so a
reader can judge rather than trust the assertion.

Exit 0 all three hold, 1 one of them does not, 2 the server could not be reached.

Called by p5.sh. Stdlib only, so it needs nothing the probe venv does not already have.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

CORPUS = [
    "validate_approvals.py runs git verify-commit --raw against the allowed-signers file to "
    "decide whether an approval is witnessed or merely claimed.",
    "Landlock binds inodes rather than path strings, so a symlink from a permitted directory is "
    "still caught by a read-only rule.",
    "Bananas are a good source of potassium and grow in tropical and subtropical climates.",
    "The Taskfile boundary test forbids a workflow, command or manifest from reaching the task "
    "runner, because distribution must not depend on a developer tool.",
]

# Each query's correct answer, by index into CORPUS. Two of them, so a lucky guess is 1 in 16.
QUERIES = [
    ("How does the validator decide an approval's commit signature is trustworthy?", 0),
    ("Does the filesystem policy catch a write that goes through a symlink?", 1),
]

BATCH = [
    "def build(): return 'ok'",
    "The gate evaluates six conditions and fails if any of them is unmet.",
    "REQ-CORE-0001 requires that governance state live on the filesystem.",
    "An approval binds content, not a human.",
    "Retrieval fuses a lexical index with a structural one before reranking.",
    "The audit reports exactly two reasons and a third means something broke.",
    "Every probe states what would falsify it before it runs.",
    "A check nobody has seen fail is not a check.",
]


def post(url: str, payload: dict, timeout: float = 600.0) -> tuple[dict, float]:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    start = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    return data, time.monotonic() - start


def get(url: str, timeout: float = 60.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def descendants(pid: int) -> list[int]:
    """Every live process whose parent chain reaches pid, pid included.

    Read from /proc rather than pgrep: the question is how many OS processes the server needs,
    and a pattern match would count the shell that launched it.
    """
    parent: dict[int, int] = {}
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat", "rb") as fh:
                fields = fh.read().rsplit(b")", 1)[1].split()
            parent[int(entry)] = int(fields[1])
        except (OSError, IndexError, ValueError):
            continue
    out, frontier = {pid}, [pid]
    while frontier:
        nxt = []
        for child, par in parent.items():
            if par in frontier and child not in out:
                out.add(child)
                nxt.append(child)
        frontier = nxt
    return sorted(p for p in out if p in parent or p == pid)


def rss_kb(pids: list[int]) -> int:
    total = 0
    for p in pids:
        try:
            with open(f"/proc/{p}/status") as fh:
                for line in fh:
                    if line.startswith("VmRSS:"):
                        total += int(line.split()[1])
                        break
        except OSError:
            continue
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:7997")
    ap.add_argument("--embed-model", required=True)
    ap.add_argument("--rerank-model", required=True)
    ap.add_argument("--pid", type=int, required=True, help="the server process id")
    ap.add_argument(
        "--query-prefix",
        default="",
        help="prepended to queries before embedding. Qwen3-Embedding is instruction-aware and "
        "its model card documents a query prefix; measuring it without one would be testing "
        "the model outside its documented usage and calling the result a finding.",
    )
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    failures: list[str] = []

    # ---------------------------------------------------------------- 1. one process, both models
    try:
        models = get(f"{base}/models")
    except (urllib.error.URLError, OSError) as exc:
        print(f"SETUP FAULT: {base}/models unreachable: {exc}", file=sys.stderr)
        return 2

    served = [m.get("id") for m in models.get("data", [])]
    print(f"  models registered on one server : {served}")
    # The server states each model's backend and capabilities. Recording them is the difference
    # between "both ids appear" and "both are loaded as the kind of model they are meant to be".
    for m in models.get("data", []):
        print(
            f"      {m.get('id'):8} backend={m.get('backend', '?')!r} "
            f"capabilities={sorted(m.get('capabilities') or [])}"
        )
    for wanted in (args.embed_model, args.rerank_model):
        if wanted not in served:
            failures.append(f"{wanted} is not registered")

    pids = descendants(args.pid)
    print(f"  server process tree             : {len(pids)} process(es) {pids}")
    print(f"  resident memory, whole tree     : {rss_kb(pids) / 1024:.0f} MiB")

    # ---------------------------------------------------------------- 2. both endpoints answer
    try:
        emb, emb_s = post(
            f"{base}/embeddings", {"model": args.embed_model, "input": BATCH}
        )
        dims = len(emb["data"][0]["embedding"])
        print(f"  /embeddings  {len(BATCH)} texts        : {emb_s:6.2f}s  {dims} dims")
    except Exception as exc:  # noqa: BLE001 - any failure here is the falsifier
        failures.append(f"/embeddings failed: {exc}")
        emb_s, dims = float("nan"), 0

    # The embedder has the same failure mode as the reranker, from the other direction.
    # Qwen3-Embedding needs last-token pooling ("pooling_mode_lasttoken": true). A server that
    # applied mean or cls pooling instead would return well-formed vectors of the right width
    # that retrieve badly, and dimension-checking would not notice. So retrieve with them.
    retrieved_correctly = 0
    try:
        texts = [args.query_prefix + q for q, _ in QUERIES] + CORPUS
        vecs, _ = post(f"{base}/embeddings", {"model": args.embed_model, "input": texts})
        rows = [d["embedding"] for d in sorted(vecs["data"], key=lambda d: d["index"])]
        qv, dv = rows[: len(QUERIES)], rows[len(QUERIES) :]
        print("\n  embedding retrieval (cosine over the same corpus)")
        for (query, answer), v in zip(QUERIES, qv):
            norm = lambda a: sum(x * x for x in a) ** 0.5 or 1.0  # noqa: E731
            sims = [
                (sum(x * y for x, y in zip(v, d)) / (norm(v) * norm(d)), i)
                for i, d in enumerate(dv)
            ]
            sims.sort(reverse=True)
            top = sims[0][1]
            retrieved_correctly += top == answer
            print(f"      query: {query[:60]}…")
            for s, i in sims:
                mark = "<-- expected" if i == answer else ""
                print(f"        [{i}] cos {s:+.4f}  {CORPUS[i][:46]}… {mark}")
            print(f"        top={top} expected={answer}  {'OK' if top == answer else 'WRONG'}")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"embedding retrieval check failed: {exc}")

    rerank_times = []
    ranked_correctly = 0
    for query, answer in QUERIES:
        try:
            res, secs = post(
                f"{base}/rerank",
                {"model": args.rerank_model, "query": query, "documents": CORPUS},
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(f"/rerank failed: {exc}")
            break
        rerank_times.append(secs)
        results = sorted(
            res.get("results", []), key=lambda r: r["relevance_score"], reverse=True
        )
        top = results[0]["index"] if results else -1
        ok = top == answer
        ranked_correctly += ok
        print(f"\n  /rerank  {len(CORPUS)} docs  {secs:6.2f}s   query: {query[:58]}…")
        for r in results:
            mark = "<-- expected" if r["index"] == answer else ""
            print(
                f"      [{r['index']}] {r['relevance_score']:+.6f}  "
                f"{CORPUS[r['index']][:52]}… {mark}"
            )
        print(f"      top={top} expected={answer}  {'OK' if ok else 'WRONG'}")

    # ---------------------------------------------------------------- 3. does it actually work
    # Two separate failures, kept separate. "Supports embedding but not reranking" is the
    # pre-registered falsifier; an embedder that returns vectors which do not retrieve is a
    # finding of its own and the write-up must be able to tell them apart.
    if rerank_times and ranked_correctly < len(QUERIES):
        failures.append(
            f"the reranker served {len(QUERIES)} queries and ranked {ranked_correctly} "
            "correctly - it answers but does not rank"
        )
    if retrieved_correctly < len(QUERIES):
        failures.append(
            f"the embedder returned vectors for {len(QUERIES)} queries and retrieved "
            f"{retrieved_correctly} correctly - check the pooling method"
        )

    print("\n  " + "-" * 72)
    summary = {
        "processes": len(pids),
        "rss_mib": round(rss_kb(pids) / 1024),
        "embed_seconds": round(emb_s, 3) if emb_s == emb_s else None,
        "embed_dims": dims,
        "rerank_seconds": [round(t, 3) for t in rerank_times],
        "queries_ranked_correctly": f"{ranked_correctly}/{len(QUERIES)}",
        "queries_retrieved_correctly": f"{retrieved_correctly}/{len(QUERIES)}",
    }
    print("  SUMMARY " + json.dumps(summary))

    if failures:
        for f in failures:
            print(f"  FAIL: {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
