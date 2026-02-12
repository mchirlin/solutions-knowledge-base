"""Shared data models used across parser modules."""

from dataclasses import dataclass, field
from typing import Any


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
