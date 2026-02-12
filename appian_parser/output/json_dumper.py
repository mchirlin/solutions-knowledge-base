"""JSON output generation.

Writes parsed objects, manifest, dependencies, and errors to a structured
JSON directory.
"""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from appian_parser.domain.constants import TYPE_TO_FOLDER


@dataclass
class ParsedObject:
    """A parsed Appian object with metadata."""

    uuid: str
    name: str
    object_type: str
    data: dict[str, Any]
    diff_hash: str | None = None
    source_file: str = ''


@dataclass
class ParseError:
    """A parsing error for a single file."""

    file: str
    error: str
    object_type: str = 'Unknown'


@dataclass
class DumpOptions:
    """Options controlling the dump output."""

    excluded_types: set[str] = field(default_factory=set)
    include_raw_xml: bool = False
    include_dependencies: bool = True
    locale: str = 'en-US'
    pretty: bool = True


@dataclass
class DumpResult:
    """Result summary of a dump operation."""

    total_files: int
    objects_parsed: int
    errors_count: int
    output_dir: str


def _sanitize_filename(name: str, uuid: str) -> str:
    """Create a safe filename from object name and UUID prefix."""
    sanitized = re.sub(r'[^\w\-]', '_', name or 'Unknown')[:80]
    prefix = uuid[:8] if uuid else 'no_uuid'
    return f"{sanitized}_{prefix}.json"


class JSONDumper:
    """Writes parsed objects to a structured JSON directory.

    Output structure:
        output_dir/
        ├── manifest.json
        ├── dependencies.json
        ├── errors.json (only if errors)
        └── objects/{type_folder}/{name}_{uuid_prefix}.json

    Args:
        output_dir: Root directory for output files.
        pretty: Whether to pretty-print JSON (default True).
    """

    def __init__(self, output_dir: str, pretty: bool = True) -> None:
        self._output_dir = output_dir
        self._indent = 2 if pretty else None

    def write_objects(self, objects: list[ParsedObject]) -> None:
        """Write each parsed object as an individual JSON file."""
        for obj in objects:
            folder = TYPE_TO_FOLDER.get(obj.object_type, 'unknown')
            dir_path = os.path.join(self._output_dir, 'objects', folder)
            os.makedirs(dir_path, exist_ok=True)

            envelope = {
                '_metadata': {
                    'parser_version': '1.0.0',
                    'parsed_at': datetime.now(timezone.utc).isoformat(),
                    'source_file': obj.source_file,
                    'object_type': obj.object_type,
                    'diff_hash': obj.diff_hash,
                },
                'uuid': obj.uuid,
                'name': obj.name,
                'object_type': obj.object_type,
                'data': obj.data,
            }
            filepath = os.path.join(dir_path, _sanitize_filename(obj.name, obj.uuid))
            self._write_json(filepath, envelope)

    def write_manifest(self, manifest: dict) -> None:
        """Write the package manifest."""
        os.makedirs(self._output_dir, exist_ok=True)
        self._write_json(os.path.join(self._output_dir, 'manifest.json'), manifest)

    def write_dependencies(self, dependencies: list) -> None:
        """Write the dependency graph."""
        if not dependencies:
            return
        os.makedirs(self._output_dir, exist_ok=True)

        by_type: dict[str, int] = {}
        inbound: dict[str, int] = {}
        outbound: dict[str, int] = {}
        target_info: dict[str, dict] = {}
        source_info: dict[str, dict] = {}

        for d in dependencies:
            by_type[d.dependency_type] = by_type.get(d.dependency_type, 0) + 1
            inbound[d.target_uuid] = inbound.get(d.target_uuid, 0) + 1
            outbound[d.source_uuid] = outbound.get(d.source_uuid, 0) + 1
            target_info[d.target_uuid] = {
                'uuid': d.target_uuid, 'name': d.target_name, 'object_type': d.target_type,
            }
            source_info[d.source_uuid] = {
                'uuid': d.source_uuid, 'name': d.source_name, 'object_type': d.source_type,
            }

        most_depended = sorted(inbound.items(), key=lambda x: -x[1])[:20]
        most_deps = sorted(outbound.items(), key=lambda x: -x[1])[:20]

        data = {
            '_metadata': {
                'total_dependencies': len(dependencies),
                'total_resolved': sum(1 for d in dependencies if d.is_resolved),
                'total_unresolved': sum(1 for d in dependencies if not d.is_resolved),
            },
            'dependency_summary': {
                'by_type': dict(sorted(by_type.items())),
                'most_depended_on': [
                    {**target_info[uuid], 'inbound_count': count} for uuid, count in most_depended
                ],
                'most_dependencies': [
                    {**source_info[uuid], 'outbound_count': count} for uuid, count in most_deps
                ],
            },
            'dependencies': [
                {
                    'source': {'uuid': d.source_uuid, 'name': d.source_name, 'object_type': d.source_type},
                    'target': {'uuid': d.target_uuid, 'name': d.target_name, 'object_type': d.target_type},
                    'dependency_type': d.dependency_type,
                    'reference_context': d.reference_context,
                    'is_resolved': d.is_resolved,
                }
                for d in dependencies
            ],
        }
        self._write_json(os.path.join(self._output_dir, 'dependencies.json'), data)

    def write_errors(self, errors: list[ParseError]) -> None:
        """Write parsing errors (only if any exist)."""
        if not errors:
            return
        os.makedirs(self._output_dir, exist_ok=True)
        data = [{'file': e.file, 'error': e.error, 'object_type': e.object_type} for e in errors]
        self._write_json(os.path.join(self._output_dir, 'errors.json'), data)

    def _write_json(self, path: str, data: Any) -> None:
        """Write data as JSON to a file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=self._indent, ensure_ascii=False, default=str)
