# Tool Descriptions

**Student:** Nguyễn Huy Tú  
**MSV:** 2A202600170

The FastMCP server exposes three tools: `search`, `insert`, and `aggregate`.

## `search`

Search rows from a validated SQLite table.

### Parameters

| Parameter | Type | Required | Description |
|---|---:|---:|---|
| `table` | string | yes | Table name, such as `students`, `courses`, or `enrollments` |
| `filters` | array/null | no | List of filter objects with `column`, `operator`, and `value` |
| `columns` | array/null | no | Selected columns to return; returns all columns when omitted |
| `limit` | integer | no | Number of rows to return, default `20`, max `100` |
| `offset` | integer | no | Number of rows to skip, default `0` |
| `order_by` | string/null | no | Column used for sorting |
| `descending` | boolean | no | Sort descending when `true` |

### Supported filter operators

- `eq`
- `ne`
- `gt`
- `gte`
- `lt`
- `lte`
- `like`
- `in`

### Example

```json
{
  "table": "students",
  "filters": [
    {"column": "cohort", "operator": "eq", "value": "A1"}
  ],
  "columns": ["id", "name", "score"],
  "limit": 10,
  "offset": 0,
  "order_by": "score",
  "descending": true
}
```

## `insert`

Insert one row into a validated SQLite table and return the inserted payload.

### Parameters

| Parameter | Type | Required | Description |
|---|---:|---:|---|
| `table` | string | yes | Target table name |
| `values` | object | yes | Non-empty object of column/value pairs |

### Example

```json
{
  "table": "students",
  "values": {
    "name": "Minh Dao",
    "cohort": "D4",
    "email": "minh.dao@example.edu",
    "score": 93.25
  }
}
```

## `aggregate`

Run aggregate queries on a validated table.

### Parameters

| Parameter | Type | Required | Description |
|---|---:|---:|---|
| `table` | string | yes | Target table name |
| `metric` | string | yes | One of `count`, `avg`, `sum`, `min`, `max` |
| `column` | string/null | conditional | Required for `avg`, `sum`, `min`, `max`; optional for `count` |
| `filters` | array/null | no | Same filter shape as `search` |
| `group_by` | string/null | no | Optional column used for grouped aggregation |

### Example

```json
{
  "table": "students",
  "metric": "avg",
  "column": "score",
  "group_by": "cohort"
}
```

## Response shape

Successful response:

```json
{
  "success": true,
  "data": [],
  "error": null,
  "metadata": {}
}
```

Failure response:

```json
{
  "success": false,
  "data": null,
  "error": "Unknown table: missing",
  "metadata": {}
}
```

## Safety behavior

The implementation rejects:

- unknown table names
- unknown column names
- unsupported operators
- invalid aggregate metrics
- empty inserts
- invalid pagination limits

SQL values are passed with parameterized SQLite placeholders.
