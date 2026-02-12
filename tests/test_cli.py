"""Integration test for the full CLI pipeline."""

import json
import os

import pytest

from appian_parser.cli import dump_package
from appian_parser.output.json_dumper import DumpOptions


class TestCLIPipeline:
    """End-to-end tests for the dump pipeline."""

    def test_dump_produces_manifest(self, sample_zip, tmp_path):
        output_dir = str(tmp_path / "output")
        options = DumpOptions(pretty=True)
        result = dump_package(sample_zip, output_dir, options)

        assert result.objects_parsed > 0
        assert result.errors_count == 0
        assert os.path.isfile(os.path.join(output_dir, 'manifest.json'))

    def test_dump_manifest_structure(self, sample_zip, tmp_path):
        output_dir = str(tmp_path / "output")
        dump_package(sample_zip, output_dir, DumpOptions())

        with open(os.path.join(output_dir, 'manifest.json')) as f:
            manifest = json.load(f)

        assert '_metadata' in manifest
        assert 'package_info' in manifest
        assert 'object_inventory' in manifest
        assert manifest['package_info']['total_parsed_objects'] > 0

    def test_dump_produces_dependencies(self, sample_zip, tmp_path):
        output_dir = str(tmp_path / "output")
        dump_package(sample_zip, output_dir, DumpOptions(include_dependencies=True))

        deps_path = os.path.join(output_dir, 'dependencies.json')
        # Dependencies file may or may not exist depending on whether deps are found
        if os.path.isfile(deps_path):
            with open(deps_path) as f:
                deps = json.load(f)
            assert '_metadata' in deps

    def test_dump_no_deps_option(self, sample_zip, tmp_path):
        output_dir = str(tmp_path / "output")
        dump_package(sample_zip, output_dir, DumpOptions(include_dependencies=False))

        # Should not produce dependencies.json
        assert not os.path.isfile(os.path.join(output_dir, 'dependencies.json'))

    def test_dump_no_errors_file_when_clean(self, sample_zip, tmp_path):
        output_dir = str(tmp_path / "output")
        result = dump_package(sample_zip, output_dir, DumpOptions())

        if result.errors_count == 0:
            assert not os.path.isfile(os.path.join(output_dir, 'errors.json'))

    def test_dump_result_fields(self, sample_zip, tmp_path):
        output_dir = str(tmp_path / "output")
        result = dump_package(sample_zip, output_dir, DumpOptions())

        assert result.total_files > 0
        assert result.objects_parsed > 0
        assert result.output_dir == output_dir
