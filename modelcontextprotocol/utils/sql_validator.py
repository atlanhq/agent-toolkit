"""
Lightweight read-only SQL validator for ``query_asset_tool``.

``query_asset_tool`` is documented as read-only, but the underlying Atlan
query service will happily execute any SQL it is given. This module provides
a conservative, dependency-free check that rejects statements which are not
plainly read-only *before* a ``QueryRequest`` is ever built, so the tool's
documented contract is enforced in code rather than only in the docstring.

This is intentionally conservative rather than a full SQL parser: it is
designed to catch write/DDL statements and multi-statement payloads, not to
validate SQL correctness. Anything it can't confidently classify as
read-only is rejected.
"""

import re

# Statement keywords that are allowed to start a read-only query.
_ALLOWED_LEADING_KEYWORDS = {
    "select",
    "with",
    "show",
    "describe",
    "desc",
    "explain",
    "values",
}

# Keywords that indicate a write, DDL, or session/administrative
# statement. These are rejected wherever they appear (not just as the
# leading keyword) so that write statements hidden inside CTEs or
# subqueries (e.g. ``WITH t AS (INSERT INTO ... RETURNING *) SELECT * FROM t``)
# are also caught.
_DISALLOWED_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "merge",
    "upsert",
    "replace",
    "drop",
    "alter",
    "create",
    "truncate",
    "rename",
    "grant",
    "revoke",
    "call",
    "exec",
    "execute",
    "copy",
    "vacuum",
    "attach",
    "detach",
    "pragma",
    "use",
    "set",
    "lock",
    "unlock",
    "into",  # covers "SELECT ... INTO new_table"
}

# Matches single- and double-quoted string literals, backtick/bracket
# identifiers, and line/block comments so keyword scanning doesn't get
# confused by SQL that merely *mentions* a disallowed word inside a
# literal (e.g. WHERE comment = 'please insert here').
_STRIPPABLE_PATTERN = re.compile(
    r"""
    '(?:[^'\\]|\\.)*'      # single-quoted string literal
    | "(?:[^"\\]|\\.)*"    # double-quoted string/identifier
    | `(?:[^`\\]|\\.)*`    # backtick identifier
    | --[^\n]*             # line comment
    | /\*.*?\*/            # block comment
    """,
    re.VERBOSE | re.DOTALL,
)

_WORD_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _strip_literals_and_comments(sql: str) -> str:
    return _STRIPPABLE_PATTERN.sub(" ", sql)


def _split_statements(sql: str) -> list:
    """Split on top-level semicolons (literals/comments already stripped)."""
    statements = [s.strip() for s in sql.split(";")]
    return [s for s in statements if s]


def validate_read_only_sql(sql: str) -> tuple[bool, str | None]:
    """
    Check whether the given SQL is a plain, single, read-only statement.

    Args:
        sql: The raw SQL text supplied to ``query_asset_tool``.

    Returns:
        A ``(is_valid, error_message)`` tuple. ``error_message`` is ``None``
        when ``is_valid`` is ``True``.
    """
    if not sql or not sql.strip():
        return False, "SQL query cannot be empty"

    cleaned = _strip_literals_and_comments(sql)

    statements = _split_statements(cleaned)
    if len(statements) == 0:
        return False, "SQL query cannot be empty"
    if len(statements) > 1:
        return (
            False,
            (
                "Multi-statement SQL is not supported by query_asset_tool; "
                "please submit a single read-only statement"
            ),
        )

    statement = statements[0]
    words = [w.lower() for w in _WORD_PATTERN.findall(statement)]
    if not words:
        return False, "SQL query cannot be empty"

    leading_keyword = words[0]
    if leading_keyword not in _ALLOWED_LEADING_KEYWORDS:
        return (
            False,
            (
                "query_asset_tool only supports read-only statements "
                "(SELECT/WITH/SHOW/DESCRIBE/EXPLAIN/VALUES); "
                f"'{leading_keyword.upper()}' is not allowed"
            ),
        )

    found_disallowed = [w for w in words if w in _DISALLOWED_KEYWORDS]
    if found_disallowed:
        return (
            False,
            (
                "query_asset_tool only supports read-only statements; "
                f"found disallowed keyword(s): {', '.join(sorted(set(found_disallowed)))}"
            ),
        )

    return True, None
