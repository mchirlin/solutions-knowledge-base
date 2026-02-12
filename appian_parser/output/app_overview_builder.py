"""Builds the single-fetch app_overview.json."""

import json
import os
from datetime import datetime, timezone
from typing import Any


class AppOverviewBuilder:
    """Builds the single-fetch application overview."""

    def build(
        self,
        package_info: dict,
        object_counts: dict,
        bundle_entries: list[dict],
        dependency_summary: dict,
        coverage: dict,
    ) -> dict[str, Any]:
        return {
            '_metadata': {
                'parser_version': '2.0.0',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'source_package': package_info.get('filename', ''),
            },
            'package_info': package_info,
            'object_counts': object_counts,
            'bundles': bundle_entries,
            'dependency_summary': dependency_summary,
            'coverage': coverage,
        }

    @staticmethod
    def write(overview: dict, output_dir: str, pretty: bool = True) -> None:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, 'app_overview.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(overview, f, indent=2 if pretty else None, ensure_ascii=False, default=str)
