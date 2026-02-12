"""CLI for appian-parser."""

import argparse
import os
import sys
import time

from appian_parser.package_reader import PackageReader
from appian_parser.type_detector import TypeDetector
from appian_parser.parser_registry import ParserRegistry
from appian_parser.diff_hash import DiffHashService
from appian_parser.domain.models import ParsedObject, ParseError, DumpOptions, DumpResult
from appian_parser.output.json_dumper import JSONDumper
from appian_parser.resolution.reference_resolver import ReferenceResolver
from appian_parser.resolution.label_bundle_resolver import LabelBundleResolver
from appian_parser.dependencies.analyzer import DependencyAnalyzer
from appian_parser.output.bundle_coordinator import BundleCoordinator
from appian_parser.output.search_index_builder import SearchIndexBuilder
from appian_parser.output.app_overview_builder import AppOverviewBuilder
from appian_parser.output.object_dependency_writer import ObjectDependencyWriter
from appian_parser.output.orphan_writer import OrphanWriter


def _build_dependency_summary(dependencies: list) -> dict:
    """Build dependency summary stats from raw dependency list."""
    by_type: dict[str, int] = {}
    inbound: dict[str, int] = {}
    outbound: dict[str, int] = {}
    target_info: dict[str, dict] = {}
    source_info: dict[str, dict] = {}

    for d in dependencies:
        by_type[d.dependency_type] = by_type.get(d.dependency_type, 0) + 1
        inbound[d.target_uuid] = inbound.get(d.target_uuid, 0) + 1
        outbound[d.source_uuid] = outbound.get(d.source_uuid, 0) + 1
        target_info[d.target_uuid] = {'name': d.target_name, 'type': d.target_type}
        source_info[d.source_uuid] = {'name': d.source_name, 'type': d.source_type}

    most_depended = sorted(inbound.items(), key=lambda x: -x[1])[:20]
    most_deps = sorted(outbound.items(), key=lambda x: -x[1])[:20]

    return {
        'total': len(dependencies),
        'by_type': dict(sorted(by_type.items())),
        'most_depended_on': [
            {**target_info[uuid], 'inbound_count': count} for uuid, count in most_depended
        ],
        'most_dependencies': [
            {**source_info[uuid], 'outbound_count': count} for uuid, count in most_deps
        ],
    }


def dump_package(zip_path: str, output_dir: str, options: DumpOptions) -> DumpResult:
    """Main orchestration: ZIP -> parsed objects -> JSON output."""
    start_time = time.time()

    reader = PackageReader()
    detector = TypeDetector(excluded_types=options.excluded_types or None)
    registry = ParserRegistry()

    contents = reader.read(zip_path)

    try:
        parsed_objects: list[ParsedObject] = []
        errors: list[ParseError] = []

        for xml_file in contents.xml_files:
            detection = None
            try:
                detection = detector.detect(xml_file)
                if detection.is_excluded or detection.is_unknown:
                    continue

                parser = registry.get_parser(detection.mapped_type)
                parsed_data = parser.parse(xml_file)

                if not parsed_data or not parsed_data.get('uuid'):
                    continue

                diff_hash = DiffHashService.generate_hash(parsed_data)

                parsed_objects.append(ParsedObject(
                    uuid=parsed_data['uuid'],
                    name=parsed_data.get('name', 'Unknown'),
                    object_type=detection.mapped_type,
                    data=parsed_data,
                    diff_hash=diff_hash,
                    source_file=os.path.basename(xml_file),
                ))
            except Exception as e:
                errors.append(ParseError(
                    file=os.path.basename(xml_file),
                    error=str(e),
                    object_type=detection.mapped_type if detection else 'Unknown',
                ))

        # Resolve UUID/URN references in-memory
        label_lookup = LabelBundleResolver.build_lookup(contents.properties_files)
        resolver = ReferenceResolver(parsed_objects, label_lookup=label_lookup)
        resolver.resolve_all(parsed_objects, locale=options.locale)

        # Analyze dependencies
        dependencies = []
        if options.include_dependencies:
            analyzer = DependencyAnalyzer()
            dependencies = analyzer.analyze(parsed_objects)

        duration = time.time() - start_time

        # Build package info (replaces ManifestBuilder)
        by_type: dict[str, int] = {}
        for obj in parsed_objects:
            by_type[obj.object_type] = by_type.get(obj.object_type, 0) + 1

        package_info = {
            'filename': contents.zip_filename,
            'total_files_in_zip': contents.total_files,
            'total_xml_files': len(contents.xml_files),
            'total_parsed_objects': len(parsed_objects),
            'total_errors': len(errors),
            'parse_duration_seconds': round(duration, 2),
        }
        object_counts = dict(sorted(by_type.items()))

        # Build bundles and get assignment map
        bundle_assignments: dict[str, list[str]] = {}
        if options.include_dependencies and dependencies:
            coordinator = BundleCoordinator(pretty=options.pretty)
            bundle_assignments = coordinator.build_all(parsed_objects, dependencies, output_dir)
            bundle_entries = coordinator.get_index_entries()
        else:
            bundle_entries = []

        bundled_uuids = set(bundle_assignments.keys())

        # Build search index (all objects)
        search_builder = SearchIndexBuilder()
        search_index = search_builder.build(parsed_objects, dependencies, bundle_assignments)
        search_builder.write(search_index, output_dir, pretty=options.pretty)

        # Build dependency summary
        dep_summary = _build_dependency_summary(dependencies) if dependencies else {
            'total': 0, 'by_type': {}, 'most_depended_on': [], 'most_dependencies': [],
        }

        # Build app overview
        coverage = {
            'total_objects': len(parsed_objects),
            'bundled': len(bundled_uuids),
            'orphaned': len(parsed_objects) - len(bundled_uuids),
        }
        overview_builder = AppOverviewBuilder()
        overview = overview_builder.build(package_info, object_counts, bundle_entries, dep_summary, coverage)
        overview_builder.write(overview, output_dir, pretty=options.pretty)

        # Write per-object dependency files
        if dependencies:
            dep_writer = ObjectDependencyWriter()
            dep_writer.write_all(parsed_objects, dependencies, bundle_assignments, output_dir, pretty=options.pretty)

        # Write orphan files
        orphans = [obj for obj in parsed_objects if obj.uuid not in bundled_uuids]
        if orphans:
            orphan_writer = OrphanWriter()
            orphan_writer.write_all(orphans, dependencies, output_dir, pretty=options.pretty)

        # Write errors
        dumper = JSONDumper(output_dir, pretty=options.pretty)
        dumper.write_errors(errors)

        return DumpResult(
            total_files=len(contents.xml_files),
            objects_parsed=len(parsed_objects),
            errors_count=len(errors),
            output_dir=output_dir,
        )
    finally:
        reader.cleanup(contents.temp_dir)


def main():
    parser = argparse.ArgumentParser(prog='appian-parser', description='Appian package parser')
    subparsers = parser.add_subparsers(dest='command')

    # dump command
    dump_parser = subparsers.add_parser('dump', help='Parse package and dump JSON')
    dump_parser.add_argument('package', help='Path to Appian package ZIP file')
    dump_parser.add_argument('output', help='Output directory')
    dump_parser.add_argument('--exclude-types', help='Comma-separated types to exclude')
    dump_parser.add_argument('--no-pretty', action='store_true', help='Disable pretty printing')
    dump_parser.add_argument('--locale', default='en-US', help='Locale for translation resolution (default: en-US)')
    dump_parser.add_argument('--no-deps', action='store_true', help='Skip dependency analysis')

    # types command
    subparsers.add_parser('types', help='List supported object types')

    args = parser.parse_args()

    if args.command == 'dump':
        if not os.path.isfile(args.package):
            print(f"Error: {args.package} not found", file=sys.stderr)
            sys.exit(1)

        options = DumpOptions(
            pretty=not args.no_pretty,
            locale=args.locale,
            include_dependencies=not args.no_deps,
        )
        if args.exclude_types:
            options.excluded_types = set(args.exclude_types.split(','))

        print(f"Parsing {args.package}...")
        result = dump_package(args.package, args.output, options)
        print(f"Done! Parsed {result.objects_parsed} objects ({result.errors_count} errors)")
        print(f"Output: {result.output_dir}")

    elif args.command == 'types':
        registry = ParserRegistry()
        for t in sorted(registry.get_supported_types()):
            print(f"  {t}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
