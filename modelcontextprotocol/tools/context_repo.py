"""ContextRepository + Skill + SkillArtifact bundle persistence.

Mirrors the canonical agent-bundle flow at
`skills/agent-bundle/scripts/publish_to_atlan.py`:

    1. Paired create — ContextRepository AND its contextOutputSkill go to
       /api/meta/entity/bulk in a single request with negative guids so the
       server resolves the cross-reference atomically.
    2. Per artifact — TWO writes:
         a. Entity row to /api/meta/entity/bulk with the six required UI
            fields (name, displayName, filePath, fileType, description,
            skillArtifactRepoGuid) plus the skillSource relationship.
         b. Body bytes to S3 via /api/service/files/presignedUrl + PUT.
    3. Optional activate — flips contextRepositoryLifecycleStatus to ACTIVE
       and certificateStatus to VERIFIED on both repo and skill.

Idempotent: if an artifact with the same displayName already exists under
the bundle's Skill, its qualifiedName is reused (so re-publishing overwrites
the body in place instead of producing duplicates).
"""

from __future__ import annotations

import logging
import secrets
import string
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

from pyatlan.client.constants import API, HTTPMethod
from pyatlan.model.assets import Skill
from pyatlan.utils import EndPoint

from client import get_atlan_client
from utils import save_assets
from .models import (
    ContextBundleArtifactSpec,
    ContextRepositorySpec,
    SkillSpec,
)

logger = logging.getLogger(__name__)

S3_PREFIX = "s3://atlan-bucket/context-repos"

BULK_ENTITY = API("entity/bulk", HTTPMethod.POST, HTTPStatus.OK, endpoint=EndPoint.ATLAS)
PRESIGNED_URL = API(
    "files/presignedUrl", HTTPMethod.POST, HTTPStatus.OK, endpoint=EndPoint.HERACLES
)
INDEX_SEARCH = API(
    "search/indexsearch", HTTPMethod.POST, HTTPStatus.OK, endpoint=EndPoint.ATLAS
)

CONTENT_TYPE_BY_EXT = {
    "md": "text/markdown",
    "yaml": "application/x-yaml",
    "yml": "application/x-yaml",
    "json": "application/json",
    "sql": "text/plain",
    "csv": "text/csv",
    "py": "text/plain",
    "txt": "text/plain",
}

ARTIFACT_KIND_BY_EXT = {"md", "yaml", "json", "sql", "csv", "py"}


def _nano21() -> str:
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(21))


def _basename_no_ext(display_name: str) -> str:
    base = display_name.rsplit("/", 1)[-1]
    return base.rsplit(".", 1)[0] if "." in base else base


def _ext_of(display_name: str) -> str:
    base = display_name.rsplit("/", 1)[-1]
    return base.rsplit(".", 1)[-1].lower() if "." in base else "txt"


def _kind_of(ext: str) -> str:
    return ext if ext in ARTIFACT_KIND_BY_EXT else "md"


def _bulk_create(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    client = get_atlan_client()
    return client._call_api(BULK_ENTITY, request_obj={"entities": entities})


def _index_search(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = get_atlan_client()
    return client._call_api(INDEX_SEARCH, request_obj=payload)


def _presigned_put_url(repo_guid: str, display_name: str) -> str:
    client = get_atlan_client()
    res = client._call_api(
        PRESIGNED_URL,
        request_obj={
            "key": f"context-repos/{repo_guid}/{display_name}",
            "expiry": "120s",
            "method": "PUT",
        },
    )
    url = (res or {}).get("url")
    if not url:
        raise RuntimeError(f"presignedUrl response missing 'url': {res!r}")
    return url


def _s3_put(url: str, body: bytes, content_type: str) -> int:
    """PUT bytes to a presigned URL. Uses the same httpx session as the SDK
    but explicitly drops Atlan auth headers — the URL is already signed."""
    client = get_atlan_client()
    sess = client._session
    # Strip the SDK's Authorization header for the S3 put; the presigned URL
    # carries its own credentials, and S3 rejects extra auth headers.
    resp = sess.put(url, content=body, headers={"Content-Type": content_type})
    return resp.status_code


def _ensure_repo_and_skill(spec: ContextRepositorySpec) -> Dict[str, str]:
    """Persist ContextRepository + paired Skill via a single bulk-create with
    negative guids cross-referencing each other. Returns identifiers."""
    repo_qn = f"default/context/{_nano21()}"
    skill_qn = f"default/skill/{_nano21()}"

    input_assets = [
        {"guid": ref.guid, "typeName": ref.type_name}
        for ref in (spec.input_assets or [])
    ]

    repo_attrs: Dict[str, Any] = {
        "name": spec.name,
        "qualifiedName": repo_qn,
        "contextRepositoryLifecycleStatus": "DRAFT",
        "contextRepositoryRepoType": "agent_bundle",
    }
    if spec.user_description:
        repo_attrs["description"] = spec.user_description
    if spec.agent_instructions is not None:
        repo_attrs["contextRepositoryAgentInstructions"] = spec.agent_instructions
    if spec.target_connection_qualified_name:
        repo_attrs["contextRepositoryTargetConnectionQualifiedName"] = (
            spec.target_connection_qualified_name
        )

    payload = [
        {
            "guid": "-1",
            "typeName": "ContextRepository",
            "attributes": repo_attrs,
            "relationshipAttributes": {
                "contextInputAssets": input_assets,
                "contextOutputSkill": {"guid": "-2", "typeName": "Skill"},
            },
        },
        {
            "guid": "-2",
            "typeName": "Skill",
            "attributes": {
                "name": spec.name,
                "qualifiedName": skill_qn,
                "skillType": "CONTEXT_REPO",
                "skillVersion": "0.1.0",
                "certificateStatus": "DRAFT",
            },
        },
    ]
    res = _bulk_create(payload)
    created = (res or {}).get("mutatedEntities", {}).get("CREATE", []) or []
    repo_guid: Optional[str] = next(
        (e["guid"] for e in created if e.get("typeName") == "ContextRepository"),
        None,
    )
    skill_guid: Optional[str] = next(
        (e["guid"] for e in created if e.get("typeName") == "Skill"),
        None,
    )
    if not repo_guid:
        raise RuntimeError(
            f"Could not extract ContextRepository guid from bulk-create response: {res!r}"
        )
    return {
        "repo_qn": repo_qn,
        "repo_guid": repo_guid,
        "skill_qn": skill_qn,
        "skill_guid": skill_guid or "",
    }


def _index_existing_artifacts(skill_qn: str) -> Dict[str, str]:
    """Return {displayName: qualifiedName} for every SkillArtifact under skill_qn."""
    res = _index_search(
        {
            "dsl": {
                "from": 0,
                "size": 200,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"__typeName.keyword": "SkillArtifact"}},
                            {"prefix": {"qualifiedName": f"{skill_qn}/artifact/"}},
                        ]
                    }
                },
            },
            "attributes": ["displayName", "qualifiedName"],
        }
    )
    out: Dict[str, str] = {}
    for e in (res or {}).get("entities", []) or []:
        a = e.get("attributes") or {}
        dn, qn = a.get("displayName"), a.get("qualifiedName")
        if dn and qn:
            out[dn] = qn
    return out


def _publish_artifact(
    repo_guid: str,
    skill_qn: str,
    art: ContextBundleArtifactSpec,
    existing_qn: Optional[str],
) -> Dict[str, Any]:
    body_bytes = art.content.encode("utf-8")
    ext = _ext_of(art.display_name)
    kind = _kind_of(ext)
    qn = existing_qn or f"{skill_qn}/artifact/{kind}/{_nano21()}"
    op = "UPDATE" if existing_qn else "CREATE"

    entity = {
        "typeName": "SkillArtifact",
        "attributes": {
            "name": _basename_no_ext(art.display_name),
            "qualifiedName": qn,
            "displayName": art.display_name,
            "filePath": f"{S3_PREFIX}/{repo_guid}/{art.display_name}",
            "fileType": ext,
            "description": art.content,
            "skillArtifactContent": art.content,
            "skillArtifactContentType": ext,
            "skillArtifactRepoGuid": repo_guid,
        },
        "relationshipAttributes": {
            "skillSource": {
                "typeName": "Skill",
                "uniqueAttributes": {"qualifiedName": skill_qn},
            },
        },
    }
    bulk_res = _bulk_create([entity])
    # Locate the just-saved guid from the bulk response so we can return it.
    art_guid: Optional[str] = None
    for k in ("CREATE", "UPDATE", "PARTIAL_UPDATE"):
        for e in (bulk_res or {}).get("mutatedEntities", {}).get(k, []) or []:
            if e.get("typeName") == "SkillArtifact" and (
                e.get("attributes", {}).get("qualifiedName") == qn
            ):
                art_guid = e.get("guid")
                break
        if art_guid:
            break

    # S3 upload — the presigned URL is signed for the exact key.
    presigned = _presigned_put_url(repo_guid, art.display_name)
    content_type = CONTENT_TYPE_BY_EXT.get(ext, "text/plain")
    s3_status = _s3_put(presigned, body_bytes, content_type)
    if not (200 <= s3_status < 300):
        raise RuntimeError(
            f"S3 PUT for {art.display_name!r} failed with status {s3_status}"
        )

    return {
        "operation": op,
        "name": art.display_name,
        "guid": art_guid or "",
        "qualified_name": qn,
        "type_name": "SkillArtifact",
    }


def _activate_bundle(
    spec_name: str, repo_qn: str, skill_qn: str, owner_user: Optional[str]
) -> None:
    entities = [
        {
            "typeName": "ContextRepository",
            "attributes": {
                "qualifiedName": repo_qn,
                "name": spec_name,
                "contextRepositoryLifecycleStatus": "ACTIVE",
                "certificateStatus": "VERIFIED",
                **({"ownerUsers": [owner_user]} if owner_user else {}),
            },
        },
        {
            "typeName": "Skill",
            "attributes": {
                "qualifiedName": skill_qn,
                "name": spec_name,
                "certificateStatus": "VERIFIED",
                **({"ownerUsers": [owner_user]} if owner_user else {}),
            },
        },
    ]
    _bulk_create(entities)


def create_context_repository_assets(
    repos: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Create one or multiple ContextRepository bundles (repo + skill + artifacts).

    See ContextRepositorySpec for the input shape. Returns a flat list of
    dicts describing each created/updated asset:

        {
          "operation": "CREATE" | "UPDATE",
          "guid": "<asset-guid>",
          "name": "<asset-name>",
          "qualified_name": "<asset-qualified-name>",
          "type_name": "ContextRepository" | "Skill" | "SkillArtifact",
        }
    """
    data = repos if isinstance(repos, list) else [repos]
    logger.info(f"Creating {len(data)} ContextRepository bundle(s)")
    specs = [ContextRepositorySpec(**item) for item in data]

    results: List[Dict[str, Any]] = []
    for spec in specs:
        ids = _ensure_repo_and_skill(spec)
        repo_guid = ids["repo_guid"]
        skill_qn = ids["skill_qn"]
        results.extend(
            [
                {
                    "operation": "CREATE",
                    "guid": ids["repo_guid"],
                    "name": spec.name,
                    "qualified_name": ids["repo_qn"],
                    "type_name": "ContextRepository",
                },
                {
                    "operation": "CREATE",
                    "guid": ids["skill_guid"],
                    "name": spec.name,
                    "qualified_name": skill_qn,
                    "type_name": "Skill",
                },
            ]
        )

        artifacts = spec.artifacts or []
        if artifacts:
            existing = _index_existing_artifacts(skill_qn)
            for art in artifacts:
                results.append(
                    _publish_artifact(
                        repo_guid=repo_guid,
                        skill_qn=skill_qn,
                        art=art,
                        existing_qn=existing.get(art.display_name),
                    )
                )

        if spec.activate:
            _activate_bundle(spec.name, ids["repo_qn"], skill_qn, spec.owner_user)

    return results


def create_skill_assets(
    skills: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Create one or multiple standalone Skill assets.

    For Skills tied to a ContextRepository (the common case), use
    create_context_repository_assets — it creates the paired bundle and the
    artifacts as a single transaction, which is what the UI expects.

    This tool covers the rarer case of SYSTEM or CUSTOM skills that exist
    independently of a context repo.
    """
    data = skills if isinstance(skills, list) else [skills]
    logger.info(f"Creating {len(data)} standalone Skill asset(s)")
    specs = [SkillSpec(**item) for item in data]

    asset_objs: List[Skill] = []
    for spec in specs:
        skill = Skill.creator(name=spec.name)
        if spec.user_description is not None:
            skill.user_description = spec.user_description
        if spec.certificate_status:
            skill.certificate_status = spec.certificate_status.value
        if spec.skill_version is not None:
            skill.skill_version = spec.skill_version
        asset_objs.append(skill)

    return save_assets(asset_objs)
