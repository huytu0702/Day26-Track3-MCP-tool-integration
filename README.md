# Database MCP Server Lab

**Student:** Nguyễn Huy Tú  
**MSV:** 2A202600170

This repository contains a FastMCP + SQLite implementation for the Day 26 Track 3 MCP tool integration lab.

## Documentation

- [Setup Instructions](docs/setup-instructions.md)
- [Tool Descriptions](docs/tool-descriptions.md)
- [Testing Steps](docs/testing-steps.md)
- [Client Configuration Example](docs/client-configuration.md)

## Quick verification

```bash
source .venv/Scripts/activate
python -m implementation.verify_server
pytest implementation/tests --cov=implementation --cov-report=term-missing
```
