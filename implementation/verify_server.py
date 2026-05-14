import json
from pathlib import Path
from typing import Any

from implementation import mcp_server
from implementation.db import SQLiteAdapter
from implementation.init_db import create_database


def show(label: str, payload: Any) -> None:
    print(f"\n## {label}")
    print(json.dumps(payload, indent=2))


def main() -> None:
    db_path = create_database(Path(__file__).with_name("lab.db"))
    mcp_server.adapter = SQLiteAdapter(db_path)

    show("Schema resource", json.loads(mcp_server.database_schema()))
    show(
        "Table schema resource",
        json.loads(mcp_server.table_schema("students")),
    )
    show(
        "Successful search",
        mcp_server.search(
            "students",
            filters=[{"column": "cohort", "operator": "eq", "value": "A1"}],
            columns=["id", "name", "score"],
            limit=10,
            order_by="score",
            descending=True,
        ),
    )
    show(
        "Successful insert",
        mcp_server.insert(
            "students",
            {
                "name": "Minh Dao",
                "cohort": "D4",
                "email": "minh.dao@example.edu",
                "score": 93.25,
            },
        ),
    )
    show(
        "Successful aggregate",
        mcp_server.aggregate("students", "avg", "score", group_by="cohort"),
    )
    show("Failing bad table", mcp_server.search("missing"))
    show(
        "Failing bad operator",
        mcp_server.search(
            "students",
            filters=[{"column": "name", "operator": "raw", "value": "An"}],
        ),
    )
    show("Failing bad aggregate", mcp_server.aggregate("students", "median", "score"))


if __name__ == "__main__":
    main()
