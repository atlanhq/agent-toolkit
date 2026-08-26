#!/usr/bin/env python3
"""build-view companion — deterministic call to the governed semantic-model build.

Stdlib only. POSTs {tables, engine, name} to the governed build endpoint, saves the
returned model YAML, and prints a one-line summary. This is the script the
build-view skill runs, so the endpoint call, auth, timeout, and error handling are
identical every time (not improvised by the model).

Endpoint resolution (first that is set wins):
  --endpoint <url>                     explicit
  $ATLAN_BUILD_ENDPOINT                override (e.g. the local mock)
  DEFAULT_ENDPOINT constant below      the hosted governed endpoint (if baked)

Auth: sends `Authorization: Bearer $ATLAN_API_KEY` when that env var is set (the
hosted endpoint requires it; the local mock ignores it). Never prints the value.

Usage:
  build_model.py --tables @tables.json --engine cortex --name gtm --out model.yaml
  # --tables entries are Atlan qualifiedNames WITH the connection prefix (not DB/SCHEMA/TABLE):
  build_model.py --tables default/snowflake/<conn>/DB/SCHEMA/DIM_ACCOUNTS --engine cortex --name gtm --out model.yaml
"""

import argparse
import json
import os
import ssl
import sys
import urllib.request
import urllib.error

# The governed build endpoint is your Atlan tenant's store-nothing
# `/semantic-model/build` API. Set it via $ATLAN_BUILD_ENDPOINT or --endpoint;
# auth is Bearer $ATLAN_API_KEY.
DEFAULT_ENDPOINT = ""

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def resolve_endpoint(cli):
    return (
        cli
        or os.environ.get("ATLAN_BUILD_ENDPOINT")
        or DEFAULT_ENDPOINT
        or sys.exit(
            "ERROR: no build endpoint — pass --endpoint, set $ATLAN_BUILD_ENDPOINT, "
            "point --endpoint at your tenant's governed /semantic-model/build endpoint."
        )
    )


def load_tables(val):
    if val.startswith("@"):
        data = json.load(open(val[1:]))
        return data if isinstance(data, list) else data.get("tables", [])
    return [t.strip() for t in val.split(",") if t.strip()]


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--tables",
        required=True,
        help="comma list or @file.json (list or {tables:[...]})",
    )
    p.add_argument(
        "--engine", default="cortex", choices=["cortex", "genie", "databricks"]
    )
    p.add_argument("--name", required=True)
    p.add_argument("--out", required=True, help="path to write the returned model YAML")
    p.add_argument("--endpoint", default=None)
    p.add_argument(
        "--timeout", type=int, default=400, help="seconds; real build takes 4-5 min"
    )
    a = p.parse_args()

    url = resolve_endpoint(a.endpoint)
    tables = load_tables(a.tables)
    if not tables:
        sys.exit("ERROR: no tables resolved from --tables")

    body = json.dumps({"tables": tables, "engine": a.engine, "name": a.name}).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header(
        "User-Agent", UA
    )  # Atlan is behind Cloudflare (1010-blocks default urllib UA)
    key = os.environ.get("ATLAN_API_KEY")
    if key:
        req.add_header("Authorization", "Bearer " + key)  # value never printed

    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=a.timeout) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR: build endpoint returned HTTP {e.code} (body withheld)")
    except Exception as e:
        sys.exit(f"ERROR: build call failed: {type(e).__name__}: {e}")

    if not resp.get("success") or not resp.get("content"):
        sys.exit(
            f"ERROR: build did not return a model (message: {resp.get('message','?')})"
        )

    open(a.out, "w").write(resp["content"])
    val = resp.get("validation", {})

    # `dropped` is a structured list (per-entry section / entry_name / reason).
    # build-view ends at the handoff, so the caller won't come back for a diagnosis
    # pass — the reasons are what they need to act (fix the source SQL or accept the
    # gap). Print a per-section count and write the full list next to --out so
    # nothing is lost while the summary stays short.
    dropped = resp.get("dropped", []) or []
    counts = {}
    for d in dropped:
        sec = (d.get("section") or "?") if isinstance(d, dict) else "?"
        counts[sec] = counts.get(sec, 0) + 1
    dropped_by_section = (
        ", ".join(f"{n} {s}" for s, n in sorted(counts.items())) or "none"
    )
    if dropped:
        with open(a.out + ".dropped.json", "w") as f:
            json.dump(dropped, f, indent=2)

    print(
        f"built {a.engine} model → {a.out}  "
        f"tables_modelled={len(resp.get('tables_modelled', []))}  "
        f"validation={val.get('status', '?') if isinstance(val, dict) else val}"
    )
    print(
        f"  dropped ({len(dropped)}): {dropped_by_section}"
        + (f"  · full list → {a.out}.dropped.json" if dropped else "")
    )
    if isinstance(val, dict) and val.get("status") == "skipped":
        print(
            "  note: validation skipped (no engine reachable to compile-check) — carry forward"
        )


if __name__ == "__main__":
    main()
