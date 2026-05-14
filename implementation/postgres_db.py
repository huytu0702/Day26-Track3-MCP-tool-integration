import os
from typing import Any

import psycopg
from psycopg.rows import dict_row

from implementation.adapters import Filter, Row, ValidationError
from implementation.db import SUPPORTED_AGGREGATES, SUPPORTED_OPERATORS, SQLiteAdapter


class PostgresAdapter(SQLiteAdapter):
    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.environ.get("DATABASE_URL", "")
        if not self.dsn:
            raise ValidationError("DATABASE_URL is required for PostgreSQL")

    def connect(self) -> psycopg.Connection[Any]:
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def list_tables(self) -> list[str]:
        with self.connect() as connection:
            rows = connection.execute("""
                SELECT table_name AS name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """).fetchall()
        return [row["name"] for row in rows]

    def get_table_schema(self, table: str) -> list[Row]:
        table_name = self.validate_table(table)
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    column_name AS name,
                    data_type AS type,
                    is_nullable,
                    column_default AS default_value
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                ORDER BY ordinal_position
                """,
                [table_name],
            ).fetchall()
        return [
            {
                "name": row["name"],
                "type": row["type"],
                "not_null": row["is_nullable"] == "NO",
                "default": row["default_value"],
                "primary_key": False,
            }
            for row in rows
        ]

    def table_columns(self, table: str) -> list[str]:
        return [column["name"] for column in self.get_table_schema(table)]

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
            f"{where_sql}{order_sql} LIMIT %s OFFSET %s"
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
        placeholders = ", ".join("%s" for _ in columns)
        column_sql = ", ".join(self.quote(column) for column in columns)
        sql = (
            f"INSERT INTO {self.quote(table_name)} "
            f"({column_sql}) VALUES ({placeholders}) RETURNING *"
        )

        with self.connect() as connection:
            row = connection.execute(
                sql, [values[column] for column in values]
            ).fetchone()
            connection.commit()

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
                placeholders = ", ".join("%s" for _ in value)
                clauses.append(f"{self.quote(column)} IN ({placeholders})")
                parameters.extend(value)
                continue

            if operator not in SUPPORTED_OPERATORS:
                raise ValidationError(f"Unsupported filter operator: {operator}")
            clauses.append(f"{self.quote(column)} {SUPPORTED_OPERATORS[operator]} %s")
            parameters.append(value)

        return f" WHERE {' AND '.join(clauses)}", parameters

    def quote(self, identifier: str) -> str:
        return f'"{identifier}"'


__all__ = ["PostgresAdapter", "SUPPORTED_AGGREGATES", "SUPPORTED_OPERATORS"]
