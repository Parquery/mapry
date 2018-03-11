#!/usr/bin/env python3

# pylint: disable=missing-docstring

import unittest

import mapry
import mapry.cpp.validation
import mapry.parse


class TestReservedKeywords(unittest.TestCase):
    def test_properties(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some object graph.",
            "classes": [
                {
                    "name": "Some_class",
                    "description":
                        "defines a class with reserved property names.",
                    "properties": {
                        "ID": {
                            "type": "boolean",
                            "description":
                                "conflicts with a keyword of the mapry."
                        },
                        "goto": {
                            "type": "boolean",
                            "description": "conflicts with a keyword of C++."
                        }
                    }
                },
                {
                    "name": "Reserved_plural",
                    "description": "defines a class with an invalid plural.",
                    "plural": "Volatile"
                }
            ],
            "embeds": [
                {
                    "name": "Some_embed",
                    "description":
                        "defines an embed with a reserved property name.",
                    "properties": {
                        "goto": {
                            "type": "boolean",
                            "description": "conflicts with a keyword."
                        }
                    }
                }
            ],
            "properties": {
                "goto": {
                    "type": "boolean",
                    "description": "conflicts with a keyword."
                }
            }
        }
        # yapf: enable

        schema = mapry.parse.schema_from_mapping(mapping=mapping, ref='#')

        errs = mapry.cpp.validation.validate_schema(schema=schema)
        text = '\n'.join([str(err) for err in errs])

        self.assertEqual(
            "#/classes/0/goto: The C++ field identifier 'goto' "
            "is a keyword in C++\n"
            "#/classes/0/ID: The C++ field identifier 'id' "
            "is reserved for class identifiers and "
            "used by the autogenerated code\n"
            "#/embeds/0/goto: The C++ field identifier 'goto' "
            "is a keyword in C++\n"
            "#/goto: The C++ field identifier 'goto' is a keyword in C++\n"
            "#/classes/1: The C++ field identifier 'volatile' corresponding "
            "to the registry of the class "
            "'Reserved_plural' in the object graph "
            "is a reserved keyword in C++", text)


class TestConflicts(unittest.TestCase):
    def test_class_plural_with_graph_property(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some object graph.",
            "classes": [
                {
                    "name": "Some_URL",
                    "description":
                        "defines some class whose plural conflicts "
                        "with a property of the object graph."
                }
            ],
            "properties": {
                "some_URLs": {
                    "type": "boolean",
                    "description": "conflicts with another property."
                }
            }
        }
        # yapf: enable

        schema = mapry.parse.schema_from_mapping(mapping=mapping, ref='#')

        errs = mapry.cpp.validation.validate_schema(schema=schema)
        text = '\n'.join([str(err) for err in errs])

        self.assertEqual(
            "#/classes/0: The C++ field identifier 'some_urls' corresponding "
            "to the registry of the class 'Some_URL' in the object graph "
            "conflicts with another C++ field corresponding to "
            "a property of the object graph (#/some_URLs)", text)

    def test_class_properties(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some object graph.",
            "classes": [
                {
                    "name": "Some_class",
                    "description":
                        "defines a class with a conflict.",
                    "properties": {
                        "some_urls": {
                            "type": "boolean",
                            "description": "conflicts with another property."
                        },
                        "some_URLs": {
                            "type": "boolean",
                            "description": "conflicts with another property."
                        }
                    }
                }
            ]
        }
        # yapf: enable

        schema = mapry.parse.schema_from_mapping(mapping=mapping, ref='#')

        errs = mapry.cpp.validation.validate_schema(schema=schema)
        text = '\n'.join([str(err) for err in errs])

        self.assertEqual(
            "#/classes/0/some_urls: "
            "The C++ field identifier 'some_urls' "
            "conflicts another field (#/classes/0/some_URLs)", text)

    def test_embed_properties(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines some object graph.",
            "embeds": [
                {
                    "name": "Some_embed",
                    "description":
                        "defines an embeddable structure with a conflict.",
                    "properties": {
                        "some_urls": {
                            "type": "boolean",
                            "description": "conflicts with another property."
                        },
                        "some_URLs": {
                            "type": "boolean",
                            "description": "conflicts with another property."
                        }
                    }
                }
            ]
        }
        # yapf: enable

        schema = mapry.parse.schema_from_mapping(mapping=mapping, ref='#')

        errs = mapry.cpp.validation.validate_schema(schema=schema)
        text = '\n'.join([str(err) for err in errs])

        self.assertEqual(
            "#/embeds/0/some_urls: "
            "The C++ field identifier 'some_urls' "
            "conflicts another field (#/embeds/0/some_URLs)", text)

    def test_graph_properties(self) -> None:
        # yapf: disable
        mapping = {
            "name": "Some_graph",
            "description": "defines an object graph with a conflict.",
            "properties": {
                "some_urls": {
                    "type": "boolean",
                    "description": "conflicts with another property."
                },
                "some_URLs": {
                    "type": "boolean",
                    "description": "conflicts with another property."
                }
            }
        }
        # yapf: enable

        schema = mapry.parse.schema_from_mapping(mapping=mapping, ref='#')

        errs = mapry.cpp.validation.validate_schema(schema=schema)
        text = '\n'.join([str(err) for err in errs])

        self.assertEqual(
            "#/some_urls: The C++ field identifier 'some_urls' "
            "conflicts another field (#/some_URLs)", text)


if __name__ == '__main__':
    unittest.main()
