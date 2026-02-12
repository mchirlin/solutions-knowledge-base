# Implementation Best Practices

## Python Version & Dependencies

- **Python 3.10+** required (for `X | Y` union syntax, `match` statements)
- **Zero external dependencies** — stdlib only. This is a hard constraint.
- Use `from __future__ import annotations` only if needed for forward references.

## OOP Standards

### Class Design

1. **Single Responsibility Principle (SRP)**: Each class has one reason to change.
   - Parsers parse XML → dict. They don't resolve references or write output.
   - Resolvers resolve identifiers. They don't parse XML or analyze dependencies.
   - The analyzer extracts dependencies. It doesn't resolve or output anything.

2. **Open/Closed Principle (OCP)**: Extend via new classes, not by modifying existing ones.
   - New object types → new parser class extending `BaseParser`.
   - New dependency types → add to `DependencyTypeEnum`, not restructure analyzer.
   - New bundle types → add entry point discovery logic, not restructure BundleBuilder.

3. **Liskov Substitution Principle (LSP)**: All parsers must be interchangeable via `BaseParser`.
   - Every parser's `parse()` returns a dict with at minimum `uuid` and `name`.
   - No parser should require special handling in the orchestration layer.

4. **Interface Segregation**: Keep interfaces minimal.
   - `BaseParser` defines only `parse()` as abstract. Helper methods are concrete.
   - Resolvers expose only `resolve_sail_code()` and `__init__()`.

5. **Dependency Inversion**: High-level modules depend on abstractions.
   - `cli.py` depends on `BaseParser` (via `ParserRegistry`), not concrete parsers.
   - `ReferenceResolver` depends on resolver interfaces, not their implementations.

### Abstract Base Classes

```python
from abc import ABC, abstractmethod

class BaseParser(ABC):
    """All parsers MUST inherit from this."""

    @abstractmethod
    def parse(self, xml_path: str) -> dict[str, Any]:
        """Parse XML file → structured dict with uuid, name, and type-specific fields."""
        ...
```

### Dataclasses for Value Objects

Use `@dataclass` for data containers. Use `@dataclass(frozen=True)` for immutable value objects.

```python
from dataclasses import dataclass

@dataclass
class ParsedObject:
    uuid: str
    name: str
    object_type: str
    data: dict[str, Any]
    diff_hash: str | None = None
    source_file: str = ''

@dataclass(frozen=True)
class Dependency:
    source_uuid: str
    source_name: str
    # ...
```

### Enums for Fixed Sets

```python
from enum import Enum

class DependencyTypeEnum(str, Enum):
    CALLS = 'CALLS'
    USES_CONSTANT = 'USES_CONSTANT'
    # ...
```

## Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Module files | `snake_case.py` | `record_type_parser.py` |
| Classes | `PascalCase` | `RecordTypeParser` |
| Methods/functions | `snake_case` | `resolve_sail_code` |
| Private methods | `_snake_case` | `_build_uuid_lookup` |
| Constants | `UPPER_SNAKE_CASE` | `TYPE_TO_FOLDER` |
| Module-level compiled regex | `_UPPER_SNAKE_CASE` | `_CANONICAL_RE` |
| Type aliases | `PascalCase` | `UUIDLookup = dict[str, dict[str, Any]]` |

## Type Annotations

- **All** public method signatures must have type annotations.
- Use modern syntax: `dict[str, Any]` not `Dict[str, Any]`, `str | None` not `Optional[str]`.
- Use `Any` sparingly — prefer specific types.

```python
# Good
def resolve_sail_code(self, code: str, locale: str = 'en-US') -> str: ...

# Bad
def resolve_sail_code(self, code, locale='en-US'): ...
```

## Docstrings

Use Google-style docstrings for all public classes and methods.

```python
class RecordTypeParser(BaseParser):
    """Parses Appian Record Type XML files.

    Extracts fields, relationships, views, and actions from record type
    definitions. Handles both source-backed and expression-backed record types.
    """

    def parse(self, xml_path: str) -> dict[str, Any]:
        """Parse a Record Type XML file.

        Args:
            xml_path: Absolute path to the XML file.

        Returns:
            Dict containing uuid, name, fields, relationships, views, actions.

        Raises:
            ValueError: If no record type element found in the XML.
        """
```

Private methods need only a brief one-liner docstring if the purpose isn't obvious from the name.

## Error Handling

1. **Parsers**: Raise `ValueError` for structural XML issues. The CLI catches all exceptions per-file and records them as `ParseError`.
2. **Resolvers**: Never raise. Return the original value if resolution fails.
3. **I/O**: Let `OSError`/`zipfile.BadZipFile` propagate — the CLI handles them.

```python
# Parser — fail explicitly
if constant_elem is None:
    raise ValueError(f"No constant element found in {xml_path}")

# Resolver — fail silently, return original
if rt_uuid not in self.record_types:
    return match.group(0)  # Return unmodified
```

## Regex Patterns

- Compile at **module level** for patterns used repeatedly.
- Use raw strings: `r'pattern'`.
- Use `re.IGNORECASE` for UUID patterns (hex can be upper or lower).
- Name patterns descriptively with `_UPPER_SNAKE_CASE`.

```python
# Module level — compiled once
_CANONICAL_RE = re.compile(
    r'(_[ae]-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_\d+)',
    re.I,
)

# Inside class — use class constant for patterns shared across methods
class RecordTypeURNResolver:
    _UUID = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}(?:-[\w-]+)?'
```

## Code Organization

### Module Structure

Each module should follow this order:
1. Module docstring
2. Imports (stdlib → third-party → local, separated by blank lines)
3. Module-level constants and compiled patterns
4. Classes
5. Module-level helper functions (if any, prefer class/static methods)

### Method Ordering Within Classes

1. `__init__`
2. Public methods (the class's API)
3. Private methods (in order of use by public methods)
4. Static/class methods

### Import Style

```python
# stdlib
import os
import re
from dataclasses import dataclass
from typing import Any

# local
from appian_parser.parsers.base_parser import BaseParser
from appian_parser.resolution.uuid_utils import UUIDUtils
```

## Configuration Over Code

Field paths for resolution and dependency extraction are declared as data, not hardcoded in logic:

```python
_SAIL_CODE_FIELDS: dict[str, list[str]] = {
    'Interface': ['sail_code'],
    'Expression Rule': ['sail_code'],
    'Process Model': [
        'nodes[].form_expression',
        'nodes[].gateway_conditions[].condition',
        'nodes[].subprocess_config.input_mappings[].expression',
    ],
    # ...
}
```

This makes it easy to add new fields without touching resolution/analysis logic.

## Testing Standards

### Framework

Use `pytest` as the test framework. Tests live in `tests/` mirroring the source structure:

```
tests/
├── conftest.py              # Shared fixtures
├── parsers/
│   ├── test_base_parser.py
│   ├── test_constant_parser.py
│   └── ...
├── resolution/
│   ├── test_uuid_resolver.py
│   ├── test_record_type_resolver.py
│   └── ...
├── dependencies/
│   └── test_analyzer.py
├── output/
│   └── test_bundle_builder.py
├── test_type_detector.py
├── test_package_reader.py
└── test_cli.py
```

### Test Naming

```python
def test_resolve_prefixed_uuid_returns_rule_name():
    """Test that a prefixed UUID resolves to rule!Name format."""

def test_resolve_unknown_uuid_returns_original():
    """Test that an unknown UUID is returned unchanged."""
```

### Fixtures

Use `pytest` fixtures for shared test data. Use `tmp_path` for file-based tests.

```python
@pytest.fixture
def sample_uuid_lookup():
    return {
        '_a-0006eed1-0f7f-8000-0020-7f0000014e7a_43398': {
            'name': 'GetCustomerAddress',
            'object_type': 'Expression Rule',
        }
    }
```

### Coverage Target

- Aim for **80%+ line coverage** on core modules (parsers, resolution, dependencies).
- 100% coverage on utility classes (`UUIDUtils`, `DiffHashService`).
- Integration tests for the full pipeline (ZIP → JSON output).

## Performance Guidelines

1. **Compile regex once** at module/class level, not inside loops.
2. **Use `setdefault`** for dict indexing to avoid overwriting.
3. **Iterate in reverse** when doing regex replacements to preserve match positions.
4. **BFS over DFS** for dependency graph walks (avoids stack overflow on deep graphs).
5. **Avoid unnecessary copies** — mutate in place where the API contract allows it.

## Git & Code Quality

- No `__pycache__`, `.DS_Store`, `.venv`, or `*.egg-info` in version control.
- `.gitignore` must cover all generated artifacts.
- No dead code or commented-out blocks in committed code.
- No `print()` statements in library code — only in `cli.py` for user output.
