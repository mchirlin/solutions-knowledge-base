"""
GAM Appian Knowledge Base — MCP Server.

Exposes parsed Appian application data (bundles, manifests, dependencies)
to LLM clients via the Model Context Protocol. Designed as the central
knowledge base for all Government Acquisition Management (GAM) Appian solutions.

Usage:
    # Local mode (reads from filesystem)
    python -m mcp_server --data-dir /path/to/data

    # GitHub mode (reads from a GitHub repo)
    python -m mcp_server --github owner/repo [--branch main] [--data-prefix data]

    Requires GITHUB_TOKEN env var for private repos (or to avoid rate limits).
"""

from __future__ import annotations

import json
import sys

from mcp.server.fastmcp import FastMCP

from mcp_server.datasource import DataSource, GitHubDataSource, LocalDataSource

# ── Globals ─────────────────────────────────────────────────────────────

_ds: DataSource | None = None
mcp = FastMCP("gam-appian-kb")


def _datasource() -> DataSource:
    if _ds is None:
        raise RuntimeError("Data source not initialized")
    return _ds


def _truncate(data: dict | list, max_chars: int = 80_000) -> dict | list | str:
    text = json.dumps(data, ensure_ascii=False)
    if len(text) <= max_chars:
        return data
    return {
        "_truncated": True,
        "_message": f"Response too large ({len(text):,} chars). Use get_bundle with detail_level='summary'.",
    }


# ── Tools ───────────────────────────────────────────────────────────────


@mcp.tool()
def list_applications() -> list[dict]:
    """List all GAM Appian applications available in the knowledge base.

    Returns application names, object counts, and bundle coverage stats.
    Call this first to discover what's available.
    """
    ds = _datasource()
    apps = []
    for name in ds.list_apps():
        overview = ds.read_json(name, "app_overview.json")
        info = overview.get("package_info", {})
        coverage = overview.get("coverage", {})
        bundles = overview.get("bundles", [])
        bundle_types: dict[str, int] = {}
        for b in bundles:
            bt = b.get("bundle_type", "unknown")
            bundle_types[bt] = bundle_types.get(bt, 0) + 1
        apps.append({
            "name": name,
            "total_objects": info.get("total_parsed_objects"),
            "total_errors": info.get("total_errors"),
            "bundle_coverage": coverage,
            "bundles_by_type": bundle_types,
        })
    return apps


@mcp.tool()
def get_app_overview(app_name: str) -> dict:
    """Get a comprehensive overview of a GAM application in a single call.

    Returns package metadata, object counts by type, bundle index with key objects,
    dependency summary (top shared utilities, dependency type breakdown), and coverage.
    Use this as the starting point before drilling into specific bundles or objects.

    Args:
        app_name: Application folder name (from list_applications).
    """
    return _datasource().read_json(app_name, "app_overview.json")


@mcp.tool()
def search_bundles(app_name: str, query: str, bundle_type: str | None = None) -> list[dict]:
    """Search bundles by name within a GAM application.

    Use this to quickly find relevant bundles instead of browsing the full list.

    Args:
        app_name: Application folder name.
        query: Case-insensitive substring to match against bundle root names.
        bundle_type: Optional filter — one of: action, process, page, site, dashboard, web_api.
    """
    overview = _datasource().read_json(app_name, "app_overview.json")
    query_lower = query.lower()
    results = []
    for b in overview.get("bundles", []):
        if bundle_type and b.get("bundle_type") != bundle_type:
            continue
        name = b.get("root_name", "")
        parent = b.get("parent_name", "") or ""
        if query_lower in name.lower() or query_lower in parent.lower():
            results.append(b)
    return results


@mcp.tool()
def search_objects(app_name: str, query: str, object_type: str | None = None) -> list[dict]:
    """Search parsed objects by name within a GAM application.

    Args:
        app_name: Application folder name.
        query: Case-insensitive substring to match against object names.
        object_type: Optional filter (e.g. "Interface", "Expression Rule", "Process Model",
                     "Record Type", "CDT", "Integration", "Web API", "Constant").
    """
    ds = _datasource()
    index = ds.read_json(app_name, "search_index.json")
    query_lower = query.lower()
    results = []
    for name, info in index.items():
        if object_type and info.get("type") != object_type:
            continue
        if query_lower in name.lower():
            results.append({"name": name, **info})
    return results[:50]


@mcp.tool()
def get_bundle(app_name: str, bundle_id: str, detail_level: str = "summary") -> dict | str:
    """Get a bundle's content at the requested detail level.

    Args:
        app_name: Application folder name.
        bundle_id: Bundle directory name (e.g. "AS_GSS_ConsensusReport_RECORD_-_Sign").
                   Use search_bundles or get_app_overview to find available bundles.
        detail_level: "summary" for structure only (fast, small, no code),
                      "full" for structure + SAIL code merged together.
    """
    ds = _datasource()
    structure = ds.read_json(app_name, f"bundles/{bundle_id}/structure.json")

    if detail_level == "summary":
        return structure

    # Full: merge code into structure
    code = ds.read_json(app_name, f"bundles/{bundle_id}/code.json")
    code_map = code.get("objects", {})
    for obj in structure.get("objects", []):
        uuid = obj.get("uuid")
        if uuid and uuid in code_map:
            obj["sail_code"] = code_map[uuid].get("sail_code")
    return _truncate(structure)


@mcp.tool()
def get_dependencies(app_name: str, object_name: str) -> dict:
    """Get the dependency subgraph for a specific object (by name).

    Returns what the object calls (outbound) and what calls it (inbound).

    Args:
        app_name: Application folder name.
        object_name: Case-insensitive object name to look up.
    """
    ds = _datasource()
    # Look up UUID from search index
    index = ds.read_json(app_name, "search_index.json")
    name_lower = object_name.lower()
    uuid = None
    for name, info in index.items():
        if name.lower() == name_lower:
            uuid = info.get("uuid")
            break

    if not uuid:
        return {"error": f"Object '{object_name}' not found", "object_name": object_name}

    obj_data = ds.read_json(app_name, f"objects/{uuid}.json")
    return obj_data


@mcp.tool()
def get_object_detail(app_name: str, object_uuid: str) -> dict:
    """Get full dependency and bundle info for a specific object by UUID.

    Args:
        app_name: Application folder name.
        object_uuid: The object's UUID.
    """
    return _datasource().read_json(app_name, f"objects/{object_uuid}.json")


@mcp.tool()
def list_orphans(app_name: str) -> dict:
    """List all orphaned objects (not reachable from any entry point).

    Args:
        app_name: Application folder name.
    """
    return _datasource().read_json(app_name, "orphans/_index.json")


@mcp.tool()
def get_orphan(app_name: str, object_uuid: str) -> dict:
    """Get full detail (including code) for an orphaned object.

    Args:
        app_name: Application folder name.
        object_uuid: The orphan object's UUID.
    """
    return _datasource().read_json(app_name, f"orphans/{object_uuid}.json")


# ── Entry point ─────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="GAM Appian Knowledge Base MCP Server")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--data-dir", help="Local directory containing parsed application folders")
    group.add_argument("--github", metavar="OWNER/REPO", help="GitHub repository (e.g. myorg/gam-appian-kb)")
    parser.add_argument("--branch", default="main", help="Git branch (default: main)")
    parser.add_argument("--data-prefix", default="data", help="Path prefix in repo for app folders (default: data)")

    args = parser.parse_args()

    global _ds
    if args.data_dir:
        import os
        data_dir = os.path.abspath(args.data_dir)
        if not os.path.isdir(data_dir):
            print(f"Error: {data_dir} is not a directory", file=sys.stderr)
            sys.exit(1)
        _ds = LocalDataSource(data_dir)
    else:
        parts = args.github.split("/", 1)
        if len(parts) != 2:
            print("Error: --github must be OWNER/REPO format", file=sys.stderr)
            sys.exit(1)
        _ds = GitHubDataSource(
            owner=parts[0],
            repo=parts[1],
            branch=args.branch,
            data_prefix=args.data_prefix,
        )

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
