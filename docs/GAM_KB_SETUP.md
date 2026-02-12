# GAM Appian Knowledge Base — Setup Guide

Central knowledge base for all Government Acquisition Management (GAM) Appian solutions. Provides LLM-powered exploration of application architecture, bundles, dependencies, and object relationships via Kiro.

---

## Architecture Overview

```
┌─────────────────────┐       ┌──────────────────────┐
│  Team Member's Kiro │──MCP──│  gam-appian-kb CLI   │
│  (with GAM Power)   │       │  (runs locally)      │
└─────────────────────┘       └──────────┬───────────┘
                                         │ GitHub API
                                         ▼
                              ┌──────────────────────┐
                              │  GitHub Repository    │
                              │  ram-020998/gam-appian-kb  │
                              │                       │
                              │  data/                │
                              │  ├── SourceSelection/ │
                              │  ├── ReqMgmt/         │
                              │  └── ...              │
                              └──────────────────────┘
```

---

## For Administrators (One-Time Setup)

### Step 1: Create the GitHub Repository

1. Go to https://github.com/new
2. Create a repository:
   - **Name**: `gam-appian-kb`
   - **Visibility**: Private (recommended) or Public
   - **Initialize**: Add a README
3. Clone it locally:
   ```bash
   git clone https://github.com/ram-020998/gam-appian-kb.git
   cd gam-appian-kb
   ```

### Step 2: Parse Appian Applications

For each GAM application package:

```bash
cd /path/to/appian-parser
source .venv/bin/activate

# Parse the package into the repo's data directory
python -m appian_parser dump MyApplication.zip /path/to/gam-appian-kb/data/MyApplication
```

The output structure will be:
```
gam-appian-kb/
└── data/
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

### Step 3: Push to GitHub

```bash
cd /path/to/gam-appian-kb
git add data/
git commit -m "Add parsed GAM applications"
git push origin main
```

### Step 4: Publish the Kiro Power

The power is located in the `power-appian-parser/` directory of the appian-parser repo.

1. Before publishing, update `power-appian-parser/mcp.json` with your actual GitHub org/repo:
   ```json
   {
     "mcpServers": {
       "gam-appian-kb": {
         "command": "gam-appian-kb",
         "args": ["--github", "ram-020998/gam-appian-kb"],
         "env": {
           "GITHUB_TOKEN": "${GITHUB_TOKEN}"
         }
       }
     }
   }
   ```
   Replace `ram-020998/gam-appian-kb` with your actual repository path.

2. Push the power to its own public GitHub repo (so team members can install it):
   ```bash
   cd /path/to/appian-parser
   
   # Create a separate repo for the power
   mkdir /tmp/power-gam-appian
   cp -r power-appian-parser/* /tmp/power-gam-appian/
   cd /tmp/power-gam-appian
   git init
   git add .
   git commit -m "GAM Appian Knowledge Base power"
   git remote add origin https://github.com/ram-020998/power-gam-appian.git
   git push -u origin main
   ```

### Step 5: Adding New Applications

When a new GAM application needs to be added:

```bash
# Parse the new package
cd /path/to/appian-parser
source .venv/bin/activate
python -m appian_parser dump NewApp.zip /path/to/gam-appian-kb/data/NewApp

# Push to GitHub
cd /path/to/gam-appian-kb
git add data/NewApp/
git commit -m "Add NewApp application"
git push origin main
```

All team members will see the new application immediately — no reinstall needed.

---

## For Team Members

### Step 1: Install the MCP Server CLI

This is a one-time install. Run in your terminal:

```bash
pipx install "gam-appian-kb @ git+https://github.com/ram-020998/gam-appian-kb.git#subdirectory=mcp_server"
```

Verify it installed:
```bash
gam-appian-kb --help
```

You should see:
```
usage: gam-appian-kb [-h] (--data-dir DATA_DIR | --github OWNER/REPO)
                     [--branch BRANCH] [--data-prefix DATA_PREFIX]
```

### Step 2: Create a GitHub Personal Access Token

1. Go to https://github.com/settings/tokens?type=beta
2. Click **Generate new token**
3. Configure:
   - **Token name**: `gam-appian-kb`
   - **Expiration**: 90 days (or your preference)
   - **Repository access**: Select **Only select repositories** → choose `ram-020998/gam-appian-kb`
   - **Permissions**: Under **Repository permissions**, set **Contents** → **Read-only**
4. Click **Generate token**
5. Copy the token (starts with `github_pat_...`) — you won't see it again

### Step 3: Install the Kiro Power

**In Kiro IDE:**
1. Open the Powers panel (sidebar)
2. Click **Add power from GitHub**
3. Enter the power repo URL: `https://github.com/ram-020998/power-gam-appian`
4. When prompted for `GITHUB_TOKEN`, paste your token from Step 2

**In Kiro CLI:**
Add to your project's `.kiro/settings/mcp.json`:
```json
{
  "mcpServers": {
    "gam-appian-kb": {
      "command": "gam-appian-kb",
      "args": ["--github", "ram-020998/gam-appian-kb"],
      "env": {
        "GITHUB_TOKEN": "github_pat_YOUR_TOKEN_HERE"
      }
    }
  }
}
```

### Step 4: Start Using It

The power activates automatically when you mention Appian, GAM, or related keywords. Try:

- *"What GAM applications are available?"*
- *"Show me the evaluation actions in SourceSelection"*
- *"How does the vendor proposal process work?"*
- *"What depends on AS_CO_UT_isBlank?"*
- *"Give me an overview of the SourceSelection app"*

---

## Available Tools

Once connected, Kiro has access to 6 tools:

| Tool | What it does | When to use |
|---|---|---|
| `list_applications` | Lists all GAM apps with object counts and bundle stats | Discover what's available |
| `get_app_overview` | Full app map: metadata, all bundles, dependency summary, orphan count | Understand an app in one call |
| `search_bundles` | Find bundles by keyword, optional type filter | Locate specific functionality |
| `get_bundle` | Load bundle content (summary or full detail) | Analyze specific workflows |
| `search_objects` | Search objects by name and type | Find specific interfaces, rules, etc. |
| `get_dependencies` | Inbound + outbound dependency graph for an object | Trace relationships and impact |

### Bundle Types

| Type | What it represents |
|---|---|
| `action` | Record type action → process model → form → all dependencies |
| `process` | Standalone process model → subprocesses → interfaces |
| `page` | Record type views → interfaces → supporting objects |
| `site` | Site navigation → all page targets |
| `dashboard` | Control panel → interfaces → record types |
| `web_api` | API endpoint → all called rules/integrations |

---

## Troubleshooting

### "command not found: gam-appian-kb"
The CLI isn't installed or not on your PATH. Reinstall:
```bash
pip install "gam-appian-kb @ git+https://github.com/ram-020998/gam-appian-kb.git#subdirectory=mcp_server"
```
If using a virtual environment, make sure it's activated.

### "Application not found" errors
The application hasn't been parsed and pushed to the GitHub repo yet. Ask your admin to add it.

### Slow responses
First call for each file fetches from GitHub (~200-500ms). Subsequent calls for the same data are cached in memory and instant. If consistently slow, check your network connection.

### GitHub rate limit errors
- **Without token**: 60 requests/hour (will hit limits quickly)
- **With token**: 5,000 requests/hour (plenty for normal use)

Make sure your `GITHUB_TOKEN` is set correctly.

### Token expired
Generate a new token (Step 2 above) and update your Kiro power configuration.

---

## Updating

### Updating the MCP Server CLI
```bash
pip install --upgrade "gam-appian-kb @ git+https://github.com/ram-020998/gam-appian-kb.git#subdirectory=mcp_server"
```

### Updating Application Data
Admins parse and push new data. Team members get updates automatically — no action needed.
