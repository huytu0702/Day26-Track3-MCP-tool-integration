# Setup Instructions

**Student:** Nguyễn Huy Tú  
**MSV:** 2A202600170

## Prerequisites

- Python 3.12 or newer
- Git Bash, PowerShell, or another terminal
- Node.js/npm only if you want to run MCP Inspector

## 1. Clone or open the repository

Open a terminal at the project root:

```bash
cd /path/to/Day26-Track3-MCP-tool-integration
```

## 2. Create the virtual environment

Windows Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Initialize the SQLite database

```bash
python -m implementation.init_db
```

This creates `implementation/lab.db` with reproducible seed data for:

- `students`
- `courses`
- `enrollments`

## 5. Run the MCP server

```bash
python -m implementation.mcp_server
```

The server uses stdio transport by default.

## 6. Optional: run MCP Inspector

Windows Git Bash:

```bash
./implementation/start_inspector.sh
```

Manual equivalent:

```bash
npx -y @modelcontextprotocol/inspector ./.venv/Scripts/python.exe -m implementation.mcp_server
```

For macOS/Linux, replace `./.venv/Scripts/python.exe` with `./.venv/bin/python`.
