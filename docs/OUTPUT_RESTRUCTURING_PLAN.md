# GAM Knowledge Base — Output Restructuring Plan

## Problem Statement

The current parser output was designed for general-purpose JSON dumps. When consumed via MCP by an LLM:

1. **Too many round-trips** — The LLM needs 3-5 calls just to orient itself (manifest + index + deps + bundle summary + bundle full)
2. **Oversized payloads** — Bundles embed full SAIL code inline (2MB+ files), even when the LLM only needs the flow structure
3. **No unified search** — Finding an object requires loading the entire manifest (364KB) and scanning
4. **Monolithic dependency file** — `dependencies.json` is 4.6MB; every dependency lookup loads the whole thing
5. **Inconsistent bundle shapes** — Action, process, site bundles all have different JSON structures, requiring the LLM to understand each format
6. **Orphan blob** — `_orphans.json` is 2.1MB with full data for all unbundled objects, no way to query individual orphans

## Design Principles

- **Single-fetch orientation** — One file gives the LLM everything it needs to navigate the entire app
- **Layered detail** — Structure first, code on demand
- **Consistent shapes** — All bundles follow the same schema
- **Pre-computed indexes** — Search and dependency lookups are instant
- **OOP with clear responsibilities** — Each output generator is a single class with one job

## Validation Baseline

Pre-restructuring output is preserved at `data/SourceSelection_backup_v1/` (129MB). This backup contains the complete old-format output and is used by the validation script (Phase 6) to verify data completeness after restructuring.

---

## New Output Structure

```
data/<AppName>/
├── app_overview.json              # ONE file: manifest + bundle index + dep summary + coverage
├── search_index.json              # Flat lookup: object_name → {type, uuid, bundles[], deps_out, deps_in}
├── errors.json                    # Parse errors (only if errors exist)
├── bundles/
│   ├── <bundle_id>/
│   │   ├── structure.json         # Flow structure, object names, relationships — NO code
│   │   └── code.json              # SAIL code keyed by object UUID — loaded only when needed
│   └── ...
├── orphans/
│   ├── _index.json                # Orphan catalog: {total, by_type: {type: [{uuid, name}]}}
│   └── <object_uuid>.json         # Per-orphan detail with code (same shape as objects/*.json + code)
└── objects/                       # Per-object dependency data (replaces monolithic dependencies.json)
    └── <object_uuid>.json         # {name, type, calls[], called_by[], bundles[]}
```

### Files Removed (no longer generated)

| Old File | Reason | Data Moved To |
|---|---|---|
| `manifest.json` | Replaced by `app_overview.json` | `app_overview.json` |
| `dependencies.json` | Replaced by per-object files | `objects/<uuid>.json` |
| `bundles/_index.json` | Replaced by `app_overview.json` | `app_overview.json` |
| `bundles/_orphans.json` | Replaced by per-orphan files | `orphans/` directory |
| `bundles/<type>/<name>.json` | Split into structure + code | `bundles/<id>/structure.json` + `code.json` |

### File Details

#### `app_overview.json` (~100-150KB, single fetch)
```json
{
  "_metadata": {
    "parser_version": "2.0.0",
    "generated_at": "...",
    "source_package": "SourceSelectionv2.6.0.zip"
  },
  "package_info": { "filename": "...", "total_objects": 2327, "total_xml_files": 2500, "total_errors": 5 },
  "object_counts": { "Interface": 472, "Expression Rule": 950, ... },
  "bundles": [
    {
      "id": "action__SourceSelection__Add_Vendors",
      "bundle_type": "action",
      "root_name": "AS GSS Evaluation - Add Vendors",
      "parent_name": "AS GSS Evaluation",
      "object_count": 180,
      "key_objects": ["AS_GSS_FM_addVendors", "AS_GSS_PM_addVendors"]
    }
  ],
  "dependency_summary": {
    "total": 9316,
    "by_type": { "CALLS": 5985, ... },
    "most_depended_on": [ { "name": "...", "type": "...", "inbound_count": 120 } ],
    "most_dependencies": [ { "name": "...", "type": "...", "outbound_count": 45 } ]
  },
  "coverage": { "total_objects": 2327, "bundled": 1790, "orphaned": 537 }
}
```

#### `search_index.json` (~200KB, cached after first fetch)
```json
{
  "AS_GSS_FM_addVendors": {
    "uuid": "...",
    "type": "Interface",
    "description": "Form to add vendors to an evaluation",
    "bundles": ["action__SourceSelection__Add_Vendors"],
    "deps_out": 12,
    "deps_in": 3
  }
}
```

Note: Keyed by object name (case-preserved). Appian naming conventions ensure uniqueness across types (e.g. `AS_GSS_FM_*` for interfaces, `AS_GSS_BL_*` for expression rules, `AS_GSS_PM_*` for process models). The `description` field may be `null` for object types where parsers don't extract descriptions (Constants, CDTs, Groups, Translation Sets).

#### `bundles/<id>/structure.json` (~5-50KB per bundle)
```json
{
  "_metadata": {
    "bundle_type": "action",
    "root_name": "AS GSS Evaluation - Add Vendors",
    "parent_name": "AS GSS Evaluation",
    "total_objects": 180
  },
  "entry_point": {
    "action_type": "RECORD_ACTION",
    "target_process": "AS_GSS_PM_addVendors",
    "form_interface": "AS_GSS_FM_addVendors"
  },
  "flow": {
    "process_model": {
      "name": "AS_GSS_PM_addVendors",
      "complexity_score": 4.5,
      "nodes": [
        { "name": "Start", "type": "START_EVENT", "next": ["Validate Input"] },
        { "name": "Validate Input", "type": "SCRIPT_TASK", "calls": ["AS_GSS_BL_validateVendors"], "next": ["Gateway"] },
        { "name": "Gateway", "type": "XOR_GATEWAY", "conditions": ["..."], "next": ["Save", "Error"] }
      ]
    },
    "subprocesses": []
  },
  "objects": [
    {
      "uuid": "...",
      "name": "AS_GSS_FM_addVendors",
      "type": "Interface",
      "description": "Form to add vendors",
      "parameters": [{ "name": "evaluation", "type": "Record" }],
      "calls": ["AS_GSS_BL_getVendorList", "AS_GSS_BL_validateVendors"],
      "called_by": ["AS_GSS_PM_addVendors"]
    }
  ]
}
```

#### `bundles/<id>/code.json` (~50KB-2MB per bundle)
```json
{
  "_metadata": { "bundle_id": "action__SourceSelection__Add_Vendors" },
  "objects": {
    "<uuid>": {
      "name": "AS_GSS_FM_addVendors",
      "type": "Interface",
      "sail_code": "a!localVariables(..."
    },
    "<uuid>": {
      "name": "AS_GSS_BL_validateVendors",
      "type": "Expression Rule",
      "sail_code": "..."
    }
  }
}
```

#### `objects/<uuid>.json` (~1-5KB per object)
```json
{
  "uuid": "...",
  "name": "AS_GSS_FM_addVendors",
  "type": "Interface",
  "description": "Form to add vendors to an evaluation",
  "bundles": ["action__SourceSelection__Add_Vendors", "page__SourceSelection__Evaluation"],
  "calls": [
    { "name": "AS_GSS_BL_getVendorList", "type": "Expression Rule", "dep_type": "CALLS" }
  ],
  "called_by": [
    { "name": "AS_GSS_PM_addVendors", "type": "Process Model", "dep_type": "CALLS" }
  ]
}
```

#### `orphans/_index.json` (~50KB)
```json
{
  "_metadata": {
    "description": "Objects not reachable from any entry point.",
    "total_objects": 537
  },
  "by_type": {
    "Expression Rule": [{ "uuid": "...", "name": "AS_GSS_BL_legacyHelper" }],
    "Constant": [{ "uuid": "...", "name": "AS_GSS_CONST_oldLimit" }]
  }
}
```

#### `orphans/<uuid>.json` (~1-10KB per orphan)
```json
{
  "uuid": "...",
  "name": "AS_GSS_BL_legacyHelper",
  "type": "Expression Rule",
  "description": "...",
  "sail_code": "...",
  "calls": [],
  "called_by": []
}
```

#### `errors.json` (only if parse errors exist)
```json
[
  { "file": "some_file.xml", "error": "Unexpected root element", "object_type": "Unknown" }
]
```

---

## Implementation Plan

### Rollout Order

Phases must be executed in this order due to data dependencies:

```
Phase 1 (New Output Generators)
    └─→ Phase 2 (Normalize Bundle Structure)  — depends on Phase 1 classes
         └─→ Phase 3 (Update CLI Orchestration) — wires Phase 1+2 together
              └─→ Phase 4 (Update MCP Server)   — consumes Phase 3 output
                   └─→ Phase 5 (GitHub DataSource Caching) — optimizes Phase 4
Phase 6 (Validation) — runs after Phase 3, before Phase 4
```

Phase 6 (Validation) can run as soon as Phase 3 produces output. Phase 4 and 5 can proceed in parallel once validation passes.

---

### Phase 1: New Output Generators (appian_parser/output/)

#### 1.1 `SearchIndexBuilder` (new class)

```
appian_parser/output/search_index_builder.py
```

**Responsibility:** Build the flat `search_index.json` from parsed objects, dependencies, and bundle assignments.

```python
class SearchIndexBuilder:
    """Builds a flat name → metadata lookup for all parsed objects."""

    def build(self, parsed_objects, dependencies, bundle_assignments) -> dict[str, dict]
    def write(self, index: dict, output_dir: str) -> None
```

- Input: `list[ParsedObject]`, `list[Dependency]`, `dict[str, list[str]]` (uuid → bundle_ids)
- Output: `search_index.json`
- Indexes by object name (case-preserved), includes type, UUID, description, bundle list, dep counts
- `description` will be `null` for object types whose parsers don't extract it (Constants, CDTs, Groups, Translation Sets, Translation Strings)

#### 1.2 `AppOverviewBuilder` (new class)

```
appian_parser/output/app_overview_builder.py
```

**Responsibility:** Build the single `app_overview.json` that combines manifest metadata, bundle index, dependency summary, and coverage stats.

```python
class AppOverviewBuilder:
    """Builds the single-fetch application overview."""

    def build(self, package_info, object_counts, bundle_entries, dependency_summary, coverage) -> dict
    def write(self, overview: dict, output_dir: str) -> None
```

- Replaces the need to separately fetch `manifest.json` + `bundles/_index.json` + dependency summary
- Includes `key_objects` per bundle (top 5 most-connected objects) for LLM orientation
- Includes `_metadata` with parser version and generation timestamp

#### 1.3 `BundleStructureBuilder` (refactor of BundleBuilder)

```
appian_parser/output/bundle_structure_builder.py
```

**Responsibility:** Build the `structure.json` for each bundle — flow diagrams, object metadata, relationships. No SAIL code.

```python
class BundleStructureBuilder:
    """Builds lightweight bundle structure files (no code)."""

    def build_structure(self, entry_point, objects, dep_outbound, dep_inbound, obj_map) -> dict
    def _build_flow(self, entry_point, objects, obj_map) -> dict
    def _build_flow_nodes(self, pm_data: dict, obj_map: dict) -> list[dict]
    def _build_object_entry(self, obj, dep_outbound, dep_inbound) -> dict
```

Key changes from current `BundleBuilder`:
- **Strips SAIL code** from object entries — only includes name, type, description, parameters, calls/called_by
- **Normalizes bundle shape** — all bundle types use the same top-level structure: `_metadata`, `entry_point`, `flow`, `objects`
- **Adds flow visualization** — for process bundles, transforms the raw `nodes[]` from `process_model_parser.py` into a simplified graph

**Flow node transformation detail:**

The current `process_model_parser.py` produces nodes with fields like `name`, `node_type`, `subprocess_uuid`, `interface_uuid`, `expressions`, `outgoing_connections`. The `_build_flow_nodes()` method transforms these into the simplified format:

```python
def _build_flow_nodes(self, pm_data: dict, obj_map: dict) -> list[dict]:
    """Transform raw PM nodes into a simplified directed graph."""
    nodes = pm_data.get('nodes', [])
    # Build node name lookup for resolving outgoing_connections
    # Map each node's outgoing_connections to "next" names
    # Extract calls[] from node expressions (rule!/cons! references)
    # Return: [{ name, type, calls[], next[], conditions[] }]
```

Source fields → Target fields mapping:
| PM Parser Field | Flow Node Field |
|---|---|
| `name` | `name` |
| `node_type` (from registry) | `type` (simplified: START_EVENT, END_EVENT, SCRIPT_TASK, USER_TASK, XOR_GATEWAY, AND_GATEWAY, SUBPROCESS) |
| `outgoing_connections[].target_name` | `next[]` |
| `expressions` (SAIL refs extracted) | `calls[]` |
| `subprocess_uuid` (resolved to name) | `subprocess` |
| `interface_uuid` (resolved to name) | `interface` |

#### 1.4 `BundleCodeBuilder` (new class)

```
appian_parser/output/bundle_code_builder.py
```

**Responsibility:** Build the `code.json` for each bundle — SAIL code keyed by object UUID.

```python
class BundleCodeBuilder:
    """Builds code-only bundle files, loaded on demand."""

    def build_code(self, objects: list[ParsedObject]) -> dict
    def write(self, bundle_id: str, code_data: dict, output_dir: str) -> None
```

- Only includes objects that have code (`sail_code`, `definition`, `form_expression`)
- Keyed by UUID for direct lookup
- Code fields to extract per object type:

| Object Type | Code Field(s) |
|---|---|
| Interface | `data.form_expression` |
| Expression Rule | `data.definition` |
| Web API | `data.sail_code` |
| Process Model | `data.nodes[].expressions` (concatenated per node) |
| Integration | `data.sail_code` |

#### 1.5 `ObjectDependencyWriter` (new class)

```
appian_parser/output/object_dependency_writer.py
```

**Responsibility:** Write per-object dependency files to `objects/` directory.

```python
class ObjectDependencyWriter:
    """Writes individual object dependency files."""

    def write_all(self, parsed_objects, dependencies, bundle_assignments, output_dir) -> None
    def _build_object_file(self, obj, outbound, inbound, bundles) -> dict
```

- Replaces the monolithic `dependencies.json` for per-object lookups
- Each file is 1-5KB — perfect for single-object MCP queries
- Writes files for ALL parsed objects (bundled + orphaned)

#### 1.6 `OrphanWriter` (new class)

```
appian_parser/output/orphan_writer.py
```

**Responsibility:** Write per-orphan files and orphan index to `orphans/` directory.

```python
class OrphanWriter:
    """Writes orphaned object files (objects not in any bundle)."""

    def write_all(self, orphan_objects: list[ParsedObject], dependencies, output_dir) -> None
    def _build_orphan_index(self, orphan_objects: list[ParsedObject]) -> dict
    def _build_orphan_file(self, obj: ParsedObject, outbound, inbound) -> dict
```

- Replaces the monolithic `_orphans.json` (2.1MB)
- `_index.json` has just names/UUIDs/types for browsing (~50KB)
- Individual files include code + deps for on-demand loading

#### 1.7 Refactor `BundleBuilder` (existing → `BundleCoordinator`)

The current `BundleBuilder` (835 lines) does too much. Refactor into a coordinator:

```python
class BundleCoordinator:
    """Orchestrates bundle generation using specialized builders."""

    def __init__(self, structure_builder, code_builder):
        ...

    def build_all(self, parsed_objects, dependencies, manifest, output_dir) -> dict[str, list[str]]:
        """Build all bundles. Returns bundle_assignments: uuid → list[bundle_id]."""
        entry_points = self._discover_entry_points(parsed_objects)
        bundle_assignments: dict[str, list[str]] = defaultdict(list)

        for ep in entry_points:
            objects = self._collect_bundle_objects(ep, ...)
            bundle_id = self._make_bundle_id(ep)

            # Track which objects belong to which bundles
            for obj in objects:
                bundle_assignments[obj.uuid].append(bundle_id)

            # Write structure (no code)
            structure = self.structure_builder.build_structure(ep, objects, ...)
            self._write_json(f"bundles/{bundle_id}/structure.json", structure)

            # Write code (separate file)
            code = self.code_builder.build_code(objects)
            self._write_json(f"bundles/{bundle_id}/code.json", code)

        return dict(bundle_assignments)
```

Entry point discovery, dependency walking, hub detection, and root UUID collection logic stays in the coordinator (extracted from current `BundleBuilder`). The coordinator returns `bundle_assignments` so downstream builders (`SearchIndexBuilder`, `ObjectDependencyWriter`, `OrphanWriter`) can use it.

**Methods extracted from current `BundleBuilder` into coordinator:**
- `_discover_entry_points()` — lines 175-258
- `_build_adjacency()` — lines 264-268
- `_build_dep_lookup()` — lines 270-278
- `_get_root_uuids()` — lines 280-330
- `_walk_deps()` — lines 355-380
- `_resolve_sail_refs()` — lines 332-353
- `_collect_page_uuids()` — lines 354-358
- Hub UUID detection — lines 90-100

---

### Phase 2: Normalize Bundle Structure

All bundle types produce the same JSON shape:

```json
{
  "_metadata": { "bundle_type": "...", "root_name": "...", "total_objects": N },
  "entry_point": { /* type-specific but consistent keys */ },
  "flow": { /* process flow if applicable, null otherwise */ },
  "objects": [ /* uniform object entries */ ]
}
```

#### `entry_point` normalization:

| Bundle Type | Entry Point Fields |
|---|---|
| action | `action_type`, `record_type`, `target_process`, `form_interface`, `expressions` |
| process | `complexity_score`, `total_nodes`, `start_form` |
| page | `record_type`, `views[]` (view_type, view_name, url_stub) |
| site | `url_stub`, `pages[]` (name, url_stub, target) |
| dashboard | `url_stub`, `primary_record_type`, `interfaces[]` |
| web_api | `http_method`, `url_alias`, `security` |

#### `flow` section:

- Present for `action` and `process` bundles (any bundle with a process model)
- `null` for `page`, `site`, `dashboard`, `web_api` bundles
- Contains `process_model` (root PM flow graph) and `subprocesses[]` (nested PM flow graphs)

#### `objects[]` normalization (same for all bundle types):

```json
{
  "uuid": "...",
  "name": "...",
  "type": "Interface",
  "description": "...",
  "parameters": [],
  "calls": ["name1", "name2"],
  "called_by": ["name3"]
}
```

No `data` blob — specific fields are promoted to top level:

| Object Type | Promoted Fields |
|---|---|
| Interface | `parameters` |
| Expression Rule | `parameters` |
| Process Model | (represented in `flow` section instead) |
| Record Type | `actions[]` (names only), `views[]` (names only) |
| CDT | `fields[]` (name, type) |
| Constant | `value`, `value_type` |
| Integration | `connected_system`, `http_method` |
| Web API | `url_alias`, `http_method` |
| Connected System | `system_type`, `base_url` |
| Site | `url_stub` |
| Control Panel | `url_stub` |

---

### Phase 3: Update CLI Orchestration

Update `cli.py` `dump_package()` to use the new builders:

```python
def dump_package(zip_path, output_dir, options):
    # ... existing parse + resolve + analyze (unchanged) ...

    # Build bundles and get assignment map
    coordinator = BundleCoordinator(
        BundleStructureBuilder(),
        BundleCodeBuilder(),
    )
    bundle_assignments = coordinator.build_all(parsed_objects, dependencies, manifest, output_dir)
    bundled_uuids = set(bundle_assignments.keys())

    # Build search index (all objects: bundled + orphaned)
    search_builder = SearchIndexBuilder()
    search_index = search_builder.build(parsed_objects, dependencies, bundle_assignments)
    search_builder.write(search_index, output_dir)

    # Build app overview
    overview_builder = AppOverviewBuilder()
    overview = overview_builder.build(
        package_info=manifest['package_info'],
        object_counts=manifest['object_inventory']['total_by_type'],
        bundle_entries=coordinator.get_index_entries(),
        dependency_summary=dep_summary,
        coverage={'total_objects': len(parsed_objects), 'bundled': len(bundled_uuids),
                  'orphaned': len(parsed_objects) - len(bundled_uuids)},
    )
    overview_builder.write(overview, output_dir)

    # Write per-object dependency files (all objects)
    dep_writer = ObjectDependencyWriter()
    dep_writer.write_all(parsed_objects, dependencies, bundle_assignments, output_dir)

    # Write orphan files
    orphans = [obj for obj in parsed_objects if obj.uuid not in bundled_uuids]
    orphan_writer = OrphanWriter()
    orphan_writer.write_all(orphans, dependencies, output_dir)

    # Write errors (unchanged)
    dumper = JSONDumper(output_dir, pretty=options.pretty)
    dumper.write_errors(errors)
```

**What's removed from `cli.py`:**
- `dumper.write_manifest(manifest)` — replaced by `AppOverviewBuilder`
- `dumper.write_dependencies(dependencies)` — replaced by `ObjectDependencyWriter`
- Direct `BundleBuilder` usage — replaced by `BundleCoordinator`

**What's unchanged in `cli.py`:**
- All parsing logic (PackageReader, TypeDetector, ParserRegistry)
- Resolution logic (ReferenceResolver, LabelBundleResolver)
- DependencyAnalyzer
- DiffHashService
- Error collection

---

### Phase 4: Update MCP Server

Update `mcp_server/server.py` tools to use the new structure:

| Tool | Before | After |
|---|---|---|
| `list_applications` | Reads `manifest.json` + `bundles/_index.json` | Reads `app_overview.json` (1 file) |
| `get_app_overview` | Reads `manifest.json` + `_index.json` + `dependencies.json` + `_orphans.json` (4 files, ~7MB) | Reads `app_overview.json` (1 file, ~100-150KB) |
| `search_bundles` | Reads `_index.json`, scans | Reads `app_overview.json` (already cached), filters |
| `search_objects` | Reads `manifest.json` (364KB), scans all objects | Reads `search_index.json` (200KB, cached), direct lookup |
| `get_bundle` (summary) | Reads full bundle (2MB), strips code client-side | Reads `structure.json` only (5-50KB) |
| `get_bundle` (full) | Reads full bundle (2MB) | Reads `structure.json` + `code.json` and merges |
| `get_dependencies` | Reads `dependencies.json` (4.6MB), linear scan | Reads `objects/<uuid>.json` (1-5KB) |

**New tools:**

| Tool | Description |
|---|---|
| `get_object_detail` | Reads `objects/<uuid>.json` — full dependency info for one object |
| `list_orphans` | Reads `orphans/_index.json` — browse unbundled objects |
| `get_orphan` | Reads `orphans/<uuid>.json` — full detail + code for one orphan |

**Removed tools:** None. All existing tool names are preserved with updated implementations.

**`_truncate()` helper:** Keep for safety but it should rarely trigger with the new smaller payloads.

---

### Phase 5: GitHub DataSource Caching

The current `GitHubDataSource` uses a simple `dict[str, dict]` cache with no eviction. With the new structure producing many small files (especially `objects/*.json`), update the caching strategy:

- `app_overview.json` — cached on first `get_app_overview` call, serves all subsequent navigation
- `search_index.json` — cached on first search, serves all subsequent searches
- `structure.json` — cached per bundle, small enough to cache many
- `code.json` — fetched only on demand, cached per bundle
- `objects/*.json` — fetched per object, use LRU cache (max 500 entries) to bound memory
- `orphans/_index.json` — cached on first `list_orphans` call
- `orphans/*.json` — fetched per orphan, shares LRU cache with objects

Add `maxsize` parameter to `GitHubDataSource.__init__()` and use `collections.OrderedDict` for LRU eviction on the `_cache` dict. The two "anchor" files (`app_overview.json`, `search_index.json`) are pinned and never evicted.

---

### Phase 6: Output Validation

**Responsibility:** Verify the new output contains all data elements from the old output.

```
scripts/validate_restructured_output.py
```

```python
"""Validates new output against the v1 backup.

Usage:
    python scripts/validate_restructured_output.py \
        --old data/SourceSelection_backup_v1 \
        --new data/SourceSelection
"""
```

**Validation checks:**

1. **Object completeness** — Every UUID in old `manifest.json` `object_inventory.by_type[].objects[]` exists in new `search_index.json`
2. **Object count match** — `app_overview.json` `object_counts` matches old `manifest.json` `object_inventory.total_by_type`
3. **Bundle completeness** — Every bundle in old `bundles/_index.json` has a corresponding `bundles/<id>/structure.json`
4. **Bundle object coverage** — For each bundle, the set of object UUIDs in new `structure.json` matches the set in the old flat bundle file
5. **Code preservation** — For each bundle, every object with SAIL code in the old bundle has a matching entry in new `code.json` with identical code content
6. **Dependency completeness** — Total dependency count from old `dependencies.json._metadata.total_dependencies` equals sum of all `calls[]` entries across all `objects/<uuid>.json` files
7. **Dependency accuracy** — For a sample of 50 objects, verify outbound/inbound deps in `objects/<uuid>.json` match the old `dependencies.json` entries
8. **Orphan completeness** — Every UUID in old `_orphans.json` exists in new `orphans/_index.json`
9. **Orphan code preservation** — For a sample of 20 orphans, verify code in `orphans/<uuid>.json` matches old `_orphans.json`
10. **Error preservation** — `errors.json` content matches old output (if errors existed)
11. **No data loss summary** — Print a table: `| Check | Old Count | New Count | Status |`

**Output:** Exit code 0 if all checks pass, non-zero with detailed failure report otherwise.

---

## Class Diagram

```
                        ┌──────────────────┐
                        │   CLI (cli.py)   │
                        │   dump_package() │
                        └────────┬─────────┘
                                 │ orchestrates
          ┌──────────────┬───────┼───────────┬──────────────┐
          │              │       │           │              │
          ▼              ▼       ▼           ▼              ▼
 ┌────────────────┐ ┌────────┐ ┌──────────┐ ┌────────────┐ ┌────────────┐
 │BundleCoordinator│ │Search  │ │  App     │ │  Object    │ │  Orphan    │
 │                │ │Index   │ │ Overview │ │ Dependency │ │  Writer    │
 │ -discover EPs  │ │Builder │ │ Builder  │ │  Writer    │ │            │
 │ -walk deps     │ │        │ │          │ │            │ │ -_index    │
 │ -assign objs   │ │-build()│ │-build()  │ │-write_all()│ │ -per-file  │
 │ -returns       │ │-write()│ │-write()  │ │            │ │-write_all()│
 │  assignments   │ └────────┘ └──────────┘ └────────────┘ └────────────┘
 └───────┬────────┘
         │ delegates
  ┌──────┴──────┐
  ▼             ▼
┌──────────┐ ┌──────────┐
│Structure │ │  Code    │
│Builder   │ │ Builder  │
│          │ │          │
│-structure│ │-code only│
│-flow     │ │-by UUID  │
│-no code  │ │          │
└──────────┘ └──────────┘

Existing (kept, modified):
┌──────────────┐
│  JSONDumper   │  (write_errors only; write_manifest and write_dependencies removed)
└──────────────┘

Existing (removed):
┌──────────────┐  ┌──────────────┐
│ManifestBuilder│ │BundleSummarizer│  (functionality absorbed into AppOverviewBuilder
│  (removed)   │  │  (removed)    │   and structure.json respectively)
└──────────────┘  └──────────────┘
```

---

## Impact on Existing Components

### `BundleSummarizer` — REMOVED

The `summarize` CLI command and `BundleSummarizer` class are removed. Their functionality is replaced by:
- `app_overview.json` provides the high-level bundle catalog that summaries provided
- `structure.json` per bundle provides the detailed object breakdown
- The MCP server's `get_bundle(detail_level='summary')` reading `structure.json` replaces the markdown summaries

The `summarize` subcommand is removed from `cli.py`'s argparse setup.

### `ManifestBuilder` — REMOVED

All manifest data is now produced by `AppOverviewBuilder`. The `ManifestBuilder` class and `manifest.json` output are removed.

### `JSONDumper` — SIMPLIFIED

- `write_manifest()` — removed (replaced by `AppOverviewBuilder`)
- `write_dependencies()` — removed (replaced by `ObjectDependencyWriter`)
- `write_objects()` — already unused in current `cli.py`, removed
- `write_errors()` — kept as-is
- Data classes (`ParsedObject`, `ParseError`, `DumpOptions`, `DumpResult`) — kept, moved to `appian_parser/domain/models.py` since they're used across modules

### `web/app.py` — NOT AFFECTED

The Flask web UI (`web/app.py`) invokes `dump_package()` and reads the output directory. Since `dump_package()` still accepts the same inputs and writes to the same `output_dir`, the web app only needs its output-reading logic updated if it directly reads `manifest.json` or `dependencies.json`. Verify and update as needed during Phase 3.

---

## Expected Impact

| Metric | Before | After |
|---|---|---|
| Calls to orient (app overview) | 3-4 files, ~5MB | 1 file, ~100-150KB |
| Search an object | Load 364KB manifest, scan | Load 200KB index (cached), direct lookup |
| Get bundle structure | Load 2MB bundle, strip code | Load 5-50KB structure.json |
| Get bundle code | Already loaded (2MB) | Load code.json on demand |
| Dependency lookup | Load 4.6MB, scan | Load 1-5KB per-object file |
| Browse orphans | Load 2.1MB _orphans.json | Load 50KB index, then 1-10KB per orphan |
| Typical query (end-to-end) | 5-8 MCP calls | 1-2 MCP calls |
| Total output size | ~129MB (few large files) | ~similar (many small files, same data) |
