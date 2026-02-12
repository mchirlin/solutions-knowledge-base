---
name: "gam-appian"
displayName: "GAM Appian Knowledge Base"
description: "Central knowledge base for all Government Acquisition Management (GAM) Appian solutions. Browse application bundles, trace dependencies, search objects, and understand architecture across all GAM applications."
keywords: ["appian", "gam", "government acquisition", "acquisition management", "sail", "record type", "process model", "expression rule", "interface", "integration", "web api", "connected system", "cdt", "source selection", "requirements management", "appian bundle", "appian dependency"]
---

# Onboarding

## Step 1: Validate knowledge base access
Call the `list_applications` tool to verify available GAM applications. If no applications are found, a GAM application package needs to be parsed first:

```bash
cd /path/to/gam-appian-knowledge-base
source .venv/bin/activate
python -m appian_parser dump <package.zip> ./data/<AppName>
```

## Step 2: Understand the knowledge base
This is the central repository for all GAM Appian solution documentation. Each parsed application contains:

- **manifest.json** — Package metadata and full object inventory (15 Appian object types)
- **dependencies.json** — Complete inter-object dependency graph
- **bundles/** — Self-contained documentation bundles organized by entry point type

Bundle types:
| Type | Entry Point | Contents |
|---|---|---|
| action | Record Type Action | Action → process model → form interface → all deps |
| process | Standalone Process Model | PM → subprocesses → interfaces → deps |
| page | Record Type Views | Summary/detail views → interfaces → supporting objects |
| site | Site | Navigation → all page targets → interfaces |
| dashboard | Control Panel | Dashboard → interfaces → record types |
| web_api | Web API | Endpoint → all called rules/integrations |

## Recommended workflow
1. `list_applications` → see all GAM apps
2. `get_app_overview(app)` → full map of one app (bundles, deps, object counts) in ONE call
3. `search_bundles(app, query)` → find relevant bundles by keyword
4. `get_bundle(app, file, "summary")` → preview before loading full content
5. `get_bundle(app, file, "full")` → load complete bundle only when needed

# When to Load Steering Files
- Exploring application structure, browsing bundles, understanding what an app does → `bundle-analysis.md`
- Tracing dependencies, impact analysis, finding shared utilities → `dependency-analysis.md`
