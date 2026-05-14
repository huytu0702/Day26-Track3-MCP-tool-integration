import json
from pathlib import Path

import pytest

from implementation import mcp_server
from implementation.db import SQLiteAdapter
from implementation.init_db import create_database


@pytest.fixture(autouse=True)
def isolated_server_adapter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = create_database(tmp_path / "lab.db")
    monkeypatch.setattr(mcp_server, "DB_PATH", db_path)
    monkeypatch.setattr(mcp_server, "adapter", SQLiteAdapter(db_path))


def test_search_tool_returns_success_response() -> None:
    response = mcp_server.search(
        "students",
        filters=[{"column": "cohort", "operator": "eq", "value": "A1"}],
        columns=["name"],
        limit=2,
        order_by="name",
    )

    assert response["success"] is True
    assert response["error"] is None
    assert response["data"] == [{"name": "An Nguyen"}, {"name": "Binh Tran"}]


def test_insert_tool_returns_inserted_row() -> None:
    response = mcp_server.insert(
        "students",
        {
            "name": "Lan Mai",
            "cohort": "A1",
            "email": "lan.mai@example.edu",
            "score": 89,
        },
    )

    assert response["success"] is True
    assert response["data"]["email"] == "lan.mai@example.edu"


def test_aggregate_tool_returns_grouped_results() -> None:
    response = mcp_server.aggregate("students", "avg", "score", group_by="cohort")

    assert response["success"] is True
    assert response["data"][0] == {"cohort": "A1", "value": 89.75}


def test_tool_errors_are_clear() -> None:
    response = mcp_server.search("missing")

    assert response == {
        "success": False,
        "data": None,
        "error": "Unknown table: missing",
        "metadata": {},
    }


def test_database_schema_resource_contains_all_tables() -> None:
    response = json.loads(mcp_server.database_schema())

    assert response["success"] is True
    assert set(response["data"]) == {"courses", "enrollments", "students"}


def test_table_schema_resource_contains_student_columns() -> None:
    response = json.loads(mcp_server.table_schema("students"))

    assert response["success"] is True
    assert [column["name"] for column in response["data"]] == [
        "id",
        "name",
        "cohort",
        "email",
        "score",
    ]


def test_table_schema_resource_rejects_missing_table() -> None:
    response = json.loads(mcp_server.table_schema("missing"))

    assert response["success"] is False
    assert response["error"] == "Unknown table: missing"


def test_create_adapter_defaults_to_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_BACKEND", raising=False)

    adapter = mcp_server.create_adapter()

    assert isinstance(adapter, SQLiteAdapter)


def test_create_adapter_rejects_unknown_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_BACKEND", "oracle")

    with pytest.raises(
        mcp_server.ValidationError, match="Unsupported DATABASE_BACKEND"
    ):
        mcp_server.create_adapter()


def test_create_mcp_supports_auth_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SQLITE_LAB_AUTH_TOKEN", "dev-token")

    server = mcp_server.create_mcp()

    assert server is not None


def test_main_requires_auth_for_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SQLITE_LAB_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(
        mcp_server,
        "parse_args",
        lambda: mcp_server.argparse.Namespace(transport="http"),
    )

    with pytest.raises(SystemExit, match="SQLITE_LAB_AUTH_TOKEN"):
        mcp_server.main()
