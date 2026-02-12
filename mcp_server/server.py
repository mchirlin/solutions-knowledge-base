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
        manifest = ds.read_json(name, "manifest.json")
        info = manifest.get("package_info", {})
        coverage = {}
        bundle_types = {}
        if ds.file_exists(name, "bundles/_index.json"):
            index = ds.read_json(name, "bundles/_index.json")
            coverage = index.get("coverage", {})
            for b in index.get("bundles", []):
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

    Returns package metadata, object counts by type, bundle index, dependency
    summary (top shared utilities, dependency type breakdown), and orphan count.
    Use this as the starting point before drilling into specific bundles or objects.

    Args:
        app_name: Application folder name (from list_applications).
    """
    ds = _datasource()
    manifest = ds.read_json(app_name, "manifest.json")

    overview: dict = {
        "package_info": manifest.get("package_info", {}),
        "object_counts": manifest.get("object_inventory", {}).get("total_by_type", {}),
    }

    if not overview["object_counts"]:
        by_type = manifest.get("object_inventory", {}).get("by_type", {})
        overview["object_counts"] = {k: v.get("count", len(v.get("objects", []))) for k, v in by_type.items()}

    if ds.file_exists(app_name, "bundles/_index.json"):
        index = ds.read_json(app_name, "bundles/_index.json")
        overview["coverage"] = index.get("coverage", {})
        overview["bundles"] = [
            {
                "file": b["file"],
                "bundle_type": b["bundle_type"],
                "root_name": b["root_name"],
                "parent_name": b.get("parent_name"),
                "object_count": b["object_count"],
            }
            for b in index.get("bundles", [])
        ]

    if ds.file_exists(app_name, "dependencies.json"):
        deps = ds.read_json(app_name, "dependencies.json")
        overview["dependency_summary"] = {
            "total_dependencies": deps.get("_metadata", {}).get("total_dependencies"),
            "by_type": deps.get("dependency_summary", {}).get("by_type", {}),
            "most_depended_on": deps.get("dependency_summary", {}).get("most_depended_on", [])[:10],
            "most_dependencies": deps.get("dependency_summary", {}).get("most_dependencies", [])[:10],
        }

    if ds.file_exists(app_name, "bundles/_orphans.json"):
        orphans = ds.read_json(app_name, "bundles/_orphans.json")
        overview["orphan_count"] = orphans.get("_metadata", {}).get("total_objects", 0)

    return overview


@mcp.tool()
def search_bundles(app_name: str, query: str, bundle_type: str | None = None) -> list[dict]:
    """Search bundles by name within a GAM application.

    Use this to quickly find relevant bundles instead of browsing the full list.

    Args:
        app_name: Application folder name.
        query: Case-insensitive substring to match against bundle root names.
        bundle_type: Optional filter — one of: action, process, page, site, dashboard, web_api.
    """
    ds = _datasource()
    if not ds.file_exists(app_name, "bundles/_index.json"):
        return []
    index = ds.read_json(app_name, "bundles/_index.json")
    query_lower = query.lower()
    results = []
    for b in index.get("bundles", []):
        if bundle_type and b.get("bundle_type") != bundle_type:
            continue
        name = b.get("root_name", "")
        parent = b.get("parent_name", "") or ""
        if query_lower in name.lower() or query_lower in parent.lower():
            results.append({
                "file": b["file"],
                "bundle_type": b["bundle_type"],
                "root_name": name,
                "parent_name": b.get("parent_name"),
                "object_count": b["object_count"],
            })
    return results


@mcp.tool()
def get_bundle(app_name: str, bundle_file: str, detail_level: str = "full") -> dict | str:
    """Get a bundle's content at the requested detail level.

    Args:
        app_name: Application folder name.
        bundle_file: Relative path from bundles/ (e.g. "actions/My_Action.json").
                     Use search_bundles or get_app_overview to find available files.
        detail_level: "summary" for metadata + object names only (fast, small),
                      "full" for complete bundle with SAIL code and all data.
    """
    ds = _datasource()
    path = f"bundles/{bundle_file}"
    data = ds.read_json(app_name, path)

    if detail_level == "summary":
        summary: dict = {"_metadata": data.get("_metadata", {})}
        objects = []
        for key, val in data.items():
            if key == "_metadata":
                continue
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict) and "name" in item:
                        objects.append({"name": item["name"], "object_type": item.get("object_type"), "section": key})
            elif isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    if isinstance(sub_val, dict) and "name" in sub_val:
                        objects.append({"name": sub_val["name"], "object_type": sub_val.get("object_type"), "section": f"{key}.{sub_key}"})
                    elif isinstance(sub_val, list):
                        for item in sub_val:
                            if isinstance(item, dict) and "name" in item:
                                objects.append({"name": item["name"], "object_type": item.get("object_type"), "section": f"{key}.{sub_key}"})
        summary["objects"] = objects
        return summary

    return _truncate(data)


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
    manifest = ds.read_json(app_name, "manifest.json")
    inventory = manifest.get("object_inventory", {}).get("by_type", {})
    query_lower = query.lower()
    results = []
    for otype, info in inventory.items():
        if object_type and otype != object_type:
            continue
        for obj in info.get("objects", []):
            if query_lower in obj.get("name", "").lower():
                results.append({
                    "uuid": obj["uuid"],
                    "name": obj["name"],
                    "object_type": otype,
                })
    return results[:50]


@mcp.tool()
def get_dependencies(app_name: str, object_name: str) -> dict:
    """Get the dependency subgraph for a specific object (by name).

    Returns what the object calls (outbound) and what calls it (inbound).

    Args:
        app_name: Application folder name.
        object_name: Case-insensitive object name to look up.
    """
    ds = _datasource()
    data = ds.read_json(app_name, "dependencies.json")
    name_lower = object_name.lower()

    outbound, inbound = [], []
    for dep in data.get("dependencies", []):
        src, tgt = dep.get("source", {}), dep.get("target", {})
        if src.get("name", "").lower() == name_lower:
            outbound.append({
                "target": tgt.get("name"),
                "target_type": tgt.get("object_type"),
                "dependency_type": dep.get("dependency_type"),
            })
        if tgt.get("name", "").lower() == name_lower:
            inbound.append({
                "source": src.get("name"),
                "source_type": src.get("object_type"),
                "dependency_type": dep.get("dependency_type"),
            })
    return {
        "object_name": object_name,
        "outbound_count": len(outbound),
        "inbound_count": len(inbound),
        "calls": outbound[:100],
        "called_by": inbound[:100],
    }


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
