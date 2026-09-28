#!/usr/bin/env python3
"""Build a semantic model for a set of Atlan tables and write it to a file.

One request to Atlan. Nothing is created in your tenant: no context repository, no stored
artifact, no cloud-storage write. The model is built and returned, and what you do with the
file is up to you.

Standard library only, so there is nothing to install.

    export ATLAN_BASE_URL=https://<your-tenant>.atlan.com
    export ATLAN_API_KEY=<your api key>

    python build_semantic_model.py \
      --tables default/snowflake/1700000000/DB/SCHEMA/ORDERS \
               default/snowflake/1700000000/DB/SCHEMA/CUSTOMERS \
      --engine cortex \
      --out orders.yaml

Why an API key rather than the browser sign-in the rest of this plugin uses: this calls an
Atlan HTTP endpoint directly, and that endpoint authenticates with a key. Create one in Atlan
under Settings, then API tokens.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

# Names Atlan accepts, and what each one gives you.
ENGINES = {
    "atlan": "Atlan's own model, the form every other one is produced from",
    "cortex": "Snowflake Cortex Analyst semantic model",
    "snowflake": "the same thing as cortex",
    "databricks": "Databricks Unity Catalog metric view",
    "genie": "Databricks Genie space configuration",
    "dbt": "dbt MetricFlow semantic models",
}

TIMEOUT_SECONDS = 1800  # a real build reads the catalog for every table; minutes, not seconds


def build_url(base_url: str) -> str:
    """Where the build endpoint lives for this tenant.

    Normally the tenant's own gateway, which proxies the service that does the building. An
    ATLAN_WISDOM_URL override points at a service directly, which is how this path gets tested
    against a branch before it ships - without it the script can only be exercised against a
    deployed tenant, and a script that cannot be run before release is a script nobody has run.
    """
    override = os.environ.get("ATLAN_WISDOM_URL", "").strip().rstrip("/")
    if override:
        return f"{override}/semantic-model/build"
    return base_url.rstrip("/") + "/api/service/wisdom/v1/semantic-model/build"


def build(base_url: str, api_key: str, tables: list[str], engine: str, name: str) -> dict:
    url = build_url(base_url)
    payload = json.dumps({"tables": tables, "engine": engine, "name": name}).encode()
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "atlan-agent-toolkit/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = ""
        try:
            detail = json.load(error).get("detail", "")
        except Exception:
            detail = error.reason or ""
        if error.code == 401:
            raise SystemExit(
                "Atlan rejected the API key. Check ATLAN_API_KEY, and that it belongs to "
                f"{base_url}."
            )
        if error.code == 404:
            # The endpoint deliberately answers the same way for a table that does not exist
            # and one you cannot see, so the message says which names it could not find.
            raise SystemExit(f"Atlan could not find some of those tables. {detail}")
        raise SystemExit(f"Atlan returned {error.code}. {detail}")
    except urllib.error.URLError as error:
        raise SystemExit(f"Could not reach {base_url}. {error.reason}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a semantic model from Atlan catalog context.",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        required=True,
        help="Atlan table qualifiedNames, e.g. default/snowflake/1700000000/DB/SCHEMA/TABLE",
    )
    parser.add_argument(
        "--engine",
        default="cortex",
        choices=sorted(ENGINES),
        help="; ".join(f"{k}: {v}" for k, v in sorted(ENGINES.items())),
    )
    parser.add_argument("--out", required=True, help="Where to write the built model")
    parser.add_argument("--name", default="", help="Name for the model (optional)")
    args = parser.parse_args()

    base_url = os.environ.get("ATLAN_BASE_URL", "").strip()
    api_key = os.environ.get("ATLAN_API_KEY", "").strip()
    if not base_url or not api_key:
        raise SystemExit(
            "Set ATLAN_BASE_URL (https://<your-tenant>.atlan.com) and ATLAN_API_KEY."
        )

    result = build(base_url, api_key, list(args.tables), args.engine, args.name)

    content = result.get("content") or ""
    if not content:
        raise SystemExit(
            f"The build returned no file. {result.get('message') or 'No reason given.'}"
        )

    with open(args.out, "w") as handle:
        handle.write(content)

    modelled = result.get("tables_modelled") or []
    print(f"Wrote {args.out}")
    print(
        f"  {len(modelled)} of {len(args.tables)} tables modelled, "
        f"{len(content)} characters, {result.get('format') or 'yaml'}"
    )
    print("  Nothing was created in your Atlan tenant.")

    for failure in result.get("tables_failed") or []:
        print(
            f"  Could not model {failure.get('qualified_name')}: {failure.get('reason')}",
            file=sys.stderr,
        )
    for warning in result.get("warnings") or []:
        print(f"  Warning: {warning}", file=sys.stderr)
    dropped = result.get("dropped") or []
    if dropped:
        print(
            f"  {len(dropped)} item(s) could not be grounded in your catalog and were left "
            f"out. They are listed in the file.",
            file=sys.stderr,
        )

    if not result.get("success"):
        # The file is still written, because the tables that worked are worth having. The
        # non-zero exit stops a pipeline from treating a model with a missing table as clean.
        print(
            "The build did not cover everything that was asked for; see above.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
