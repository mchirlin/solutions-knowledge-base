# Project Overview — Appian Package Parser

## Purpose

A standalone Python library that parses Appian application packages (ZIP files containing XML/XSD) into structured, LLM-readable JSON. Zero external dependencies — runs entirely on Python 3.10+ stdlib.

The primary goal is to enable reverse-engineering of Appian business logic by producing self-contained JSON bundles where every opaque identifier (UUID, URN) is resolved to a human-readable name.

## Domain Context

### What is Appian?

Appian is a low-code enterprise platform. Applications are built using:

- **SAIL** (Self-Assembling Interface Layer) — expression language for UI and logic
- **Process Models** — BPMN-like workflows with nodes, flows, and variables
- **Record Types** — data entities (like database tables) with fields, relationships, views, and actions
- **Interfaces** — SAIL-based UI components (forms, screens, dialogs)
- **Expression Rules** — reusable business logic functions
- **Integrations** — outbound API calls via Connected Systems
- **Web APIs** — inbound API endpoints
- **Sites** — top-level navigation containers
- **CDTs** (Custom Data Types) — user-defined data structures stored as XSD

### Package Format

Appian exports applications as ZIP files containing XML/XSD files. Each file wraps an object in a "Haul" format (e.g., `<interfaceHaul>`, `<processModelHaul>`) or a `<contentHaul>` wrapper with a child element indicating the type.

### Identifier Formats

Appian uses three types of opaque identifiers that this parser resolves:

| Type | Example | Resolves To |
|---|---|---|
| Prefixed UUID | `#"_a-0006eed1-0f7f-8000-0020-7f0000014e7a_43398"` | `rule!GetCustomerAddress` |
| Record Type URN | `urn:appian:record-field:v1:{rt_uuid}/{field_uuid}` | `recordType!Addresses.addressId` |
| Translation URN | `urn:appian:translation-string:v1:{uuid}` | `"Bonding Required To Bid"` |

UUIDs can have application suffixes (e.g., `-tmg-am-am`) that differ between references and definitions. The parser handles this via canonical prefix matching.

## Architecture

```
ZIP Input
    │
    ▼
┌─────────────────┐
│  PackageReader   │  Extract ZIP, discover XML/XSD files
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TypeDetector    │  Determine object type from XML root tag
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ParserRegistry   │  Route to appropriate parser (15 types)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Object Parsers   │  15 type-specific parsers (all extend BaseParser)
│ (parsers/)       │  Extract structured data from XML
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DiffHashService  │  SHA-512 content hash per object
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ ReferenceResolver     │  Resolve UUIDs, RT URNs, translation URNs
│ (resolution/)         │  Coordinates: UUIDResolver, RecordTypeURNResolver,
│                       │  TranslationResolver
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ DependencyAnalyzer    │  Extract inter-object dependency graph
│ (dependencies/)       │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Output Layer          │  JSONDumper: per-object JSON files
│ (output/)             │  BundleBuilder: self-contained LLM bundles
│                       │  ManifestBuilder: package metadata
└──────────────────────┘
```

## Module Map

```
appian_parser/
├── __init__.py                  # Package version
├── __main__.py                  # python -m entry point
├── cli.py                       # CLI orchestration (dump, types commands)
├── package_reader.py            # ZIP extraction → PackageContents
├── type_detector.py             # XML tag → object type mapping
├── parser_registry.py           # Object type → parser instance routing
├── diff_hash.py                 # SHA-512 content hashing
│
├── parsers/                     # 15 type-specific XML parsers
│   ├── base_parser.py           # Abstract base class (ABC)
│   ├── interface_parser.py      # SAIL code, parameters, test inputs
│   ├── expression_rule_parser.py# SAIL code, inputs, test cases
│   ├── process_model_parser.py  # Nodes, flows, variables, complexity
│   ├── record_type_parser.py    # Fields, relationships, views, actions
│   ├── cdt_parser.py            # Namespace, field definitions
│   ├── integration_parser.py    # HTTP config, connected system ref
│   ├── web_api_parser.py        # URL alias, HTTP method, SAIL code
│   ├── site_parser.py           # Hierarchical pages, branding
│   ├── group_parser.py          # Members, parent group
│   ├── constant_parser.py       # Value, type, scope
│   ├── connected_system_parser.py # Base URL, auth config
│   ├── control_panel_parser.py  # Dashboard config, interfaces
│   ├── translation_set_parser.py# Locales, security
│   ├── translation_string_parser.py # Per-locale translations
│   └── unknown_object_parser.py # Fallback parser
│
├── resolution/                  # Reference resolution (in-memory)
│   ├── reference_resolver.py    # Coordinator: builds caches, walks fields
│   ├── uuid_resolver.py         # UUID → rule!/cons!/type! in SAIL code
│   ├── record_type_resolver.py  # RT URN → recordType!Name.field
│   ├── translation_resolver.py  # Translation URN → translated text
│   └── uuid_utils.py            # UUID format detection and extraction
│
├── dependencies/                # Dependency extraction
│   └── analyzer.py              # Pattern-based dependency graph builder
│
├── domain/                      # Domain knowledge
│   ├── enums.py                 # DependencyTypeEnum
│   ├── appian_type_resolver.py  # XSD/Appian type name resolution
│   └── node_types/              # Process model node type registry
│       ├── categories.py        # NodeCategory enum
│       └── registry.py          # 80+ node type metadata entries
│
└── output/                      # JSON output generation
    ├── json_dumper.py           # Per-object JSON files + manifest + deps
    ├── manifest_builder.py      # Package metadata builder
    ├── bundle_builder.py        # Self-contained LLM documentation bundles
    └── doc_context_builder.py   # Pre-aggregated AI documentation context
```

## Data Flow

1. **PackageReader** extracts ZIP → temp directory, discovers XML/XSD files
2. **TypeDetector** inspects each XML root tag to determine object type
3. **ParserRegistry** routes to the correct parser based on detected type
4. Each **Parser** extracts structured data from XML into a Python dict
5. **DiffHashService** generates SHA-512 hash of each object's content
6. **ReferenceResolver** resolves all opaque identifiers in-memory:
   - Builds UUID lookup, record type cache, translation cache from parsed objects
   - Walks configured field paths per object type
   - Delegates to UUIDResolver, RecordTypeURNResolver, TranslationResolver
7. **DependencyAnalyzer** extracts inter-object dependencies via regex patterns
8. **Output layer** writes:
   - Per-object JSON files (JSONDumper)
   - Package manifest (ManifestBuilder)
   - Dependency graph (JSONDumper)
   - Self-contained bundles per entry point (BundleBuilder)

## Bundle System

The BundleBuilder produces self-contained JSON files for LLM consumption. Each bundle represents a complete functional flow:

| Bundle Type | Entry Point | Description |
|---|---|---|
| `action` | Record Type Action | Record action + target process model + all deps |
| `process` | Standalone Process Model | PM not triggered by any action or subprocess |
| `page` | Record Type Views | Summary/detail views with their interfaces |
| `site` | Site | Navigation container + all page targets |
| `dashboard` | Control Panel | Dashboard + interfaces + record types |
| `web_api` | Web API | API endpoint + all called rules/integrations |

Objects not reachable from any entry point go into `_orphans.json`.

## Key Design Decisions

1. **Zero external dependencies** — stdlib only (xml.etree, re, json, etc.)
2. **In-memory resolution** — all UUID/URN resolution uses data from the parsed objects themselves
3. **Canonical prefix matching** — handles cross-application-suffix UUID references
4. **Field path configuration** — resolver and analyzer use declarative field path lists per object type
5. **BFS graph walk** — bundles include full transitive dependency trees
6. **Mutation in place** — ReferenceResolver mutates parsed object data directly for efficiency

## CLI Commands

```bash
# Parse package → JSON output + bundles
python -m appian_parser dump <package.zip> <output_dir> [--locale LOCALE] [--no-deps] [--no-pretty]

# List supported object types
python -m appian_parser types
```

## Performance

| Package | Objects | Dependencies | Time |
|---|---|---|---|
| SourceSelection v2.6.0 | 2,327 | ~5,000+ | ~2s |
| RequirementsManagement v2.3.0 | 3,494 | ~7,000+ | ~3s |

## Resolution Accuracy

| Metric | SourceSelection | RequirementsManagement |
|---|---|---|
| UUID resolution | 99.97% | ~99.9% |
| RT URN resolution | 98.1% | ~92% |
| Remaining URNs | Multi-segment chains | Multi-segment chains |
