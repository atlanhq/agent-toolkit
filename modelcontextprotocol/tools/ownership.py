"""Ownership utilities for user and group suggestion and resolution."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from difflib import get_close_matches, SequenceMatcher

from client import get_atlan_client

logger = logging.getLogger(__name__)


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def suggest_usernames(query: str, max_suggestions: int = 5) -> List[str]:
    """Suggest usernames similar to *query* (case-insensitive)."""

    client = get_atlan_client()
    batch_size = 100
    usernames: List[str] = []
    offset = 0

    while True:
        resp = client.user.get(limit=batch_size, offset=offset)
        records = resp.records if resp and resp.records else []
        if not records:
            break
        usernames.extend(
            u.username for u in records if getattr(u, "username", None)
        )
        offset += batch_size

    if query in usernames:
        return [query]
    suggestions = get_close_matches(query, usernames, n=max_suggestions, cutoff=0.6)
    suggestions.sort(key=lambda u: _similarity(query, u), reverse=True)
    return suggestions


def suggest_groups(query: str, max_suggestions: int = 5) -> List[str]:
    """Suggest group aliases similar to *query*."""

    client = get_atlan_client()
    batch_size = 100
    groups: List[str] = []
    offset = 0

    while True:
        resp = client.group.get(limit=batch_size, offset=offset)
        records = resp.records if resp and resp.records else []
        if not records:
            break
        groups.extend(g.alias for g in records if getattr(g, "alias", None))
        offset += batch_size

    if query in groups:
        return [query]
    suggestions = get_close_matches(query, groups, n=max_suggestions, cutoff=0.6)
    suggestions.sort(key=lambda g: _similarity(query, g), reverse=True)
    return suggestions 