# Testing Steps

**Student:** Nguyễn Huy Tú  
**MSV:** 2A202600170

Run these commands from the project root after activating `.venv`.

## 1. Initialize the database

```bash
python -m implementation.init_db
```

Expected result:

```text
Initialized SQLite database at .../implementation/lab.db
```

## 2. Run the repeatable verification script

```bash
python -m implementation.verify_server
```

The script demonstrates:

- reading the full schema resource
- reading `schema://table/students`
- successful `search`
- successful `insert`
- successful `aggregate`
- failing request for a missing table
- failing request for an unsupported operator
- failing request for an unsupported aggregate metric

## 3. Run automated tests with coverage

```bash
pytest implementation/tests --cov=implementation --cov-report=term-missing
```

Current verified result:

```text
23 passed
coverage: 93%
```

## 4. Run HTTP auth verification

```bash
python -m implementation.verify_http_auth
```

Expected result:

```text
Authenticated HTTP ping succeeded
Unauthenticated HTTP ping was rejected
```

## 5. Run lint checks

```bash
ruff check implementation
```

Expected result:

```text
All checks passed!
```

## 6. Run format check

```bash
black --check implementation
```

Expected result:

```text
7 files would be left unchanged.
```

## 7. Manual MCP client checks

After configuring the MCP client, verify these calls:

### Search

```json
{
  "table": "students",
  "filters": null,
  "columns": ["id", "name", "cohort"],
  "limit": 2,
  "offset": 0,
  "order_by": "id",
  "descending": false
}
```

Expected response includes students `An Nguyen` and `Binh Tran`.

### Aggregate

```json
{
  "table": "students",
  "metric": "avg",
  "column": "score",
  "filters": null,
  "group_by": "cohort"
}
```

Expected response includes average score by cohort.

### Failure case

```json
{
  "table": "missing"
}
```

Expected response:

```json
{
  "success": false,
  "data": null,
  "error": "Unknown table: missing",
  "metadata": {}
}
```

## 8. Resource checks

Verify these resources are readable:

- `schema://database`
- `schema://table/students`

The per-table resource should list columns:

- `id`
- `name`
- `cohort`
- `email`
- `score`
