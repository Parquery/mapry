#!/usr/bin/env python3

# pylint: disable=missing-docstring

import unittest

import mapry


def dummy_property(
        name: str, a_type: mapry.Type,
        composite: mapry.Composite) -> mapry.Property:
    """
    Generate a dummy property of a composite.

    :param name: name of the property
    :param a_type: type of the property
    :param composite: composite structure that this property belongs to
    :return: generated dummy property
    """
    return mapry.Property(
        ref='',
        name=name,
        a_type=a_type,
        description='',
        json=name,
        optional=False,
        composite=composite)


class TestMapry(unittest.TestCase):
    def test_value_needs_type(self) -> None:
        type_definition = mapry.Path()

        self.assertTrue(
            mapry.needs_type(a_type=type_definition, query=mapry.Path))

        self.assertFalse(
            mapry.needs_type(a_type=type_definition, query=mapry.Date))

    def test_array_needs_type(self) -> None:
        array = mapry.Array(values=mapry.Path(), minimum_size=None)

        self.assertTrue(mapry.needs_type(a_type=array, query=mapry.Path))
        self.assertFalse(mapry.needs_type(a_type=array, query=mapry.Date))

    def test_map_needs_type(self) -> None:
        a_map = mapry.Map(values=mapry.Path())

        self.assertTrue(mapry.needs_type(a_type=a_map, query=mapry.Path))
        self.assertFalse(mapry.needs_type(a_type=a_map, query=mapry.Date))

    def test_class_needs_type(self) -> None:
        cls = mapry.Class(name='some_class', plural='', description='', ref='')
        cls.name = 'some_class'
        cls.properties = {
            'some_property':
            dummy_property(
                name='some_property', a_type=mapry.Path(), composite=cls)
        }

        self.assertTrue(mapry.needs_type(a_type=cls, query=mapry.Path))
        self.assertFalse(mapry.needs_type(a_type=cls, query=mapry.Date))

    def test_embed_needs_type(self) -> None:
        embed = mapry.Embed(name='some_embed', description='', ref='')

        embed.properties = {
            'some_property':
            dummy_property(
                name='some_property', a_type=mapry.Path(), composite=embed)
        }

        self.assertTrue(mapry.needs_type(a_type=embed, query=mapry.Path))
        self.assertFalse(mapry.needs_type(a_type=embed, query=mapry.Date))

    def test_graph_needs_type(self) -> None:
        # Property of an object graph
        graph = mapry.Graph()
        graph.properties = {
            "some_property":
            dummy_property(
                name='some_property', a_type=mapry.Path(), composite=graph)
        }

        self.assertTrue(mapry.needs_type(a_type=graph, query=mapry.Path))
        self.assertFalse(mapry.needs_type(a_type=graph, query=mapry.Date))

        # Recursively needs type by a property of a class
        cls = mapry.Class(name='some_class', plural='', description='', ref='')
        cls.properties = {
            'some_property':
            dummy_property(
                name='some_property', a_type=mapry.Path(), composite=cls)
        }

        graph = mapry.Graph()
        graph.classes = {cls.name: cls}
        self.assertTrue(mapry.needs_type(a_type=graph, query=mapry.Path))
        self.assertFalse(mapry.needs_type(a_type=graph, query=mapry.Date))

        # Recursively needs type by a property of an embeddable structure
        embed = mapry.Embed(name='some_embed', description='', ref='')
        embed.properties = {
            'some_property':
            dummy_property(
                name='some_property', a_type=mapry.Path(), composite=embed)
        }

        graph = mapry.Graph()
        graph.embeds = {embed.name: embed}
        self.assertTrue(mapry.needs_type(a_type=graph, query=mapry.Path))
        self.assertFalse(mapry.needs_type(a_type=graph, query=mapry.Date))

    def test_iterate_over_types(self) -> None:
        embed_path = mapry.Path()
        embed_array = mapry.Array(values=embed_path)
        embed = mapry.Embed(name='some_embed', description='', ref='E#')
        embed.properties = {
            "some_embed_property":
            dummy_property(
                name="some_embed_property", a_type=embed_array, composite=embed)
        }

        cls_path = mapry.Path()
        cls = mapry.Class(
            name='some_class', plural='', description='', ref='C#')
        cls.properties = {
            "some_class_property":
            dummy_property(
                name="some_class_property", a_type=cls_path, composite=cls)
        }

        graph_path = mapry.Path()
        graph = mapry.Graph()
        graph.ref = 'G#'
        graph.properties = {
            "some_graph_property":
            dummy_property(
                name="some_graph_property", a_type=graph_path, composite=graph),
        }
        graph.classes = {cls.name: cls}
        graph.embeds = {embed.name: embed}

        # yapf: disable
        self.assertListEqual(
            [(cls_path, 'C#/some_class_property'),
             (embed_array, 'E#/some_embed_property'),
             (embed_path, 'E#/some_embed_property/values'),
             (graph_path, 'G#/some_graph_property')],
            list(mapry.iterate_over_types(graph=graph)))
        # yapf: enable


class TestReferences(unittest.TestCase):
    def test_that_it_works(self) -> None:
        another_cls = mapry.Class(
            name='another_cls', plural='', description='', ref='')

        embed = mapry.Embed(name='some_embed', description='', ref='')
        embed.properties = {
            "another_ref":
            dummy_property(
                name='another_ref', a_type=another_cls, composite=embed)
        }

        cls = mapry.Class(name='some_class', plural='', description='', ref='')

        cls.properties = {
            "some_primitive":
            dummy_property(
                name="some_primitive", a_type=mapry.Path(), composite=cls),
            "some_ref":
            dummy_property(name="some_ref", a_type=cls, composite=cls),
            "some_embed":
            dummy_property(name="some_embed", a_type=embed, composite=cls)
        }

        self.assertListEqual([another_cls, cls], mapry.references(a_type=cls))

    def test_self_referencing_class(self) -> None:
        cls = mapry.Class(name='some_class', plural='', description='', ref='')

        cls.properties = {
            "some_ref":
            dummy_property(name="some_ref", a_type=cls, composite=cls)
        }

        self.assertListEqual([cls], mapry.references(a_type=cls))

    def test_array(self) -> None:
        cls = mapry.Class(name='some_class', plural='', description='', ref='')

        cls.properties = {
            "friends":
            mapry.Property(
                ref='',
                name='friends',
                a_type=mapry.Array(values=cls),
                description='',
                json='',
                optional=False,
                composite=cls)
        }

        self.assertListEqual([cls], mapry.references(a_type=cls))

    def test_map(self) -> None:
        cls = mapry.Class(name='some_class', plural='', description='', ref='')

        cls.properties = {
            "friends":
            mapry.Property(
                ref='',
                name='friends',
                a_type=mapry.Map(values=cls),
                description='',
                json='',
                optional=False,
                composite=cls)
        }

        self.assertListEqual([cls], mapry.references(a_type=cls))

    def test_optional(self) -> None:
        cls = mapry.Class(name='some_class', plural='', description='', ref='')

        cls.properties = {
            "bff":
            mapry.Property(
                ref='',
                name='friends',
                a_type=cls,
                description='',
                json='',
                optional=True,
                composite=cls)
        }

        self.assertListEqual([cls], mapry.references(a_type=cls))


if __name__ == '__main__':
    unittest.main()
