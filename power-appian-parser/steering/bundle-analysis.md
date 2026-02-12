# Bundle Analysis

## Workflow: Exploring a GAM Application

**Always start with `get_app_overview`** — it returns everything you need in one call:
manifest, bundle index, dependency summary, and orphan count. This eliminates
the need for multiple discovery calls.

### Step-by-step

1. `get_app_overview(app)` → read the bundle list, object counts, and top shared utilities
2. `search_bundles(app, query)` → find specific bundles by keyword (e.g. "vendor", "evaluation", "task")
3. `get_bundle(app, file, "summary")` → preview: metadata + object names, no SAIL code
4. `get_bundle(app, file, "full")` → full content only when you need SAIL code or process flow details

**Do NOT call list_applications + get_manifest + list_bundles separately.** `get_app_overview` replaces all three.

## Reading Bundle Content

Each bundle is self-contained JSON with:
- `_metadata` — bundle type, root object, total object count
- Type-specific sections (e.g. `action`, `interface`, `process` for action bundles)
- Each object includes: `name`, `object_type`, `data`, `calls` (outbound), `called_by` (inbound)

### Key fields by object type

- **Interface**: `sail_code`, `parameters`, `test_inputs`
- **Expression Rule**: `sail_code`, `inputs`, `output_type`, `test_cases`
- **Process Model**: `nodes`, `flows`, `variables`, `complexity_score`
- **Record Type**: `fields`, `relationships`, `views`, `actions`
- **Integration**: `connected_system`, `http_method`, `url`, `request_body`
- **CDT**: `fields` (name, type, required)

## Answering Common Questions

- "What does this app do?" → `get_app_overview` then load site bundles — they show top-level navigation
- "How does action X work?" → `search_bundles(app, "X", "action")` → get summary → get full
- "What interfaces exist?" → `search_objects(app, query, "Interface")`
- "What's orphaned?" → check `orphan_count` in `get_app_overview`

## Bundle Size Awareness

Some bundles have 200+ objects (2MB+). Always use `detail_level="summary"` first.
Only load full content when specific SAIL code or process flow details are needed.
