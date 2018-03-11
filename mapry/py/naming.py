"""Convert mapry identifiers to the language-specific identifiers."""
import string

import icontract

import mapry.naming


@icontract.require(
    lambda identifier: identifier != '', error=ValueError, enabled=True)
def as_attribute(identifier: str) -> str:
    """
    Translate the name of a mapry property to a name of a Python attribute.

    :param identifier: mapry identifier of a property
    :return: translated to a Python attribute name

    >>> as_attribute('some_URL_property')
    'some_url_property'

    >>> as_attribute('URL_property')
    'url_property'

    """
    return identifier.lower()


@icontract.require(
    lambda identifier: identifier[0] in string.ascii_uppercase,
    description="Expected a mapry identifier of a composite to be in capital",
    error=ValueError,
    enabled=True)
@icontract.require(
    lambda identifier: identifier != '', error=ValueError, enabled=True)
def as_variable(identifier: str) -> str:
    """
    Translate the identifier of a mapry composite to a variable name in Python.

    :param identifier: mapry identifier of a composite
    :return: translated to a Python variable name

    >>> as_variable('Some_URL_class')
    'some_url_class'

    """
    return identifier.lower()


@icontract.require(
    lambda identifier: identifier[0] in string.ascii_uppercase,
    description="Expected a mapry identifier of a composite to be in capital",
    error=ValueError,
    enabled=True)
@icontract.require(
    lambda identifier: identifier != '', error=ValueError, enabled=True)
@icontract.require(lambda identifier: isinstance(identifier, str))
def as_composite(identifier: str) -> str:
    """
    Translate the identifier of a mapry composite to a composite name in Python.

    :param identifier: mapry identifier of a composite
    :return: translated to a Python identifier of a composite

    >>> as_composite(identifier='Some_URL_class')
    'SomeURLClass'

    """
    return mapry.naming.ucamel_case(identifier=identifier)
