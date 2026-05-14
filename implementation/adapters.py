from pathlib import Path
from typing import Any, Protocol

Filter = dict[str, Any]
Row = dict[str, Any]


class DatabaseAdapter(Protocol):
    def list_tables(self) -> list[str]: ...

    def get_table_schema(self, table: str) -> list[Row]: ...

    def get_database_schema(self) -> dict[str, list[Row]]: ...

    def search(
        self,
        table: str,
        filters: list[Filter] | None = None,
        columns: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = False,
    ) -> list[Row]: ...

    def insert(self, table: str, values: dict[str, Any]) -> Row: ...

    def aggregate(
        self,
        table: str,
        metric: str,
        column: str | None = None,
        filters: list[Filter] | None = None,
        group_by: str | None = None,
    ) -> list[Row]: ...


class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""


class OutputLimit:
    DEFAULT = 20
    MAX = 100


DatabasePath = str | Path
