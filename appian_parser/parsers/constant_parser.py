"""
Parser for Appian Constant objects.

This module provides the ConstantParser class for extracting data from
Constant XML files.

Note: Value types are stored as raw values during parsing. Type resolution
to user-friendly display names is performed in post-extraction processing
when the record type cache is available.
"""

from typing import Dict, Any
import xml.etree.ElementTree as ET
from appian_parser.parsers.base_parser import BaseParser


class ConstantParser(BaseParser):
    """
    Parser for Appian Constant objects.

    Extracts value, type, and scope information from Constant XML files.
    """

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse Constant XML file and extract all relevant data.

        Args:
            xml_path: Path to the Constant XML file

        Returns:
            Dict containing:
            - uuid: Constant UUID
            - name: Constant name
            - version_uuid: Version UUID
            - description: Constant description
            - value: Constant value
            - value_type: Data type of the constant
            - scope: Scope of the constant (APPLICATION, SYSTEM, etc.)
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the constant element
        constant_elem = root.find('.//constant')
        if constant_elem is None:
            raise ValueError(f"No constant element found in {xml_path}")

        # Extract basic info - UUID and name are child elements
        data = {
            'uuid': self._get_text(constant_elem, 'uuid'),
            'name': self._get_text(constant_elem, 'name'),
            'version_uuid': self._get_text(root, './/versionUuid'),
            'description': self._get_text(constant_elem, 'description')
        }

        # Extract value from typedValue structure
        typed_value_elem = constant_elem.find('typedValue')
        if typed_value_elem is not None:
            value_elem = typed_value_elem.find('value')
            if value_elem is not None:
                data['value'] = value_elem.text
            else:
                data['value'] = None
        else:
            data['value'] = None

        # Extract value type from typedValue
        type_elem = None
        if typed_value_elem is not None:
            type_elem = typed_value_elem.find('type')
        if type_elem is None:
            type_elem = constant_elem.find('type')
        if type_elem is not None:
            type_name = type_elem.find('name')
            type_namespace = type_elem.find('namespace')

            if type_name is not None and type_name.text:
                raw_type = type_name.text
                if type_namespace is not None and type_namespace.text:
                    raw_type = f"{type_namespace.text}:{raw_type}"

                # Store raw type - will be resolved in post-extraction
                # with record type cache
                data['raw_value_type'] = raw_type
                data['value_type'] = raw_type
            else:
                data['value_type'] = None
                data['raw_value_type'] = None
        else:
            data['value_type'] = None
            data['raw_value_type'] = None

        # Extract scope
        data['scope'] = self._get_text(constant_elem, 'scope')

        return data
