# Client Configuration Example

**Student:** Nguyễn Huy Tú  
**MSV:** 2A202600170

This project includes a Claude Code MCP client configuration in `.mcp.json`.

## Claude Code configuration

Windows project-local `.venv`:

```json
{
  "mcpServers": {
    "sqlite-lab": {
      "type": "stdio",
      "command": "./.venv/Scripts/python.exe",
      "args": [
        "-m",
        "implementation.mcp_server"
      ],
      "cwd": ".",
      "env": {}
    }
  }
}
```

This configuration is portable across Windows machines as long as:

1. the repository is opened from its project root
2. `.venv` is created in the project root
3. dependencies are installed with `pip install -r requirements.txt`

## macOS/Linux variant

If using macOS or Linux, change only the `command` field:

```json
{
  "mcpServers": {
    "sqlite-lab": {
      "type": "stdio",
      "command": "./.venv/bin/python",
      "args": [
        "-m",
        "implementation.mcp_server"
      ],
      "cwd": ".",
      "env": {}
    }
  }
}
```

## Verify in Claude Code

After restarting or reloading the MCP client, the server should appear as `sqlite-lab`.

Useful checks:

- discover tools: `search`, `insert`, `aggregate`
- read `schema://database`
- read `schema://table/students`
- call `search` on `students`
- call `aggregate` on `students`
- call `search` with `table = "missing"` to confirm safe errors

## HTTP auth client example

Start the server with HTTP auth:

```bash
export SQLITE_LAB_AUTH_TOKEN="dev-lab-token"
./.venv/Scripts/python.exe -m implementation.mcp_server --transport http --host 127.0.0.1 --port 8000
```

Connect with a bearer token:

```python
from fastmcp import Client

async with Client("http://127.0.0.1:8000/mcp", auth="dev-lab-token") as client:
    await client.ping()
```

## MCP Inspector alternative

Windows Git Bash:

```bash
./implementation/start_inspector.sh
```

Manual command:

```bash
npx -y @modelcontextprotocol/inspector ./.venv/Scripts/python.exe -m implementation.mcp_server
```

macOS/Linux:

```bash
npx -y @modelcontextprotocol/inspector ./.venv/bin/python -m implementation.mcp_server
```
