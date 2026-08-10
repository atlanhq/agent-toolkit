"""get_context — retrieve the analyst context needed to answer a business question correctly.

This is a thin client over the Context Studio backend (`POST {base}/get-context`). Retrieval
logic, the query-history corpus and the glossary credentials all stay server-side, so the ranking
can be iterated and re-measured without redeploying the MCP server.

Why a backend rather than doing it here: the corpus is customer query text held in object storage
and the ranking is under an accuracy contract — the backend carries a parity test asserting its
scorer reproduces the benchmarked reference exactly (ranked row identity and scores). Splitting
that logic across two repos would let the shipped ranking drift from the measured one.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_S = int(os.environ.get("GET_CONTEXT_TIMEOUT_S", "60"))


def _base_url() -> str:
    base = (
        os.environ.get("APP_SEMANTIC_EVALS_BASE_URL")
        or os.environ.get("GET_CONTEXT_BASE_URL")
        or ""
    ).strip().rstrip("/")
    if not base:
        raise RuntimeError(
            "get_context backend is not configured: set APP_SEMANTIC_EVALS_BASE_URL "
            "(or GET_CONTEXT_BASE_URL) to the Context Studio service"
        )
    return base


def get_context(
    question: str,
    tables: Optional[List[str]] = None,
    pack: Optional[str] = None,
    k: int = 5,
    tiers: Optional[List[str]] = None,
    include_history: bool = True,
) -> Dict[str, Any]:
    """Fetch composed context for a business question.

    Args:
        question: The business question, verbatim.
        tables: Fully-qualified tables to scope to. Omit to search the whole pack.
        pack: Context pack id (defaults to the backend's configured pack).
        k: Number of real analyst queries to include.
        tiers: Glossary tiers to include (conventions, governed, mined).
        include_history: Set False for conventions/definitions only.

    Returns:
        dict with `context` (the text to give the model), plus `counts`, `layers`,
        `corpus_manifest` and `warnings` for observability.
    """
    payload: Dict[str, Any] = {
        "question": question,
        "k": k,
        "include_history": include_history,
    }
    if tables:
        payload["tables"] = tables
    if pack:
        payload["pack"] = pack
    if tiers:
        payload["tiers"] = tiers

    url = f"{_base_url()}/get-context"
    logger.info(f"get_context: POST {url} (tables={len(tables or [])}, k={k})")
    # httpx, not requests: it already ships with the server's fastmcp dependency, so the tool adds
    # no new dependency to the MCP image.
    try:
        r = httpx.post(url, json=payload, timeout=DEFAULT_TIMEOUT_S)
    except httpx.HTTPError as e:
        logger.error(f"get_context: backend unreachable: {e}")
        return {
            "context": "",
            "error": f"context backend unreachable: {type(e).__name__}",
            "warnings": ["no context retrieved"],
        }
    if r.status_code >= 300:
        logger.error(f"get_context: backend {r.status_code}: {r.text[:300]}")
        return {
            "context": "",
            "error": f"context backend returned {r.status_code}",
            "warnings": [r.text[:300]],
        }
    data = r.json()
    logger.info(
        f"get_context: {data.get('counts')} layers, {len(data.get('context') or '')} chars"
    )
    return data


def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{_base_url()}{path}"
    try:
        r = httpx.post(url, json=payload, timeout=DEFAULT_TIMEOUT_S)
    except httpx.HTTPError as e:
        logger.error(f"{path}: backend unreachable: {e}")
        return {"error": f"context backend unreachable: {type(e).__name__}"}
    if r.status_code >= 300:
        logger.error(f"{path}: backend {r.status_code}: {r.text[:300]}")
        return {"error": f"context backend returned {r.status_code}",
                "detail": r.text[:300]}
    return r.json()


def search_metrics(query: str, k: int = 5) -> Dict[str, Any]:
    """Search the governed metric glossary. Returns a ranked shortlist of metric INDEX cards
    (id, name, definition, synonyms, variant count, tables) — no SQL; call get_metric for that.

    The glossary holds the certified context layer in wikilink form: one lean index term per
    business concept, whose README carries ONE canonical execution-verified SQL and [[guid]]
    links to variant terms (the customer's BI definitions and real analyst queries) and to
    sibling metrics on the same tables.
    """
    return _post("/get-context/search-metrics", {"query": query, "k": k})


def get_metric(id_or_name: str) -> Dict[str, Any]:
    """Get ONE glossary term's README by GUID (from search_metrics or a [[guid]] wikilink) or
    exact name. An INDEX term gives the concept's definition, population/grain decisions, one
    canonical execution-verified SQL, and wikilinks to its variants and sibling metrics. A
    VARIANT term gives that variant's exact definition. Open a variant only when its grain,
    filter or time-intelligence fits the question better than the index's primary example; for
    multi-metric questions (e.g. a full funnel), open EACH relevant sibling index — their
    populations and channel scopings differ.
    """
    return _post("/get-context/metric", {"id_or_name": id_or_name})
