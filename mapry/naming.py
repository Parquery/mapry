"""Handle name transformations (e.g., plural, snake_case etc.)."""
import string
from typing import List

from icontract import ensure, require


def split_identifier(identifier: str) -> List[str]:
    """
    Split the identifier into its parts.

    :param identifier: identifier to split written in snake_case
    :return: parts of the identifier

    >>> split_identifier(identifier='some')
    ['some']

    >>> split_identifier(identifier='some_split')
    ['some', 'split']

    >>> split_identifier(identifier='Some')
    ['Some']

    >>> split_identifier(identifier='Some_split')
    ['Some', 'split']

    >>> split_identifier(identifier='Some_Split')
    ['Some', 'Split']

    """
    return identifier.split("_")


PLURAL_TABLE = {
    "criterion": "criteria",
    "minimum": "minima",
    "maximum": "maxima",
    "matrix": "matrices",
    "life": "lives",
    "focus": "foci"
}

# Capital words have plural form also in capital.
for key, value in list(PLURAL_TABLE.items()):
    PLURAL_TABLE[key[0].upper() + key[1:]] = value[0].upper() + value[1:]


def plural(identifier: str) -> str:
    """
    Generate the plural of the identifier.

    :param identifier: to be put in plural
    :return: plural of the identifier; algorithmically inferred

    >>> plural(identifier='Hello')
    'Hellos'

    >>> plural(identifier='GoodDay')
    'GoodDays'

    >>> plural(identifier='Daisy')
    'Daisies'

    >>> plural(identifier='Bounding_box')
    'Bounding_boxes'

    >>> plural(identifier='Some_URL')
    'Some_URLs'

    >>> plural(identifier='Focus')
    'Foci'

    """
    parts = split_identifier(identifier=identifier)
    last_part = parts[-1]

    if last_part in PLURAL_TABLE:
        return PLURAL_TABLE[last_part]

    if (last_part.endswith('ay') or last_part.endswith('ey')
            or last_part.endswith('iy') or last_part.endswith('oy')
            or last_part.endswith('uy')):
        return identifier + "s"

    if last_part.endswith('y'):
        return identifier[:-1] + "ies"

    if last_part.endswith('x') or last_part.endswith('s'):
        return identifier + "es"

    return identifier + 's'


@require(
    lambda a_plural: len(a_plural) > 0 and a_plural[0] in string.
    ascii_uppercase, "Expected a capital plural of a composite")
def json_plural(a_plural: str) -> str:
    """
    Translate the plural designation of a mapry class to a JSON field name.

    :param plural: mapry plural of a class
    :return: translation to a JSON field name

    >>> json_plural('Some_URL_instances')
    'some_url_instances'

    """
    return a_plural.lower()


@require(
    lambda identifier: identifier != '',
    error=lambda: ValueError("Empty identifier"),
    enabled=True)
@ensure(lambda result: result != '')
@ensure(lambda result: result[0] == result[0].lower())
def camel_case(identifier: str) -> str:
    """
    Convert the canonical identifier to camelCase.

    :param identifier: canonical identifier
    :return: lowercase camel case version of the indentifier

    >>> result = camel_case('some_block')
    >>> assert result == 'someBlock'

    >>> result = camel_case('Some_block')
    >>> assert result == 'someBlock'

    >>> result = camel_case('Some_ID_URLs')
    >>> assert result == "someIDURLs"

    >>> result = camel_case('IDs_of_URLs')
    >>> assert result == "idsOfURLs"

    """
    parts = split_identifier(identifier=identifier)

    camel_case_parts = []  # type: List[str]
    camel_case_parts.append(parts[0].lower())

    for part in parts[1:]:
        camel_case_parts.append(part[0].upper() + part[1:])

    return ''.join(camel_case_parts)


@require(
    lambda identifier: identifier != '',
    error=lambda: ValueError("Empty identifier"),
    enabled=True)
@ensure(lambda result: result != '')
@ensure(lambda result: result[0] == result[0].upper())
def ucamel_case(identifier: str) -> str:
    """
    Convert the canonical identifier to CamelCase.

    :param identifier: canonical identifier
    :return: lowercase camel case version of the indentifier

    >>> result = ucamel_case('some_block')
    >>> assert result == 'SomeBlock'

    >>> result = ucamel_case('Some_Block')
    >>> assert result == 'SomeBlock'

    >>> result = ucamel_case('Some_ID_URLs')
    >>> assert result == "SomeIDURLs"

    >>> result = ucamel_case('IDs_of_URLs')
    >>> assert result == 'IDsOfURLs'
    """
    parts = split_identifier(identifier=identifier)

    camel_case_parts = []  # type: List[str]
    camel_case_parts.append(parts[0][0].upper() + parts[0][1:])

    for part in parts[1:]:
        camel_case_parts.append(part[0].upper() + part[1:])

    return ''.join(camel_case_parts)
