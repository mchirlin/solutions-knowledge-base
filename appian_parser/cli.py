"""CLI for appian-parser."""

import argparse
import os
import sys
import time

from appian_parser.package_reader import PackageReader
from appian_parser.type_detector import TypeDetector
from appian_parser.parser_registry import ParserRegistry
from appian_parser.diff_hash import DiffHashService
from appian_parser.output.json_dumper import JSONDumper, ParsedObject, ParseError, DumpOptions, DumpResult
from appian_parser.output.manifest_builder import ManifestBuilder
from appian_parser.resolution.reference_resolver import ReferenceResolver
from appian_parser.resolution.label_bundle_resolver import LabelBundleResolver
from appian_parser.dependencies.analyzer import DependencyAnalyzer
from appian_parser.output.bundle_builder import BundleBuilder
from appian_parser.output.bundle_summarizer import BundleSummarizer


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

        # Build manifest
        manifest = ManifestBuilder.build(
            zip_filename=contents.zip_filename,
            parsed_objects=parsed_objects,
            errors=errors,
            parse_duration=duration,
            total_xml_files=len(contents.xml_files),
            total_files_in_zip=contents.total_files,
        )

        # Write output
        dumper = JSONDumper(output_dir, pretty=options.pretty)
        dumper.write_manifest(manifest)
        dumper.write_dependencies(dependencies)
        dumper.write_errors(errors)

        # Generate documentation bundles per entry point
        if options.include_dependencies and dependencies:
            bundle_builder = BundleBuilder()
            bundle_builder.build_and_write(parsed_objects, dependencies, manifest, output_dir)

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

    # summarize command
    sum_parser = subparsers.add_parser('summarize', help='Generate one business summary file per bundle type')
    sum_parser.add_argument('output', help='Output directory (must contain bundles/)')

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

    elif args.command == 'summarize':
        bundles_dir = os.path.join(args.output, 'bundles')
        if not os.path.isdir(bundles_dir):
            print(f"Error: {bundles_dir} not found. Run 'dump' first.", file=sys.stderr)
            sys.exit(1)
        summarizer = BundleSummarizer()
        summaries_dir = summarizer.summarize(args.output)
        count = len([f for f in os.listdir(summaries_dir) if f.endswith('.md')])
        print(f"Done! Wrote {count} summary file(s) to {summaries_dir}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
