"""Tests for the query_asset_tool read-only SQL enforcement."""

import pytest

from utils.sql_validator import validate_read_only_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM PAGES LIMIT 10",
        'select count(*) from "LANDING"."FRONTEND_PROD"."PAGES"',
        "  SELECT page_type FROM PAGES WHERE created_date >= '2024-01-01'  ",
        "WITH recent AS (SELECT * FROM PAGES) SELECT * FROM recent",
        "SHOW TABLES",
        "DESCRIBE PAGES",
        "DESC PAGES",
        "EXPLAIN SELECT * FROM PAGES",
        "VALUES (1, 2, 3)",
        "SELECT * FROM PAGES WHERE comment = 'please insert here'",
        "SELECT * FROM PAGES; ",  # single trailing semicolon is fine
    ],
)
def test_allows_read_only_statements(sql):
    is_valid, error = validate_read_only_sql(sql)
    assert is_valid is True
    assert error is None


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO PAGES (id) VALUES (1)",
        "UPDATE PAGES SET views = 0",
        "DELETE FROM PAGES",
        "DROP TABLE PAGES",
        "TRUNCATE TABLE PAGES",
        "ALTER TABLE PAGES ADD COLUMN foo INT",
        "CREATE TABLE PAGES (id INT)",
        "GRANT SELECT ON PAGES TO some_role",
        "SELECT * INTO new_table FROM PAGES",
        "WITH t AS (INSERT INTO PAGES (id) VALUES (1) RETURNING *) SELECT * FROM t",
        "SELECT * FROM PAGES; DROP TABLE PAGES;",
        "",
        "   ",
    ],
)
def test_rejects_non_read_only_statements(sql):
    is_valid, error = validate_read_only_sql(sql)
    assert is_valid is False
    assert error
