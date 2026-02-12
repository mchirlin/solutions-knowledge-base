# GAM Appian Knowledge Base — MCP Server

MCP server for the Government Acquisition Management (GAM) Appian knowledge base. Reads parsed application data from local filesystem or a GitHub repository.

## Setup

```bash
cd appian-parser
source .venv/bin/activate
pip install "mcp[cli]"
```

## Running

### Local mode (filesystem)
```bash
python -m mcp_server --data-dir ./data
```

### GitHub mode (shared team access)
```bash
# Public repo
python -m mcp_server --github myorg/gam-appian-kb

# Private repo
export GITHUB_TOKEN=ghp_...
python -m mcp_server --github myorg/gam-appian-kb

# Custom branch or data path
python -m mcp_server --github myorg/gam-appian-kb --branch develop --data-prefix output
```

## Data Layout

Whether local or on GitHub, the structure is the same:

```
data/
├── SourceSelection/
│   ├── manifest.json
│   ├── dependencies.json
│   └── bundles/
│       ├── _index.json
│       ├── _orphans.json
│       ├── actions/
│       ├── processes/
│       ├── pages/
│       ├── sites/
│       └── web_apis/
└── RequirementsManagement/
    └── ...
```

## Tools (6)

| Tool | Purpose | When to use |
|---|---|---|
| `list_applications` | List all GAM apps with stats | First call — discover what's available |
| `get_app_overview` | Full app map in one call | Second call — understand one app completely |
| `search_bundles` | Find bundles by keyword | Find specific bundles without browsing |
| `get_bundle` | Get bundle content (summary or full) | Load bundle data for analysis |
| `search_objects` | Search objects by name | Find specific objects |
| `get_dependencies` | Dependency subgraph | Trace relationships and impact |

## Kiro Integration

### Local mode (.kiro/settings/mcp.json)
```json
{
  "mcpServers": {
    "gam-appian-kb": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "mcp_server", "--data-dir", "/path/to/data"],
      "cwd": "/path/to/appian-parser"
    }
  }
}
```

### GitHub mode (.kiro/settings/mcp.json)
```json
{
  "mcpServers": {
    "gam-appian-kb": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "mcp_server", "--github", "myorg/gam-appian-kb"],
      "cwd": "/path/to/appian-parser",
      "env": {
        "GITHUB_TOKEN": "ghp_..."
      }
    }
  }
}
```
