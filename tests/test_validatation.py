#!/usr/bin/env python3

# pylint: disable=missing-docstring
# pylint: disable=invalid-slice-index

import unittest
from typing import Any, Dict  # pylint: disable=unused-import

import mapry.validation


class TestValidation(unittest.TestCase):
    def test_empty_schema(self) -> None:
        mapping = {}  # type: Dict[str, Any]

        errs = mapry.validation.validate(mapping=mapping, ref='#')

        self.assertEqual(1, len(errs))
        self.assertEqual(
            "#: Does not follow json schema: 'name' is a required property",
            str(errs[0]))

    def test_no_description(self) -> None:
        mapping = {"name": "Some_graph"}

        errs = mapry.validation.validate(mapping=mapping, ref='#')

        self.assertEqual(1, len(errs))
        self.assertEqual(
            "#: Does not follow json schema: "
            "'description' is a required property", str(errs[0]))

    def test_no_additional_properties(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some schema.",
            # Property 'embedes' was misspelled.
            "embedes": [
                {"name": "A", "description": "defines A."}
            ]
        }
        # yapf: enable

        errs = mapry.validation.validate(mapping=mapping, ref='#')
        self.assertEqual(1, len(errs))
        self.assertEqual(
            "#: Does not follow json schema: "
            "Additional properties are not allowed ('embedes' was unexpected)",
            str(errs[0]))

    def test_no_additional_property_in_nested(self) -> None:  # pylint: disable=invalid-name
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some schema.",
            "embeds": [
                {
                    "name": "A",
                    "description": "defines A.",
                    "some_invalid_property": 0
                }
            ]
        }
        # yapf: enable

        errs = mapry.validation.validate(mapping=mapping, ref='#')
        self.assertEqual(1, len(errs))
        self.assertEqual(
            "#/embeds/0: Does not follow json schema: "
            "Additional properties are not allowed "
            "('some_invalid_property' was unexpected)", str(errs[0]))

    def test_duplicate_classes(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some schema.",
            "classes": [
                {"name": "Some_class", "description": "defines a class."},
                {"name": "Some_class", "description": "defines a class."}
            ]
        }
        # yapf: enable

        errs = mapry.validation.validate(mapping=mapping, ref='#')

        self.assertEqual(1, len(errs))
        self.assertEqual(
            "#/classes/1/name: Duplicate names: 'Some_class'", str(errs[0]))

    def test_duplicate_embeds(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some schema.",
            "embeds": [
                {"name": "A", "description": "defines A."},
                {"name": "A", "description": "defines A."}
            ]
        }
        # yapf: enable

        errs = mapry.validation.validate(mapping=mapping, ref='#')

        self.assertEqual(1, len(errs))
        self.assertEqual("#/embeds/1/name: Duplicate names: 'A'", str(errs[0]))

    def test_duplicate_class_and_embed(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some schema.",
            "classes": [
                {"name": "Some_name", "description": "defines a class."}
            ],
            "embeds": [
                {"name": "Some_name", "description": "defines an embed."}
            ]
        }
        # yapf: enable

        errs = mapry.validation.validate(mapping=mapping, ref='#')

        self.assertEqual(1, len(errs))
        self.assertEqual(
            "#/embeds/0/name: Duplicate names: 'Some_name'", str(errs[0]))

    def test_validate_class(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some schema.",
            "classes": [
                {
                    "name": "Some_class",
                    "description": "defines a class.",
                    "id_pattern": 'some invalid regex['
                }
            ]
        }
        # yapf: enable

        errs = mapry.validation.validate(mapping=mapping, ref='#')
        self.assertEqual(1, len(errs))
        self.assertEqual(
            "#/classes/0/id_pattern: "
            "Invalid regular expression: "
            "unterminated character set at position 18", str(errs[0]))

    def test_validate_properties(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some schema.",
            "properties": {
                "a": {
                    "type": "Some_invalid_type",
                    "description": "defines some invalid property."
                },
            },
            "classes": [
                {
                    "name": "Some_class",
                    "description": "defines a class.",
                    "properties": {
                        "a": {
                            "type": "invalid",
                            "description": "defines some invalid property."
                        },
                    }
                }
            ],
            "embeds": [
                {
                    "name": "Some_embed",
                    "description": "defines an embed.",
                    "properties": {
                        "a": {
                            "type": "invalid",
                            "description": "defines some invalid property."
                        },
                    }
                }
            ],
        }
        # yapf: enable

        errs = mapry.validation.validate(mapping=mapping, ref='#')
        self.assertEqual(3, len(errs))

        # yapf: disable
        self.assertEqual(
            "#/properties/a/type: Invalid type: Some_invalid_type",
            str(errs[0]))

        self.assertEqual(
            "#/classes/0/properties/a/type: Invalid type: invalid",
            str(errs[1]))

        self.assertEqual(
            "#/embeds/0/properties/a/type: Invalid type: invalid",
            str(errs[2]))
        # yapf: enable

    def test_validate_date_format(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some schema.",
            "properties": {
                "a": {
                    "type": "date",
                    "description": "date with an invalid format.",
                    "format": "%Y-%m-%d %H:%M:%S"}
            }
        }
        # yapf: enable

        errs = mapry.validation.validate(mapping=mapping, ref='#')
        self.assertEqual(1, len(errs))
        self.assertEqual(
            "#/properties/a/format: Unexpected directive '%H' in a date format",
            str(errs[0]))

    def test_validate_time_format(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some schema.",
            "properties": {
                "a": {
                    "type": "time",
                    "description": "time with an invalid format.",
                    "format": "%Y-%m-%d %H:%M:%S"}
            }
        }
        # yapf: enable

        errs = mapry.validation.validate(mapping=mapping, ref='#')
        self.assertEqual(1, len(errs))
        self.assertEqual(
            "#/properties/a/format: Unexpected directive '%Y' in a time format",
            str(errs[0]))

    def test_validate_plural_conflicts(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some schema.",
            "properties": {
                "dummies": {
                    "type": "string",
                    "description": "some property"
                },
                "noi_s": {
                    "type": "string",
                    "description": "another property"
                }
            },
            "classes": [
                {
                    "name": "Dummy",
                    "description": "defines a dummy class."
                },
                {
                    "name": "Noi",
                    "description": "defines another dummy class.",
                    "plural": "Noi_s"
                }
            ]
        }
        # yapf: enable

        errs = mapry.validation.validate(mapping=mapping, ref='#')

        self.assertEqual(2, len(errs))

        self.assertEqual(
            "#/dummies: Graph property 'dummies' conflicts "
            "with the plural necessary for the registry of class 'Dummy'",
            str(errs[0]))

        self.assertEqual(
            "#/noi_s: Graph property 'noi_s' conflicts "
            "with the plural necessary for the registry of class 'Noi'",
            str(errs[1]))


if __name__ == '__main__':
    unittest.main()
