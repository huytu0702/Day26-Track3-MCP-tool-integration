import sqlite3
from pathlib import Path
from typing import Any

from implementation.init_db import DB_PATH

Filter = dict[str, Any]
Row = dict[str, Any]

SUPPORTED_OPERATORS = {
    "eq": "=",
    "ne": "!=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "like": "LIKE",
}
SUPPORTED_AGGREGATES = {"count", "avg", "sum", "min", "max"}
MAX_LIMIT = 100


class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""


class SQLiteAdapter:
    def __init__(self, db_path: str | Path = DB_PATH) -> None:
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def list_tables(self) -> list[str]:
        with self.connect() as connection:
            rows = connection.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """).fetchall()
        return [row["name"] for row in rows]

    def get_table_schema(self, table: str) -> list[Row]:
        table_name = self.validate_table(table)
        with self.connect() as connection:
            rows = connection.execute(
                f"PRAGMA table_info({self.quote(table_name)})"
            ).fetchall()
        return [
            {
                "name": row["name"],
                "type": row["type"],
                "not_null": bool(row["notnull"]),
                "default": row["dflt_value"],
                "primary_key": bool(row["pk"]),
            }
            for row in rows
        ]

    def get_database_schema(self) -> dict[str, list[Row]]:
        return {table: self.get_table_schema(table) for table in self.list_tables()}

    def search(
        self,
        table: str,
        filters: list[Filter] | None = None,
        columns: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = False,
    ) -> list[Row]:
        table_name = self.validate_table(table)
        selected_columns = self.validate_columns(table_name, columns)
        where_sql, parameters = self.build_where_clause(table_name, filters)
        limit_value = self.validate_limit(limit)
        offset_value = self.validate_offset(offset)

        order_sql = ""
        if order_by is not None:
            order_column = self.validate_column(table_name, order_by)
            direction = "DESC" if descending else "ASC"
            order_sql = f" ORDER BY {self.quote(order_column)} {direction}"

        column_sql = ", ".join(self.quote(column) for column in selected_columns)
        sql = (
            f"SELECT {column_sql} FROM {self.quote(table_name)}"
            f"{where_sql}{order_sql} LIMIT ? OFFSET ?"
        )

        with self.connect() as connection:
            rows = connection.execute(
                sql, [*parameters, limit_value, offset_value]
            ).fetchall()
        return [dict(row) for row in rows]

    def insert(self, table: str, values: dict[str, Any]) -> Row:
        table_name = self.validate_table(table)
        if not values:
            raise ValidationError("Insert values must not be empty")

        columns = [self.validate_column(table_name, column) for column in values]
        placeholders = ", ".join("?" for _ in columns)
        column_sql = ", ".join(self.quote(column) for column in columns)
        sql = (
            f"INSERT INTO {self.quote(table_name)} "
            f"({column_sql}) VALUES ({placeholders})"
        )

        with self.connect() as connection:
            cursor = connection.execute(sql, [values[column] for column in values])
            row_id = cursor.lastrowid
            connection.commit()
            row = connection.execute(
                f"SELECT * FROM {self.quote(table_name)} WHERE id = ?", [row_id]
            ).fetchone()

        if row is None:
            raise ValidationError("Inserted row could not be read back")
        return dict(row)

    def aggregate(
        self,
        table: str,
        metric: str,
        column: str | None = None,
        filters: list[Filter] | None = None,
        group_by: str | None = None,
    ) -> list[Row]:
        table_name = self.validate_table(table)
        metric_name = self.validate_metric(metric)
        where_sql, parameters = self.build_where_clause(table_name, filters)

        if metric_name == "count" and column is None:
            aggregate_target = "*"
        else:
            if column is None:
                raise ValidationError(f"Aggregate '{metric_name}' requires a column")
            aggregate_target = self.quote(self.validate_column(table_name, column))

        select_parts = [f"{metric_name.upper()}({aggregate_target}) AS value"]
        group_sql = ""
        if group_by is not None:
            group_column = self.validate_column(table_name, group_by)
            select_parts.insert(
                0, f"{self.quote(group_column)} AS {self.quote(group_column)}"
            )
            quoted_group_column = self.quote(group_column)
            group_sql = (
                f" GROUP BY {quoted_group_column} ORDER BY {quoted_group_column}"
            )

        select_sql = ", ".join(select_parts)
        sql = (
            f"SELECT {select_sql} FROM {self.quote(table_name)}"
            f"{where_sql}{group_sql}"
        )
        with self.connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [dict(row) for row in rows]

    def validate_table(self, table: str) -> str:
        if table not in self.list_tables():
            raise ValidationError(f"Unknown table: {table}")
        return table

    def validate_columns(self, table: str, columns: list[str] | None) -> list[str]:
        available_columns = self.table_columns(table)
        if columns is None:
            return available_columns
        if not columns:
            raise ValidationError("Columns must not be empty")
        return [self.validate_column(table, column) for column in columns]

    def validate_column(self, table: str, column: str) -> str:
        if column not in self.table_columns(table):
            raise ValidationError(f"Unknown column for {table}: {column}")
        return column

    def validate_metric(self, metric: str) -> str:
        metric_name = metric.lower()
        if metric_name not in SUPPORTED_AGGREGATES:
            raise ValidationError(f"Unsupported aggregate metric: {metric}")
        return metric_name

    def validate_limit(self, limit: int) -> int:
        if not isinstance(limit, int) or limit < 1 or limit > MAX_LIMIT:
            raise ValidationError(f"Limit must be an integer between 1 and {MAX_LIMIT}")
        return limit

    def validate_offset(self, offset: int) -> int:
        if not isinstance(offset, int) or offset < 0:
            raise ValidationError("Offset must be a non-negative integer")
        return offset

    def table_columns(self, table: str) -> list[str]:
        with self.connect() as connection:
            rows = connection.execute(
                f"PRAGMA table_info({self.quote(table)})"
            ).fetchall()
        return [row["name"] for row in rows]

    def build_where_clause(
        self, table: str, filters: list[Filter] | None
    ) -> tuple[str, list[Any]]:
        if not filters:
            return "", []

        clauses = []
        parameters: list[Any] = []
        for item in filters:
            column = self.validate_column(
                table, self.require_filter_value(item, "column")
            )
            operator = self.require_filter_value(item, "operator")
            value = self.require_filter_value(item, "value")

            if operator == "in":
                if not isinstance(value, list) or not value:
                    raise ValidationError(
                        "Operator 'in' requires a non-empty list value"
                    )
                placeholders = ", ".join("?" for _ in value)
                clauses.append(f"{self.quote(column)} IN ({placeholders})")
                parameters.extend(value)
                continue

            if operator not in SUPPORTED_OPERATORS:
                raise ValidationError(f"Unsupported filter operator: {operator}")
            clauses.append(f"{self.quote(column)} {SUPPORTED_OPERATORS[operator]} ?")
            parameters.append(value)

        return f" WHERE {' AND '.join(clauses)}", parameters

    def require_filter_value(self, item: Filter, key: str) -> Any:
        if key not in item:
            raise ValidationError(f"Filter is missing required key: {key}")
        return item[key]

    def quote(self, identifier: str) -> str:
        return f'"{identifier}"'
