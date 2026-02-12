# appian-parser

A standalone Python library that parses Appian application packages (ZIP files containing XML/XSD) into structured JSON. Zero external dependencies at runtime — runs entirely on Python stdlib.

Extracts all 15 Appian object types, resolves UUID/URN references to human-readable names, builds a complete inter-object dependency graph, and writes everything to a structured JSON output directory with self-contained LLM-readable bundles.

## Requirements

- Python 3.10+
- No runtime dependencies (stdlib only)
- Dev dependencies: `pytest`, `pytest-cov`

## Installation

```bash
cd appian-parser

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

# Install in editable mode
pip install -e .

# Install dev dependencies
pip install pytest pytest-cov

# Verify
python -m appian_parser types
```

Once the venv is activated, both `python` and `appian-parser` commands are available:

```bash
# These are equivalent
python -m appian_parser dump <package.zip> <output_dir>
appian-parser dump <package.zip> <output_dir>
```

## Quick Start

```bash
# Parse a package and dump JSON + bundles
python -m appian_parser dump MyApplication.zip ./output

# List supported object types
python -m appian_parser types
```

Output:
```
Parsing MyApplication.zip...
Done! Parsed 2304 objects (0 errors)
Output: ./output
```

## CLI Reference

### `dump` — Parse package and write JSON

```bash
python -m appian_parser dump <package.zip> <output_dir> [options]
```

| Option | Default | Description |
|---|---|---|
| `--locale LOCALE` | `en-US` | Locale for translation string resolution |
| `--exclude-types TYPES` | none | Comma-separated object types to exclude |
| `--no-deps` | false | Skip dependency analysis and bundle generation |
| `--no-pretty` | false | Disable JSON pretty-printing (smaller files) |

Examples:

```bash
# Basic usage
python -m appian_parser dump MyApp.zip ./output

# Skip dependency analysis (faster, no bundles)
python -m appian_parser dump MyApp.zip ./output --no-deps

# Spanish locale, exclude groups
python -m appian_parser dump MyApp.zip ./output --locale es-ES --exclude-types "Group,Translation String"
```

### `types` — List supported object types

```bash
python -m appian_parser types
```

## Output Directory Structure

```
output_dir/
├── manifest.json              # Package metadata, object inventory
├── dependencies.json          # Complete inter-object dependency graph
├── errors.json                # Parsing errors (only if errors occurred)
└── bundles/                   # Self-contained LLM documentation bundles
    ├── _index.json            # Bundle index with coverage stats
    ├── _orphans.json          # Objects not reachable from any entry point
    ├── actions/               # Record type action bundles
    ├── processes/             # Standalone process model bundles
    ├── pages/                 # Record type view/page bundles
    ├── sites/                 # Site navigation bundles
    ├── dashboards/            # Control panel/dashboard bundles
    └── web_apis/              # Web API endpoint bundles
```

## Bundle System

Each bundle is a self-contained JSON file representing a complete functional flow with its full transitive dependency tree. Designed for LLM consumption — all UUIDs and URNs are resolved to human-readable names.

| Bundle Type | Entry Point | Description |
|---|---|---|
| `action` | Record Type Action | Record action + target process model + all deps |
| `process` | Standalone Process Model | PM not triggered by any action or subprocess |
| `page` | Record Type Views | Summary/detail views with their interfaces |
| `site` | Site | Navigation container + all page targets |
| `dashboard` | Control Panel | Dashboard + interfaces + record types |
| `web_api` | Web API | API endpoint + all called rules/integrations |

## Reference Resolution

The parser automatically resolves three types of opaque identifiers in SAIL code and structured fields:

| Type | Before (raw XML) | After (output JSON) |
|---|---|---|
| UUID references | `#"_a-0006eed1-..._43398"` | `rule!GetCustomerAddress` |
| Record type URNs | `urn:appian:record-field:v1:{rt}/{field}` | `recordType!Addresses.addressId` |
| Translation URNs | `urn:appian:translation-string:v1:{uuid}` | `"Bonding Required To Bid"` |

Resolution is performed in-memory using data from the parsed objects themselves — no external database or API needed.

### Resolution Accuracy

| Package | UUID Resolution | RT URN Resolution |
|---|---|---|
| SourceSelection (2,327 objects) | 99.97% | 98.1% |
| RequirementsManagement (3,494 objects) | ~99.9% | ~92% |

## Supported Object Types

| Object Type | Key Fields Extracted |
|---|---|
| Interface | SAIL code, parameters, test inputs, security |
| Expression Rule | SAIL code, inputs, output type, test cases |
| Process Model | Nodes, flows, variables, gateway conditions, complexity score |
| Record Type | Fields, relationships, views, actions with expressions |
| CDT | Namespace, field definitions (name, type, required) |
| Integration | Connected system, HTTP method, URL, headers, request body |
| Web API | SAIL code, URL alias, HTTP method, security |
| Site | Hierarchical pages, roles, branding expressions |
| Group | Members, parent group, group type |
| Constant | Value, type, scope |
| Connected System | Base URL, auth type, auth details |
| Control Panel | JSON settings, interfaces, record type references |
| Translation Set | Default locale, enabled locales |
| Translation String | Translations per locale |

## Architecture

```
ZIP Input
    │
    ▼
PackageReader          → Extract ZIP, discover XML/XSD files
    │
    ▼
TypeDetector           → Determine object type from XML root tag
    │
    ▼
ParserRegistry         → Route to appropriate parser (15 types)
    │
    ▼
Object Parsers (15)    → Extract structured data from XML
    │
    ▼
DiffHashService        → SHA-512 content hash per object
    │
    ▼
ReferenceResolver      → Resolve UUIDs, RT URNs, translation URNs
    │                     Coordinates: UUIDResolver, RecordTypeURNResolver,
    │                     TranslationResolver
    ▼
DependencyAnalyzer     → Extract inter-object dependency graph
    │
    ▼
Output Layer           → JSONDumper (per-object files)
                         BundleBuilder (self-contained LLM bundles)
                         ManifestBuilder (package metadata)
```

## Project Structure

```
appian_parser/
├── __init__.py                         # Package version
├── __main__.py                         # python -m entry point
├── cli.py                              # CLI orchestration
├── package_reader.py                   # ZIP extraction
├── type_detector.py                    # XML type detection
├── parser_registry.py                  # Parser factory/registry
├── diff_hash.py                        # SHA-512 content hashing
│
├── parsers/                            # 15 type-specific XML parsers
│   ├── base_parser.py                  # Abstract base class (ABC)
│   ├── interface_parser.py
│   ├── expression_rule_parser.py
│   ├── process_model_parser.py
│   ├── record_type_parser.py
│   ├── cdt_parser.py
│   ├── integration_parser.py
│   ├── web_api_parser.py
│   ├── site_parser.py
│   ├── group_parser.py
│   ├── constant_parser.py
│   ├── connected_system_parser.py
│   ├── control_panel_parser.py
│   ├── translation_set_parser.py
│   ├── translation_string_parser.py
│   └── unknown_object_parser.py
│
├── domain/                             # Domain knowledge & shared config
│   ├── constants.py                    # Shared regex patterns, field paths, type maps
│   ├── field_walker.py                 # Dotted field path walker utility
│   ├── enums.py                        # DependencyTypeEnum
│   ├── appian_type_resolver.py         # XSD/Appian type name resolution
│   └── node_types/                     # Process model node type registry
│       ├── categories.py
│       └── registry.py
│
├── resolution/                         # UUID/URN reference resolution
│   ├── reference_resolver.py           # Coordinator: builds caches, walks fields
│   ├── uuid_resolver.py               # UUID → rule!/cons!/type!
│   ├── record_type_resolver.py         # RT URN → recordType!Name.field
│   ├── translation_resolver.py         # Translation URN → translated text
│   └── uuid_utils.py                  # UUID format detection and extraction
│
├── dependencies/                       # Dependency extraction
│   └── analyzer.py                     # Pattern-based dependency graph builder
│
└── output/                             # JSON output generation
    ├── json_dumper.py                  # Per-object JSON files
    ├── manifest_builder.py             # Package metadata
    └── bundle_builder.py              # Self-contained LLM bundles

tests/                                  # Test suite (pytest)
├── conftest.py                         # Shared fixtures and sample XML
├── test_type_detector.py
├── test_package_reader.py
├── test_diff_hash.py
├── test_field_walker.py
├── test_cli.py                         # End-to-end integration tests
├── parsers/
│   └── test_parsers.py
├── resolution/
│   ├── test_uuid_resolver.py
│   ├── test_record_type_resolver.py
│   ├── test_translation_resolver.py
│   └── test_reference_resolver.py
└── dependencies/
    └── test_analyzer.py

docs/                                   # Steering documents
├── PROJECT_OVERVIEW.md                 # Architecture and domain context
└── BEST_PRACTICES.md                   # OOP standards and coding conventions
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=appian_parser --cov-report=term-missing

# Run specific test module
python -m pytest tests/resolution/test_uuid_resolver.py -v
```

### Test Coverage

Core modules have high coverage:

| Module | Coverage |
|---|---|
| `reference_resolver.py` | 96% |
| `translation_resolver.py` | 100% |
| `uuid_resolver.py` | 89% |
| `record_type_resolver.py` | 73% |
| `field_walker.py` | 93% |
| `uuid_utils.py` | 96% |
| `package_reader.py` | 100% |
| `parser_registry.py` | 100% |
| `type_detector.py` | 93% |
| `manifest_builder.py` | 100% |
| `constants.py` | 94% |
| `diff_hash.py` | 100% |

## Python API

```python
from appian_parser.package_reader import PackageReader
from appian_parser.type_detector import TypeDetector
from appian_parser.parser_registry import ParserRegistry
from appian_parser.diff_hash import DiffHashService
from appian_parser.resolution.reference_resolver import ReferenceResolver
from appian_parser.dependencies.analyzer import DependencyAnalyzer
from appian_parser.output.json_dumper import ParsedObject

# 1. Read package
reader = PackageReader()
contents = reader.read("MyApp.zip")

# 2. Detect types and parse
detector = TypeDetector()
registry = ParserRegistry()
parsed_objects = []

for xml_file in contents.xml_files:
    detection = detector.detect(xml_file)
    if detection.is_excluded or detection.is_unknown:
        continue
    parser = registry.get_parser(detection.mapped_type)
    data = parser.parse(xml_file)
    if data and data.get("uuid"):
        parsed_objects.append(ParsedObject(
            uuid=data["uuid"],
            name=data.get("name", "Unknown"),
            object_type=detection.mapped_type,
            data=data,
            diff_hash=DiffHashService.generate_hash(data),
            source_file=xml_file,
        ))

# 3. Resolve references (mutates in place)
resolver = ReferenceResolver(parsed_objects)
resolver.resolve_all(parsed_objects, locale="en-US")

# 4. Analyze dependencies
analyzer = DependencyAnalyzer()
dependencies = analyzer.analyze(parsed_objects)

# 5. Use the data
for obj in parsed_objects:
    print(f"{obj.object_type}: {obj.name}")

reader.cleanup(contents.temp_dir)
```

## Design Principles

- **Zero runtime dependencies** — stdlib only
- **Single Responsibility** — each class has one job
- **Open/Closed** — new object types = new parser class, no existing code changes
- **Declarative configuration** — field paths for resolution/analysis are data, not code
- **In-memory resolution** — all lookups built from parsed objects, no external APIs
- **Immutable value objects** — `Dependency` is a frozen dataclass
- **Shared constants** — regex patterns, field paths, type maps centralized in `domain/constants.py`

See `docs/BEST_PRACTICES.md` for full coding standards and `docs/PROJECT_OVERVIEW.md` for detailed architecture.

## Performance

| Package | Objects | Time |
|---|---|---|
| SourceSelection v2.6.0 | 2,327 | ~2s |
| RequirementsManagement v2.3.0 | 3,494 | ~3s |

## License

Internal use.
