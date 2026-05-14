import json
import logging
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from implementation.db import SQLiteAdapter, ValidationError
from implementation.init_db import DB_PATH, create_database

logger = logging.getLogger(__name__)
mcp = FastMCP("SQLite Lab MCP Server")
adapter = SQLiteAdapter(DB_PATH)


def ensure_database() -> None:
    if not Path(DB_PATH).exists():
        create_database(DB_PATH)


def success_response(
    data: Any, metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "error": None,
        "metadata": metadata or {},
    }


def error_response(message: str) -> dict[str, Any]:
    return {"success": False, "data": None, "error": message, "metadata": {}}


def call_safely(operation: str, handler: Any) -> dict[str, Any]:
    ensure_database()
    try:
        return handler()
    except ValidationError as error:
        return error_response(str(error))
    except ValueError as error:
        return error_response(str(error))
    except Exception:
        logger.exception("Unexpected %s failure", operation)
        return error_response(f"{operation} failed unexpectedly")


@mcp.tool(name="search")
def search(
    table: str,
    filters: list[dict[str, Any]] | None = None,
    columns: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    order_by: str | None = None,
    descending: bool = False,
) -> dict[str, Any]:
    return call_safely(
        "search",
        lambda: success_response(
            adapter.search(
                table=table,
                filters=filters,
                columns=columns,
                limit=limit,
                offset=offset,
                order_by=order_by,
                descending=descending,
            ),
            {"table": table, "limit": limit, "offset": offset},
        ),
    )


@mcp.tool(name="insert")
def insert(table: str, values: dict[str, Any]) -> dict[str, Any]:
    return call_safely(
        "insert",
        lambda: success_response(
            adapter.insert(table=table, values=values), {"table": table}
        ),
    )


@mcp.tool(name="aggregate")
def aggregate(
    table: str,
    metric: str,
    column: str | None = None,
    filters: list[dict[str, Any]] | None = None,
    group_by: str | None = None,
) -> dict[str, Any]:
    return call_safely(
        "aggregate",
        lambda: success_response(
            adapter.aggregate(
                table=table,
                metric=metric,
                column=column,
                filters=filters,
                group_by=group_by,
            ),
            {"table": table, "metric": metric, "group_by": group_by},
        ),
    )


@mcp.resource("schema://database", mime_type="application/json")
def database_schema() -> str:
    response = call_safely(
        "database schema", lambda: success_response(adapter.get_database_schema())
    )
    return json.dumps(response, indent=2)


@mcp.resource("schema://table/{table_name}", mime_type="application/json")
def table_schema(table_name: str) -> str:
    response = call_safely(
        "table schema",
        lambda: success_response(
            adapter.get_table_schema(table_name), {"table": table_name}
        ),
    )
    return json.dumps(response, indent=2)


if __name__ == "__main__":
    ensure_database()
    mcp.run()
