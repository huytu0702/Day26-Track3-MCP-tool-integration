from pathlib import Path

import pytest

from implementation.db import SQLiteAdapter, ValidationError
from implementation.init_db import create_database


@pytest.fixture
def adapter(tmp_path: Path) -> SQLiteAdapter:
    db_path = create_database(tmp_path / "lab.db")
    return SQLiteAdapter(db_path)


def test_search_filters_orders_and_paginates(adapter: SQLiteAdapter) -> None:
    rows = adapter.search(
        table="students",
        filters=[{"column": "cohort", "operator": "eq", "value": "A1"}],
        columns=["name", "score"],
        limit=1,
        offset=0,
        order_by="score",
        descending=True,
    )

    assert rows == [{"name": "Binh Tran", "score": 91.0}]


def test_search_supports_in_operator(adapter: SQLiteAdapter) -> None:
    rows = adapter.search(
        table="students",
        filters=[{"column": "cohort", "operator": "in", "value": ["A1", "C3"]}],
        columns=["cohort"],
        limit=10,
        order_by="cohort",
    )

    assert [row["cohort"] for row in rows] == ["A1", "A1", "C3"]


def test_insert_returns_inserted_payload(adapter: SQLiteAdapter) -> None:
    row = adapter.insert(
        "students",
        {
            "name": "Gia Hoang",
            "cohort": "D4",
            "email": "gia.hoang@example.edu",
            "score": 95.5,
        },
    )

    assert row["id"] > 0
    assert row["name"] == "Gia Hoang"
    assert row["cohort"] == "D4"


def test_aggregate_count_avg_sum_min_max(adapter: SQLiteAdapter) -> None:
    assert adapter.aggregate("students", "count") == [{"value": 5}]
    assert adapter.aggregate("students", "avg", "score") == [{"value": 82.0}]
    assert adapter.aggregate("students", "sum", "score") == [{"value": 410.0}]
    assert adapter.aggregate("students", "min", "score") == [{"value": 69.5}]
    assert adapter.aggregate("students", "max", "score") == [{"value": 91.0}]


def test_aggregate_groups_by_column(adapter: SQLiteAdapter) -> None:
    rows = adapter.aggregate("students", "avg", "score", group_by="cohort")

    assert rows == [
        {"cohort": "A1", "value": 89.75},
        {"cohort": "B2", "value": 80.5},
        {"cohort": "C3", "value": 69.5},
    ]


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda db: db.search("missing"), "Unknown table"),
        (lambda db: db.search("students", columns=["missing"]), "Unknown column"),
        (
            lambda db: db.search(
                "students",
                filters=[{"column": "name", "operator": "raw", "value": "x"}],
            ),
            "Unsupported filter operator",
        ),
        (lambda db: db.aggregate("students", "median", "score"), "Unsupported"),
        (lambda db: db.insert("students", {}), "must not be empty"),
        (lambda db: db.search("students", limit=101), "Limit"),
    ],
)
def test_rejects_invalid_requests(adapter: SQLiteAdapter, call, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        call(adapter)


def test_parameterized_filters_do_not_bypass_query(adapter: SQLiteAdapter) -> None:
    rows = adapter.search(
        "students",
        filters=[{"column": "name", "operator": "eq", "value": "x' OR 1=1--"}],
    )

    assert rows == []
