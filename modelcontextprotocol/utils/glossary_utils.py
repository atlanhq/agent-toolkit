"""Simple helper utilities for glossary asset creation."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from client import get_atlan_client
from pyatlan.model.assets import Asset

logger = logging.getLogger(__name__)


def save_asset(asset: Asset, extra: Optional[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Persist *asset* to Atlan and return a compact success / error dict.

    The helper keeps glossary-tool code short while avoiding additional layers
    of indirection.  On success it returns::

        {"guid": "…", "name": "…", "qualified_name": "…", "success": True, "errors": [], …extra}

    and on failure::

        {"guid": None, "name": "…", "qualified_name": None, "success": False, "errors": ["msg"], …extra}
    """

    extra = extra or {}

    try:
        client = get_atlan_client()
        response = client.asset.save(asset)
        guid = next(iter(response.guid_assignments.values()), None) if response else None

        return {
            "guid": guid,
            "name": asset.name,
            "qualified_name": asset.qualified_name,
            "success": True,
            "errors": [],
            **extra,
        }

    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error saving %s '%s': %s", asset.type_name, asset.name, exc)
        return {
            "guid": None,
            "name": asset.name,
            "qualified_name": None,
            "success": False,
            "errors": [str(exc)],
            **extra,
        }
