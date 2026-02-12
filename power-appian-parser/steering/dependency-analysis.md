# Dependency Analysis

## Workflow: Tracing Dependencies

1. **Start with overview** — `get_app_overview(app)` includes the top 10 most-depended-on objects and dependency type breakdown. Check this first.
2. **Find the object** — `search_objects(app, query)` to locate by name
3. **Get its graph** — `get_dependencies(app, object_name)`:
   - `calls` — what this object depends on (outbound)
   - `called_by` — what depends on this object (inbound)
4. **Follow the chain** — call `get_dependencies` on targets to trace deeper

## Dependency Types

- **CALLS** — SAIL `rule!Name` calls
- **USES_CONSTANT** — SAIL `cons!Name` references
- **USES_RECORD_TYPE** — `recordType!Name` references
- **USES_CONNECTED_SYSTEM** — integration using a connected system
- **USES_SITE** — site references

## Common Analysis Patterns

### Impact analysis ("What breaks if I change X?")
1. `get_dependencies(app, "X")` → look at `called_by`
2. For each caller, check its `called_by` to understand blast radius
3. Cross-reference with bundles — if X appears in a bundle, the bundle shows full context

### Finding shared utilities
1. `get_app_overview(app)` → `dependency_summary.most_depended_on` shows the top shared utilities
2. High-inbound objects = wide impact on changes

### Understanding a process flow
1. `search_bundles(app, query, "process")` or `search_bundles(app, query, "action")`
2. Load the bundle — it contains PM nodes, flows, gateway conditions, and all called rules
3. Use `get_dependencies` on specific rules to understand data access patterns
