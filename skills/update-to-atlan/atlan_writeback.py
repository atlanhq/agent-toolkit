#!/usr/bin/env python3
"""atlan_writeback.py — write SQL-Intelligence context back to Atlan over raw REST.

Stdlib only (json + urllib). Replaces the plugin's bundled atlan-sqlinsight write-MCP.

Auth: reads ATLAN_BASE_URL (or ATLAN_API_URL) and ATLAN_API_KEY from the environment.
      The API key value is NEVER printed or logged.

Endpoints:
  POST   /api/meta/entity/bulk          -> create/update
  GET    /api/meta/entity/guid/{guid}   -> read-back (status + attributes)
  DELETE /api/meta/entity/guid/{guid}   -> delete
  POST   /api/meta/search/indexsearch   -> sweep by name prefix

Five write types (all writes to Atlan go through this script — no MCP dependency):
  filter         -> SqlInsightFilter          (QN = {columnQN}/filter/md5(operator))
  relationship   -> SqlInsightJoin            (QN = {srcTableQN}/join/md5(joinedQN|sortedPairs|joinType))
  popular_query  -> SqlInsightBusinessQuestion(QN = {tableQN}/question/md5(questionText))
  description    -> update an asset's userDescription (resolves guid first; dbt `description` untouched)
  glossary_term  -> create AtlasGlossaryTerm anchored to a glossary (+ optional column meanings edge)

Canonical identity: every qualifiedName ends in a FULL 32-hex lowercase
md5 of its own content, derived byte-for-byte the way the SQL-Intelligence miner and the
UI author it (matching the miner's identity function and RFC-1321 md5 vectors). Reproducing it exactly is what makes a script-written row
CONVERGE with the miner/UI-written row instead of duplicating it. Each write also
dual-anchors by GUID via relationshipAttributes so the row renders on the asset page.

CLI:
  write  --type filter|relationship|popular_query|description|glossary_term --payload <json|@file>
  verify --guid <g>
  delete --guid <g> [--hard]   # --hard purges (true 404); default = soft (status=DELETED)
  typedefs [--grep SqlInsight]   # dump SqlInsight* entity defs to confirm popular_query
  sweep  --prefix ttd_           # find leftover test entities across the 3 types
"""

import json
import os
import sys
import ssl
import hashlib
import urllib.request
import urllib.error

# ----- popular-query type confirmed against the tenant typedef -----
# SqlInsightBusinessQuestion is a real entityDef (superType SqlInsight -> Catalog).
# Confirmed attrs: sqlInsightBusinessQuestionText, sqlInsightBusinessQuestionCanonicalSQL.
# Its dataset is anchored via the `sqlInsightDataset` RELATIONSHIP (by GUID), not a
# qualifiedName string attribute.
# NOTE: the qualifiedName segment used here was previously WRONG (/businessQuestion/
# + a sha256[:16] hash). It is now aligned to the canonical identity:
# {tableQN}/question/md5(questionText) with a full 32-hex md5, so a script-written
# question converges with the miner/UI-written one.
POPULAR_QUERY_TYPENAME = "SqlInsightBusinessQuestion"
POPULAR_QUERY_VALIDATED = True

# Atlan sits behind Cloudflare, which 1010-blocks the default Python-urllib
# User-Agent. A browser-like UA is REQUIRED or every call 403s ("browser signature").
_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _cfg():
    base = os.environ.get("ATLAN_BASE_URL") or os.environ.get("ATLAN_API_URL")
    key = os.environ.get("ATLAN_API_KEY")
    if not base or not key:
        sys.exit(
            "ERROR: set ATLAN_BASE_URL (or ATLAN_API_URL) and ATLAN_API_KEY in env"
        )
    return base.rstrip("/"), key


def _req(method, path, body=None):
    base, key = _cfg()
    url = base + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", "Bearer " + key)  # value never surfaced
    r.add_header("Content-Type", "application/json")
    r.add_header("Accept", "application/json")
    r.add_header("User-Agent", _UA)  # REQUIRED: dodges Cloudflare 1010 bot-block
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(r, context=ctx, timeout=60) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"_raw": raw}


def _md5(s):
    """FULL 32-hex lowercase md5 (UTF-8), matching the miner's identity function byte-for-byte.
    md5 here names a row and guards nothing — it is the miner's identity function."""
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def _bare(qn):
    """Bare column name = last '/'-segment of a column qualifiedName."""
    return qn.rsplit("/", 1)[-1]


def _anchor(entity, rel_map):
    """Dual-anchor by GUID: attach relationshipAttributes for each non-null objectId.
    Each value is an AtlasObjectId dict {'guid': ..., 'typeName': ...} or None."""
    ra = {k: v for k, v in rel_map.items() if v}
    if ra:
        entity["relationshipAttributes"] = ra


# --------------------------- builders ---------------------------


def build_filter(p):
    """SqlInsightFilter. Canonical QN = {columnQN}/filter/md5(operator).
    payload: column_qn, operator, name;
             optional: predicate_sql, dataset_qn, when_to_use, common_values (list),
                       column_guid (objectId; else resolved for the sqlInsightColumn edge)."""
    col = p["column_qn"]
    op = p["operator"]
    qn = p.get("qualifiedName") or f"{col}/filter/{_md5(op)}"
    attrs = {
        "qualifiedName": qn,
        "name": p["name"],
        "sqlInsightFilterColumnQualifiedName": col,
        "sqlInsightFilterOperator": op,
        "sqlInsightFilterPredicateSQL": p.get("predicate_sql", ""),
        "sqlInsightFilterWhenToUse": p.get("when_to_use", ""),
    }
    if p.get("dataset_qn"):
        attrs["sqlInsightFilterDatasetQualifiedName"] = p["dataset_qn"]
    if p.get("common_values"):
        attrs["sqlInsightFilterCommonValues"] = p["common_values"]
    entity = {"typeName": "SqlInsightFilter", "attributes": attrs}
    _anchor(entity, {"sqlInsightColumn": p.get("column_guid")})
    return entity, ("qualifiedName", qn), ("sqlInsightFilterOperator", op)


def build_relationship(p):
    """SqlInsightJoin. Canonical QN = {srcTableQN}/join/md5("{joinedTableQN}|{sortedPairs}|{joinType}"),
    where sortedPairs joins BARE "{srcColName}={joinedColName}" with commas ORDERED BY
    THE SOURCE COLUMN ONLY (not by the formatted pair string). That matches the miner --
    `STRING_AGG(cp.source || '=' || cp.joined, ',' ORDER BY cp.source)` in the
    sql_intelligence DAG -- and pyatlan's SqlInsightJoin.generate_qualified_name. Sorting
    the formatted strings instead diverges whenever one source column is a prefix of
    another followed by a digit (ORDER_ID / ORDER_ID2), because '=' is 0x3D and digits are
    0x30-0x39; the md5 then differs and the write DUPLICATES the miner's row instead of
    converging on it. The sort is stable, so pairs sharing a source column keep the
    caller's order, as pyatlan does. The source table QN is the PREFIX, not part of the hash.
    payload: source_dataset_qn, joined_dataset_qn, join_type,
             column_pairs:[{source_column_qn, joined_column_qn}]; optional: name,
             cardinality, source_dataset_guid / joined_dataset_guid (objectIds; else
             resolved for the sqlInsightSourceDataset / sqlInsightJoinedDataset edges)."""
    src = p["source_dataset_qn"]
    jnd = p["joined_dataset_qn"]
    jtype = p["join_type"]
    _bare_pairs = [
        (
            cp.get("source_column") or _bare(cp["source_column_qn"]),
            cp.get("joined_column") or _bare(cp["joined_column_qn"]),
        )
        for cp in p["column_pairs"]
    ]
    sorted_pairs = ",".join(
        f"{src_col}={jnd_col}"
        for src_col, jnd_col in sorted(_bare_pairs, key=lambda pair: pair[0])
    )
    qn = p.get("qualifiedName") or f"{src}/join/{_md5(f'{jnd}|{sorted_pairs}|{jtype}')}"
    pairs = []
    for cp in p["column_pairs"]:
        pairs.append(
            {
                "typeName": "SqlInsightJoinColumnPair",
                "attributes": {
                    "sqlInsightJoinColumnPairSourceColumnQualifiedName": cp[
                        "source_column_qn"
                    ],
                    "sqlInsightJoinColumnPairJoinedColumnQualifiedName": cp[
                        "joined_column_qn"
                    ],
                },
            }
        )
    attrs = {
        "qualifiedName": qn,
        "name": p.get("name", f"join_{_md5(f'{jnd}|{sorted_pairs}|{jtype}')[:12]}"),
        "sqlInsightJoinSourceDatasetQualifiedName": src,
        "sqlInsightJoinJoinedDatasetQualifiedName": jnd,
        "sqlInsightJoinType": jtype,
        "sqlInsightJoinColumnPairs": pairs,
    }
    if p.get("cardinality"):
        attrs["sqlInsightJoinCardinality"] = p["cardinality"]
    entity = {"typeName": "SqlInsightJoin", "attributes": attrs}
    _anchor(
        entity,
        {
            "sqlInsightSourceDataset": p.get("source_dataset_guid"),
            "sqlInsightJoinedDataset": p.get("joined_dataset_guid"),
        },
    )
    return entity, ("qualifiedName", qn), ("sqlInsightJoinType", jtype)


def build_popular_query(p):
    """SqlInsightBusinessQuestion. Canonical QN = {tableQN}/question/md5(questionText).
    Dataset is anchored via the sqlInsightDataset RELATIONSHIP (by GUID), not a QN attr.
    payload: dataset_qn, question, sql; optional: name,
             dataset_guid (objectId; else resolved for the sqlInsightDataset edge)."""
    ds = p["dataset_qn"]
    q = p["question"]
    qn = p.get("qualifiedName") or f"{ds}/question/{_md5(q)}"
    entity = {
        "typeName": POPULAR_QUERY_TYPENAME,
        "attributes": {
            "qualifiedName": qn,
            "name": p.get("name", q[:60]),
            "sqlInsightBusinessQuestionText": q,
            "sqlInsightBusinessQuestionCanonicalSQL": p["sql"],
        },
    }
    _anchor(entity, {"sqlInsightDataset": p.get("dataset_guid")})
    return entity, ("qualifiedName", qn), ("sqlInsightBusinessQuestionText", q)


def build_description(p):
    """Update an existing asset's userDescription (the governed prose the model
    added). We resolve the asset's guid + typeName first and send them, so this is
    an UPDATE to the existing entity, never a partial create (fixes the earlier
    'guid Field required' error). The dbt-synced `description` is left untouched.
    payload: asset_qn, user_description; optional asset_guid, asset_type."""
    qn = p["asset_qn"]
    if p.get("asset_guid") and p.get("asset_type"):
        obj = {"guid": p["asset_guid"], "typeName": p["asset_type"]}
    else:
        obj = _resolve_objid(
            qn, ("Column",) + _DATASET_TYPES
        )  # asset types only, never a lineage Process
    if not obj:
        sys.exit(f"ERROR: could not resolve asset for description update: {qn}")
    # Atlas requires `name` on an asset update; read the current name and preserve it
    # (so we update userDescription without renaming the asset).
    _, cur = op_verify(obj["guid"], quiet=True)
    name = p.get("name") or cur.get("attributes", {}).get("name") or _bare(qn)
    entity = {
        "typeName": obj["typeName"],
        "guid": obj["guid"],
        "attributes": {
            "qualifiedName": qn,
            "name": name,
            "userDescription": p["user_description"],
        },
    }
    return entity, ("qualifiedName", qn), ("userDescription", p["user_description"])


BUILDERS = {
    "filter": build_filter,
    "relationship": build_relationship,
    "popular_query": build_popular_query,
    "description": build_description,
}


# --------------------------- operations ---------------------------


def _extract_guid(resp):
    ga = resp.get("guidAssignments") or {}
    if ga:
        return list(ga.values())[0]
    mut = resp.get("mutatedEntities") or {}
    for k in ("CREATE", "UPDATE"):
        if mut.get(k):
            return mut[k][0].get("guid")
    return None


def _resolve_objid(qn, want_types=None):
    """Resolve a qualifiedName to an AtlasObjectId {'guid','typeName'} via indexsearch.
    Constrains to want_types (tuple of acceptable typeNames) so a QN also carried by a
    lineage Process (or other non-asset) isn't picked over the real Table/Column — the
    join/question/filter relationshipDefs require a specific end type, and a wrong-typed
    objectId 400s. Returns None if nothing of the wanted type resolves."""
    body = {
        "dsl": {
            "size": 10,
            "query": {"bool": {"must": [{"term": {"qualifiedName": qn}}]}},
        },
        "attributes": ["qualifiedName"],
    }
    _, resp = _req("POST", "/api/meta/search/indexsearch", body)
    ents = [e for e in (resp.get("entities") or []) if e.get("guid")]
    if want_types:
        ents = [e for e in ents if e.get("typeName") in want_types]
    for e in ents:
        return {"guid": e["guid"], "typeName": e.get("typeName")}
    return None


# a "dataset" anchor may be any of these SQL asset types (never a lineage Process)
_DATASET_TYPES = ("Table", "View", "MaterialisedView", "SnowflakeDynamicTable")
# qualifiedName payload key -> objectId payload key + acceptable typeNames for the anchor
_ANCHOR_RESOLVE = {
    "filter": [("column_qn", "column_guid", ("Column",))],
    "relationship": [
        ("source_dataset_qn", "source_dataset_guid", _DATASET_TYPES),
        ("joined_dataset_qn", "joined_dataset_guid", _DATASET_TYPES),
    ],
    "popular_query": [("dataset_qn", "dataset_guid", _DATASET_TYPES)],
}


def op_glossary_term(payload):
    """Create an AtlasGlossaryTerm via Atlan's dedicated glossary endpoint (which
    auto-assigns the term's qualifiedName — the raw entity/bulk API rejects a term
    without one). Optionally bind the term to a column (the `meanings` edge).
    payload: name, glossary_qn (or glossary_guid); optional description,
             assign_column_qn."""
    if payload.get("glossary_guid"):
        gguid = payload["glossary_guid"]
    else:
        gobj = _resolve_objid(payload["glossary_qn"], ("AtlasGlossary",))
        if not gobj:
            sys.exit(f"ERROR: could not resolve glossary: {payload.get('glossary_qn')}")
        gguid = gobj["guid"]
    body = {"name": payload["name"], "anchor": {"glossaryGuid": gguid}}
    if payload.get("description"):
        body["longDescription"] = payload["description"]
    status, resp = _req("POST", "/api/meta/glossary/term", body)
    guid = resp.get("guid")
    out = {"http_status": status, "guid": guid, "glossary_guid": gguid}
    if guid:
        _, ver = op_verify(guid, quiet=True)
        out["status"] = ver.get("status")
        out["qualifiedName"] = ver.get("attributes", {}).get("qualifiedName")
        out["verbatim_ok"] = ver.get("attributes", {}).get("name") == payload["name"]
        if payload.get("assign_column_qn"):
            col = _resolve_objid(payload["assign_column_qn"], ("Column",))
            if col:
                # APPEND to the column's existing meanings (bulk `meanings` is set-replace,
                # so read current terms first and merge — never drop an existing term).
                _, cver = op_verify(col["guid"], quiet=True)
                existing = [
                    {
                        "guid": m["guid"],
                        "typeName": m.get("typeName", "AtlasGlossaryTerm"),
                    }
                    for m in (
                        cver.get("relationshipAttributes", {}).get("meanings") or []
                    )
                    if m.get("guid")
                ]
                merged = existing + (
                    [{"guid": guid, "typeName": "AtlasGlossaryTerm"}]
                    if guid not in [m["guid"] for m in existing]
                    else []
                )
                assign = {
                    "typeName": col["typeName"],
                    "guid": col["guid"],
                    "attributes": {"qualifiedName": payload["assign_column_qn"]},
                    "relationshipAttributes": {"meanings": merged},
                }
                as_status, _ = _req(
                    "POST", "/api/meta/entity/bulk", {"entities": [assign]}
                )
                out["assigned_to_column"] = {
                    "qn": payload["assign_column_qn"],
                    "ok": as_status in (200, 204),
                    "meanings_after": len(merged),
                }
            else:
                out["assigned_to_column"] = {
                    "qn": payload["assign_column_qn"],
                    "error": "column not resolved",
                }
    else:
        out["error"] = resp
    print(json.dumps(out, indent=2))
    return out


def op_write(type_, payload):
    if type_ == "glossary_term":
        return op_glossary_term(payload)
    if type_ == "popular_query" and not POPULAR_QUERY_VALIDATED:
        sys.stderr.write(
            "WARNING: popular_query typeName/attrs are UNVALIDATED — confirm via "
            "`typedefs` against your Atlan tenant before trusting this write.\n"
        )
    # Dual-anchoring: resolve each anchor QN -> objectId unless already supplied.
    for qn_key, guid_key, want_types in _ANCHOR_RESOLVE.get(type_, []):
        if guid_key not in payload and payload.get(qn_key):
            payload[guid_key] = _resolve_objid(payload[qn_key], want_types)
    entity, qn_key, verbatim_key = BUILDERS[type_](payload)
    request_body = {"entities": [entity]}
    status, resp = _req("POST", "/api/meta/entity/bulk", request_body)
    # _extract_guid returns None on an idempotent (no-change) update; fall back to the
    # guid the builder already resolved (e.g. `description` updates) so verify still runs.
    guid = _extract_guid(resp) or entity.get("guid")
    out = {
        "http_status": status,
        "guid": guid,
        # glossary terms get an Atlan-assigned qualifiedName; filled from read-back below
        "qualifiedName": entity["attributes"].get("qualifiedName"),
    }
    out["relationshipAttributes_sent"] = list(
        (entity.get("relationshipAttributes") or {}).keys()
    )
    if guid:
        vs, ver = op_verify(guid, quiet=True)
        out["status"] = ver.get("status")
        out["verbatim_ok"] = (
            ver.get("attributes", {}).get(verbatim_key[0]) == verbatim_key[1]
        )
        if not out["qualifiedName"]:
            out["qualifiedName"] = ver.get("attributes", {}).get("qualifiedName")
        # Edge is populated when the read-back relationshipAttributes carry a guid.
        rel = ver.get("relationshipAttributes", {}) or {}
        out["edges_populated"] = {
            k: bool((rel.get(k) or {}).get("guid"))
            for k in (entity.get("relationshipAttributes") or {})
        }
    else:
        out["error"] = resp
    # Full request+response evidence dump when WRITEBACK_DEBUG=<path> is set.
    dbg = os.environ.get("WRITEBACK_DEBUG")
    if dbg:
        with open(dbg, "w") as f:
            json.dump(
                {
                    "type": type_,
                    "request": request_body,
                    "create_http_status": status,
                    "create_response": resp,
                    "summary": out,
                },
                f,
                indent=2,
            )
    print(json.dumps(out, indent=2))
    return out


def op_verify(guid, quiet=False):
    status, resp = _req("GET", f"/api/meta/entity/guid/{guid}")
    ent = resp.get("entity") or {}
    info = {
        "http_status": status,
        "guid": guid,
        "status": ent.get("status"),
        "typeName": ent.get("typeName"),
        "attributes": ent.get("attributes", {}),
        "relationshipAttributes": ent.get("relationshipAttributes", {}),
    }
    if not quiet:
        print(json.dumps(info, indent=2))
    return status, info


def op_delete(guid, hard=False):
    # Default (soft) delete flips status ACTIVE->DELETED but the entity-GET still
    # resolves (HTTP 200, status=DELETED) — this tenant retains soft-deleted rows.
    # --hard uses deleteType=PURGE so a subsequent GET is a true 404
    # (ATLAS-404-00-005). PURGE works whether the entity is ACTIVE or already
    # soft-DELETED; deleteType=HARD is a no-op on an already-soft-deleted row.
    path = f"/api/meta/entity/guid/{guid}"
    if hard:
        path += "?deleteType=PURGE"
    status, resp = _req("DELETE", path)
    print(
        json.dumps(
            {"http_status": status, "guid": guid, "hard": hard, "response": resp},
            indent=2,
        )
    )


def op_typedefs(grep):
    # NB: the ?type=entitydef filter can return empty on some tenants — fetch all
    # typedefs and filter entityDefs client-side.
    status, resp = _req("GET", "/api/meta/types/typedefs")
    defs = resp.get("entityDefs", [])
    hits = [d for d in defs if grep.lower() in d.get("name", "").lower()]
    for d in hits:
        print(d["name"], "->", [a["name"] for a in d.get("attributeDefs", [])])
    if not hits:
        print(f"(no entity typedef matching {grep!r}) http={status}")


def op_sweep(prefix):
    types = ["SqlInsightFilter", "SqlInsightJoin", POPULAR_QUERY_TYPENAME]
    total = 0
    for t in types:
        body = {
            "dsl": {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"__typeName.keyword": t}},
                            {"prefix": {"name.keyword": prefix}},
                        ]
                    }
                }
            }
        }
        status, resp = _req("POST", "/api/meta/search/indexsearch", body)
        ents = resp.get("entities", []) or []
        active = [e for e in ents if e.get("status") == "ACTIVE"]
        total += len(active)
        print(f"{t}: {len(active)} ACTIVE with name prefix {prefix!r}")
        for e in active:
            print("  ", e.get("guid"), e.get("attributes", {}).get("name"))
    print(f"TOTAL active test entities: {total}")


def _load_payload(arg):
    if arg.startswith("@"):
        with open(arg[1:]) as f:
            return json.load(f)
    return json.loads(arg)


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd = argv[0]
    args = dict(zip(argv[1::2], argv[2::2]))
    if cmd == "write":
        op_write(args["--type"], _load_payload(args["--payload"]))
    elif cmd == "verify":
        op_verify(args["--guid"])
    elif cmd == "delete":
        op_delete(args["--guid"], hard=("--hard" in argv))
    elif cmd == "typedefs":
        op_typedefs(args.get("--grep", "SqlInsight"))
    elif cmd == "sweep":
        op_sweep(args.get("--prefix", "ttd_"))
    else:
        sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main(sys.argv[1:])
