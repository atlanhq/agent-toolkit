"""Tests that query_asset enforces the read-only SQL contract before touching the client."""

from unittest.mock import patch

from tools.query import query_asset


def test_rejects_write_sql_without_calling_client():
    with patch("tools.query.get_atlan_client") as mock_get_client:
        result = query_asset(
            sql="DROP TABLE PAGES",
            connection_qualified_name="default/snowflake/1657275059",
        )

    assert result["success"] is False
    assert (
        "read-only" in result["error"].lower()
        or "not allowed" in result["error"].lower()
    )
    mock_get_client.assert_not_called()


def test_rejects_multi_statement_sql_without_calling_client():
    with patch("tools.query.get_atlan_client") as mock_get_client:
        result = query_asset(
            sql="SELECT * FROM PAGES; DROP TABLE PAGES;",
            connection_qualified_name="default/snowflake/1657275059",
        )

    assert result["success"] is False
    mock_get_client.assert_not_called()


def test_allows_select_and_calls_client():
    with (
        patch("tools.query.get_atlan_client") as mock_get_client,
        patch("tools.query.QueryRequest") as mock_query_request,
    ):
        mock_client = mock_get_client.return_value
        mock_client.queries.stream.return_value = {"rows": []}

        result = query_asset(
            sql="SELECT * FROM PAGES LIMIT 10",
            connection_qualified_name="default/snowflake/1657275059",
            default_schema="LANDING.FRONTEND_PROD",
        )

    assert result["success"] is True
    mock_get_client.assert_called_once()
    mock_query_request.assert_called_once_with(
        sql="SELECT * FROM PAGES LIMIT 10",
        data_source_name="default/snowflake/1657275059",
        default_schema="LANDING.FRONTEND_PROD",
    )
    mock_client.queries.stream.assert_called_once()
