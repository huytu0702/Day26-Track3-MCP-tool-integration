# Bonus Features

**Student:** Nguyễn Huy Tú  
**MSV:** 2A202600170

This project implements all optional bonus categories from the rubric.

## 1. HTTP/SSE authentication demo - 5 pts

The server supports stdio by default and can also run with HTTP or SSE transport.

Authentication is enabled by setting `SQLITE_LAB_AUTH_TOKEN`. FastMCP uses a development `StaticTokenVerifier`, so HTTP/SSE clients must send the matching bearer token.

### Run HTTP with auth

Windows Git Bash:

```bash
export SQLITE_LAB_AUTH_TOKEN="dev-lab-token"
./.venv/Scripts/python.exe -m implementation.mcp_server --transport http --host 127.0.0.1 --port 8000
```

PowerShell:

```powershell
$env:SQLITE_LAB_AUTH_TOKEN = "dev-lab-token"
.\.venv\Scripts\python.exe -m implementation.mcp_server --transport http --host 127.0.0.1 --port 8000
```

The MCP endpoint is available at:

```text
http://127.0.0.1:8000/mcp
```

### HTTP client configuration with bearer token

```python
from fastmcp import Client

async with Client("http://127.0.0.1:8000/mcp", auth="dev-lab-token") as client:
    await client.ping()
```

### Repeatable HTTP auth verification

```bash
./.venv/Scripts/python.exe -m implementation.verify_http_auth
```

Expected output:

```text
Authenticated HTTP ping succeeded
Unauthenticated HTTP ping was rejected
```

### Run SSE with auth

```bash
export SQLITE_LAB_AUTH_TOKEN="dev-lab-token"
./.venv/Scripts/python.exe -m implementation.mcp_server --transport sse --host 127.0.0.1 --port 8000
```

## 2. SQLite and PostgreSQL behind a shared interface - 3 pts

The shared adapter interface is defined in:

```text
implementation/adapters.py
```

Implemented adapters:

- SQLite: `implementation/db.py` / `SQLiteAdapter`
- PostgreSQL: `implementation/postgres_db.py` / `PostgresAdapter`

SQLite remains the default backend.

### SQLite default

```bash
./.venv/Scripts/python.exe -m implementation.mcp_server
```

### PostgreSQL backend

Set `DATABASE_BACKEND=postgres` and `DATABASE_URL`:

```bash
export DATABASE_BACKEND="postgres"
export DATABASE_URL="postgresql://user:password@localhost:5432/sqlite_lab"
./.venv/Scripts/python.exe -m implementation.mcp_server
```

The PostgreSQL adapter exposes the same MCP surface:

- `search`
- `insert`
- `aggregate`
- `schema://database`
- `schema://table/{table_name}`

## 3. Extra polish - 2 pts

### Pagination guidance

The `search` tool supports:

- `limit`, default `20`
- `offset`, default `0`
- `order_by`
- `descending`

Recommended paging pattern:

```json
{
  "table": "students",
  "limit": 20,
  "offset": 0,
  "order_by": "id",
  "descending": false
}
```

Then request the next page with:

```json
{
  "table": "students",
  "limit": 20,
  "offset": 20,
  "order_by": "id",
  "descending": false
}
```

### Output limits

`limit` is capped at `100` rows. Invalid limits are rejected with a clear error.

### Structured testing

The test suite covers:

- SQLite adapter behavior
- FastMCP tool wrapper responses
- schema resources
- invalid input errors
- backend selection
- auth-token server construction

Run:

```bash
pytest implementation/tests --cov=implementation --cov-report=term-missing
ruff check implementation
black --check implementation
```
