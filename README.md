# GAM Appian Knowledge Base

Pre-parsed, LLM-ready knowledge base for Government Acquisition Management (GAM) Appian applications. Contains structured JSON data for all Appian objects, self-contained documentation bundles, dependency graphs, and a MCP server that makes it all queryable from your IDE.

## What's Inside

```
data/
├── CaseManagementStudio/
│   ├── app_overview.json          # Full application map (metadata, bundles, deps, coverage)
│   ├── search_index.json          # Fast object name lookup index
│   ├── bundles/                   # Self-contained documentation bundles
│   │   └── <BundleName>/
│   │       ├── structure.json     # Flow, relationships, object metadata (no code)
│   │       └── code.json          # SAIL code keyed by UUID (loaded on demand)
│   ├── objects/                   # Per-object dependency files
│   │   └── <uuid>.json            # calls[], called_by[], bundles[]
│   └── orphans/                   # Objects not reachable from any entry point
│       ├── _index.json            # Orphan catalog grouped by type
│       └── <uuid>.json            # Individual orphan with code
└── SourceSelection/
    └── (same structure)
```

### Available Applications

| Application | Description |
|---|---|
| SourceSelection | Source selection and vendor evaluation workflows |
| CaseManagementStudio | Case management configuration and automation |

### Bundle Types

Each bundle is a self-contained JSON file representing a complete functional flow with its full transitive dependency tree. All UUIDs and URNs are resolved to human-readable names.

| Type | Entry Point | Contents |
|---|---|---|
| action | Record Type Action | Action → process model → form interface → all deps |
| process | Standalone Process Model | PM → subprocesses → interfaces → deps |
| page | Record Type Views | Summary/detail views → interfaces → supporting objects |
| site | Site | Navigation → all page targets → interfaces |
| dashboard | Control Panel | Dashboard → interfaces → record types |
| web_api | Web API | Endpoint → all called rules/integrations |

---

## Getting Started with Kiro IDE

Follow these steps to set up the GAM Appian Knowledge Base in your Kiro IDE. The knowledge base data lives on GitHub — nothing is stored locally on your machine. The MCP server fetches data on demand at runtime.

### Prerequisites

- [Kiro IDE](https://kiro.dev) installed
- Python 3.10 or later
- `pip` available in your terminal
- A GitHub personal access token (if this is a private repo)

---

### Step 1: Open Kiro IDE

Launch Kiro IDE and open any workspace you want to work in. The knowledge base doesn't need to be cloned — the MCP server reads data directly from GitHub.

---

### Step 2: Install the MCP Server

Open the integrated terminal in Kiro (`` Ctrl+` `` or `` Cmd+` ``) and run:

```bash
pip install "appian-atlas @ git+https://github.com/ram-020998/gam-knowledge-base.git"
```

This installs only the MCP server Python package. The data files in this repo are not downloaded to your machine — the server fetches them from GitHub at runtime.

Verify the installation:

```bash
appian-atlas --help
```

You should see:

```
usage: appian-atlas [-h] (--data-dir DATA_DIR | --github OWNER/REPO)
                     [--branch BRANCH] [--data-prefix DATA_PREFIX]
```

> If `appian-atlas` is not found on your PATH after install, use the full Python module path instead:
> ```bash
> python -m mcp_server --help
> ```
> You can find the installed location with:
> ```bash
> which appian-atlas        # macOS/Linux
> where appian-atlas        # Windows
> ```

---

### Step 3: Set Up GitHub Token (Private Repos Only)

If this is a private repository, the MCP server needs a GitHub token to read data.

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic).
2. Generate a new token with `repo` scope.
3. Set it as an environment variable:

```bash
# macOS/Linux — add to your ~/.zshrc or ~/.bashrc
export GITHUB_TOKEN=ghp_your_token_here

# Windows PowerShell
$env:GITHUB_TOKEN = "ghp_your_token_here"
```

Restart your terminal (or Kiro) after setting this.

---

### Step 4: Install the Kiro Power

The Kiro Power connects the MCP server to your AI assistant and provides steering files that help it use the knowledge base effectively.

1. Open the Command Palette (`Cmd+Shift+P` on macOS, `Ctrl+Shift+P` on Windows/Linux).
2. Type `Powers` and select `Kiro: Open Powers Panel`.
3. Search for `power-gam-appian`.
4. Click Install.

The power automatically configures the MCP server connection. Once installed, the AI assistant has access to all knowledge base tools.

---

### Step 5: Verify Everything Works

1. Open the Kiro sidebar and look for the MCP Servers section.
2. You should see `appian-atlas` listed with a green status indicator.
3. Open the Kiro chat and ask:

```
What GAM applications are available?
```

You should get a response listing the available applications (SourceSelection, CaseManagementStudio, etc.) with object counts and bundle stats.

---

### Step 6: Start Exploring

Here are some things you can ask:

```
Give me an overview of SourceSelection
```

```
Find all evaluation-related actions in SourceSelection
```

```
How does the Complete LPTA Evaluation action work? Show me the full flow.
```

```
What depends on AS_GSS_BL_validateVendors?
```

```
Are there any unused expression rules in SourceSelection?
```

```
Show me the SAIL code for the Add Vendors form
```

---

## MCP Server Tools Reference

The MCP server exposes 9 tools that the AI assistant calls automatically based on your questions.

### list_applications

Lists all available GAM applications with object counts and bundle coverage stats. This is typically the first call the assistant makes.

### get_app_overview

Returns a comprehensive map of a single application in one call — package metadata, all bundles with key objects, dependency summary, and coverage stats.

| Parameter | Required | Description |
|---|---|---|
| app_name | Yes | Application folder name from `list_applications` |

### search_bundles

Finds bundles by keyword match against bundle names and parent names.

| Parameter | Required | Description |
|---|---|---|
| app_name | Yes | Application folder name |
| query | Yes | Case-insensitive search term |
| bundle_type | No | Filter: action, process, page, site, dashboard, web_api |

### search_objects

Searches parsed objects by name using the search index.

| Parameter | Required | Description |
|---|---|---|
| app_name | Yes | Application folder name |
| query | Yes | Case-insensitive search term |
| object_type | No | Filter: Interface, Expression Rule, Process Model, Record Type, CDT, Integration, Web API, Constant, etc. |

### get_bundle

Loads a bundle at the requested detail level. Start with `summary` and escalate to `full` only when you need code.

| Parameter | Required | Description |
|---|---|---|
| app_name | Yes | Application folder name |
| bundle_id | Yes | Bundle ID from search results or app overview |
| detail_level | No | `summary` (default, ~5KB), `structure` (~5-50KB), `full` (~50KB-2MB) |

Detail levels:
- `summary` — metadata, entry point, flow outline, object names only
- `structure` — full structure with relationships, parameters, calls/called_by — no code
- `full` — structure + SAIL code merged into each object

### get_dependencies

Returns the dependency subgraph for a specific object — what it calls and what calls it.

| Parameter | Required | Description |
|---|---|---|
| app_name | Yes | Application folder name |
| object_name | Yes | Case-insensitive object name |

### get_object_detail

Returns dependency and bundle info for an object by UUID. Faster than name lookup when you already have the UUID.

| Parameter | Required | Description |
|---|---|---|
| app_name | Yes | Application folder name |
| object_uuid | Yes | Object UUID |

### list_orphans

Lists all objects not reachable from any entry point, grouped by type.

| Parameter | Required | Description |
|---|---|---|
| app_name | Yes | Application folder name |

### get_orphan

Returns full detail including code for an orphaned object.

| Parameter | Required | Description |
|---|---|---|
| app_name | Yes | Application folder name |
| object_uuid | Yes | Orphan UUID from `list_orphans` |

---

## Troubleshooting

### MCP server not found after pip install

pip may have installed the executable in a location not on your shell's PATH. Try:

```bash
# Use the Python module directly
python -m mcp_server --github ram-020998/gam-knowledge-base
```

Or find the install location:

```bash
pip show -f appian-atlas | grep "Location"
```

### GitHub rate limiting (403 errors)

Unauthenticated GitHub API requests are limited to 60/hour. Set a `GITHUB_TOKEN` to get 5,000/hour (see Step 3).

### Server shows as disconnected in Kiro

1. Check that Python 3.10+ is available: `python --version`
2. Check that the package is installed: `pip list | grep appian-atlas`
3. Try running the server manually to see errors:
   ```bash
   appian-atlas --github ram-020998/gam-knowledge-base
   ```
   The server runs on stdio — it will appear to hang (that's normal). Press `Ctrl+C` to stop.
4. Click the reconnect button in the Kiro MCP Servers panel.

### Data not loading / FileNotFoundError

The server reads from the `data/` folder on the `main` branch by default. If your data is on a different branch, update the power's MCP server config to include `--branch your-branch`.

---

## License

Internal use.
