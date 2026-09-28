#!/usr/bin/env python3
"""Fail when a skill tells a model to call a tool that does not exist.

A skill's job is to route: it names the tools a model should reach for. A name
that does not match a real tool does not degrade gracefully. The model calls it,
the server answers ``unknown tool``, and the skill's whole path silently stops
working while the file still reads as correct. Nothing else in this repo checks
this, and today the one skill on a branch names nine tools that do not exist.

Every one of those nine is the same mistake: ``search_assets`` instead of
``search_assets_tool``. The suffix is not inferable, because nine real tools do not
carry it (``read_artifact``, ``create_domains``, ``get_asset_icons`` and others),
so an author has no rule to follow and no feedback until a user hits it. That is
exactly the shape of drift a cheap CI check removes for good.

**What counts as a reference.** Only a backticked ``snake_case`` identifier that
either matches a known tool, or matches one after adding or removing the ``_tool``
suffix, or is a close edit-distance neighbour of one. Ordinary prose in backticks
is ignored. The rule is deliberately narrow: a check that cries wolf gets disabled,
and a near-miss name is the failure mode actually seen in the wild. A wholly
invented name that resembles nothing is NOT caught, and that limit is reported in
the summary rather than left implicit.

**Refreshing the tool list.** ``scripts/known_tools.json`` holds the names only.
Regenerate it from the MCP server's committed surface baseline:

    python3 -c "import json; b=json.load(open('../agent-toolkit-internal/\
modelcontextprotocol/tests/integration/baselines/tool_surface.json')); \
d=json.load(open('scripts/known_tools.json')); d['tools']=sorted(b); \
open('scripts/known_tools.json','w').write(json.dumps(d,indent=2)+chr(10))"

Exit codes: 0 clean or nothing to check, 1 at least one bad reference.
"""

from __future__ import annotations

import difflib
import json
import pathlib
import re
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "scripts" / "known_tools.json"

# Directories that can hold skills. Every plugin layout is checked so a skill
# copied between them cannot drift in only one place.
SKILL_DIRS = ("skills", "cursor-plugin/skills", "codex-plugin/skills", ".agents")

# Documents that route tools the same way a skill does, and drift the same way.
# CLAUDE.md is loaded into every Claude Code session using this plugin, so a stale
# name here misroutes more often than one in a single skill.
ROUTING_DOCS = ("CLAUDE.md", "cursor-plugin/README.md", "codex-plugin/README.md")

# A backticked lower_snake_case identifier. Two or more words, because a single
# word in backticks is almost always prose or a field name, not a tool.
_BACKTICKED = re.compile(r"`([a-z][a-z0-9]*(?:_[a-z0-9]+)+)`")

# Fenced code blocks are stripped before scanning: a worked example may legitimately
# show a payload whose keys look like tool names.
_FENCED = re.compile(r"```.*?```", re.DOTALL)


def load_known_tools() -> set[str]:
    if not MANIFEST.exists():
        print(f"error: {MANIFEST.relative_to(REPO_ROOT)} is missing", file=sys.stderr)
        raise SystemExit(1)
    data = json.loads(MANIFEST.read_text())
    tools = data.get("tools")
    if not isinstance(tools, list) or not tools:
        print(f"error: {MANIFEST.name} has no tools list", file=sys.stderr)
        raise SystemExit(1)
    return set(tools)


def skill_files(paths: list[str] | None) -> list[pathlib.Path]:
    """The skill markdown to scan: explicit paths, or every skill in the repo."""
    if paths:
        return [
            p
            for raw in paths
            if (p := pathlib.Path(raw)).suffix == ".md" and p.is_file()
        ]
    found: list[pathlib.Path] = []
    for d in SKILL_DIRS:
        base = REPO_ROOT / d
        if base.is_dir():
            found.extend(sorted(base.rglob("*.md")))
    for doc in ROUTING_DOCS:
        p = REPO_ROOT / doc
        if p.is_file():
            found.append(p)
    return found


def suggest(name: str, known: set[str]) -> str | None:
    """The real tool this name was probably meant to be, if there is an obvious one."""
    if name.endswith("_tool"):
        stripped = name[: -len("_tool")]
        if stripped in known:
            return stripped
    elif f"{name}_tool" in known:
        return f"{name}_tool"
    close = difflib.get_close_matches(name, sorted(known), n=1, cutoff=0.86)
    return close[0] if close else None


def display(path: pathlib.Path) -> str:
    """Repo-relative where possible, so output is clickable in CI logs."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def check(path: pathlib.Path, known: set[str]) -> list[tuple[int, str, str]]:
    """Bad references in one file, as (line number, name, suggested real name)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    scannable = _FENCED.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    lines = scannable.split("\n")

    bad: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(lines, start=1):
        for name in _BACKTICKED.findall(line):
            if name in known:
                continue
            fix = suggest(name, known)
            if fix:
                bad.append((lineno, name, fix))
            elif name.endswith("_tool"):
                # A name ending in `_tool` is claiming to be a tool outright, so it
                # is flagged even with nothing to suggest. This is what catches a
                # tool that was REMOVED rather than renamed, where no near match
                # exists by definition: `get_assets_by_dsl_tool` sat in this repo's
                # own CLAUDE.md long after the server stopped exposing it. Prose
                # does not end an identifier in `_tool`, so the false-positive risk
                # is close to nil.
                bad.append((lineno, name, ""))
    return bad


def self_test() -> int:
    """Prove the check catches the real drift and stays quiet on prose.

    Kept in-script and stdlib-only on purpose: this repo has no test framework, and
    a check whose own behaviour is unverified is not worth trusting. A checker that
    flags ordinary field names gets disabled by the first person it annoys, so the
    quiet cases matter as much as the loud ones.
    """
    import tempfile

    known = {
        "search_assets_tool",
        "semantic_search_tool",
        "get_assets_tool",
        "traverse_lineage_tool",
        "read_artifact",
        "create_domains",
    }
    cases: list[tuple[str, str, list[str]]] = [
        (
            "the suffix omission actually seen in the wild",
            "Use `search_assets` then `traverse_lineage`.",
            ["search_assets", "traverse_lineage"],
        ),
        (
            "a suffix wrongly added to a tool that has none",
            "Call `read_artifact_tool` to fetch it.",
            ["read_artifact_tool"],
        ),
        ("real tools are silent", "Use `search_assets_tool` and `read_artifact`.", []),
        (
            "field names are not tool references",
            "Filter `qualified_name`, `display_name`, `connection_qualified_name`.",
            [],
        ),
        ("single words are not tool references", "Set `limit` and `offset`.", []),
        (
            "fenced examples are not references",
            'Text.\n```json\n{"search_assets": 1}\n```\n',
            [],
        ),
        (
            "a removed tool is caught by its suffix, with nothing to suggest",
            "Use `get_assets_by_dsl_tool` for advanced filtering.",
            ["get_assets_by_dsl_tool"],
        ),
        (
            "an invented name with no tool-ish suffix is a known blind spot",
            "Call `frobnicate_the_widget` first.",
            [],
        ),
    ]

    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        for label, body, expected in cases:
            path = pathlib.Path(tmp) / "SKILL.md"
            path.write_text(body, encoding="utf-8")
            got = [name for _, name, _ in check(path, known)]
            if sorted(set(got)) != sorted(set(expected)):
                print(f"FAIL  {label}\n      expected {expected}, got {got}")
                failures += 1
            else:
                print(f"ok    {label}")

    # The suggestion has to be right, not merely present: a wrong suggestion sends
    # the author to another name that does not exist.
    for name, want in (
        ("search_assets", "search_assets_tool"),
        ("read_artifact_tool", "read_artifact"),
    ):
        got = suggest(name, known)
        if got != want:
            print(f"FAIL  suggestion for `{name}`: expected `{want}`, got `{got}`")
            failures += 1
        else:
            print(f"ok    suggestion for `{name}` is `{want}`")

    print(f"\nself-test: {failures} failure(s)")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--self-test":
        return self_test()

    known = load_known_tools()
    files = skill_files(argv or None)
    if not files:
        print("no skill files to check")
        return 0

    total = 0
    for path in files:
        for lineno, name, fix in check(path, known):
            hint = (
                f"Did you mean `{fix}`?"
                if fix
                else "No tool by that name exists; it may have been removed or renamed."
            )
            print(f"{display(path)}:{lineno}: `{name}` is not a tool. {hint}")
            total += 1

    print(
        f"\nchecked {len(files)} skill file(s) against {len(known)} tool names: "
        f"{total} bad reference(s)"
    )
    if total:
        print(
            "\nA name that does not match a real tool makes the model call it and "
            "get `unknown tool` back, so the skill's path stops working while the "
            "file still reads as correct.\nIf a tool was renamed or added, refresh "
            "scripts/known_tools.json (see this script's docstring)."
        )
        return 1

    print(
        "Note: this catches names that resemble a real tool. A wholly invented "
        "name that resembles nothing is not caught."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
