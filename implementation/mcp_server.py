import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

from implementation.adapters import DatabaseAdapter, ValidationError
from implementation.db import SQLiteAdapter
from implementation.init_db import DB_PATH, create_database
from implementation.postgres_db import PostgresAdapter

logger = logging.getLogger(__name__)


def create_adapter() -> DatabaseAdapter:
    backend = os.environ.get("DATABASE_BACKEND", "sqlite").lower()
    if backend == "postgres":
        return PostgresAdapter()
    if backend != "sqlite":
        raise ValidationError(f"Unsupported DATABASE_BACKEND: {backend}")
    return SQLiteAdapter(DB_PATH)


def create_mcp() -> FastMCP:
    token = os.environ.get("SQLITE_LAB_AUTH_TOKEN")
    if not token:
        return FastMCP("SQLite Lab MCP Server")

    verifier = StaticTokenVerifier(
        tokens={token: {"client_id": "sqlite-lab-demo", "scopes": ["lab:read"]}},
        required_scopes=["lab:read"],
    )
    return FastMCP("SQLite Lab MCP Server", auth=verifier)


adapter = create_adapter()


def ensure_database() -> None:
    if isinstance(adapter, SQLiteAdapter) and not Path(DB_PATH).exists():
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


def insert(table: str, values: dict[str, Any]) -> dict[str, Any]:
    return call_safely(
        "insert",
        lambda: success_response(
            adapter.insert(table=table, values=values), {"table": table}
        ),
    )


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


def database_schema() -> str:
    response = call_safely(
        "database schema", lambda: success_response(adapter.get_database_schema())
    )
    return json.dumps(response, indent=2)


def table_schema(table_name: str) -> str:
    response = call_safely(
        "table schema",
        lambda: success_response(
            adapter.get_table_schema(table_name), {"table": table_name}
        ),
    )
    return json.dumps(response, indent=2)


def build_mcp() -> FastMCP:
    server = create_mcp()
    server.tool(name="search")(search)
    server.tool(name="insert")(insert)
    server.tool(name="aggregate")(aggregate)
    server.resource("schema://database", mime_type="application/json")(database_schema)
    server.resource("schema://table/{table_name}", mime_type="application/json")(
        table_schema
    )
    return server


mcp = build_mcp()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SQLite Lab MCP Server")
    parser.add_argument(
        "--transport", choices=["stdio", "http", "sse"], default="stdio"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    global mcp

    args = parse_args()
    ensure_database()
    if args.transport == "stdio":
        mcp.run()
        return
    if not os.environ.get("SQLITE_LAB_AUTH_TOKEN"):
        raise SystemExit("SQLITE_LAB_AUTH_TOKEN is required for http/sse transport")
    mcp = build_mcp()
    mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
