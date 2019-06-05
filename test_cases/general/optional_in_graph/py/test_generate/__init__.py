# File automatically generated by mapry. DO NOT EDIT OR APPEND!


"""defines some object graph."""


import collections
import datetime
import pathlib
import typing


class Empty:
    """defines an empty class."""

    def __init__(
            self,
            id: str) -> None:
        """
        initializes an instance of Empty with the given values.

        :param id: identifier of the instance
        """
        self.id = id


class SomeEmbed:
    """defines an empty embeddable structure."""


class SomeGraph:
    """defines some object graph."""

    def __init__(
            self,
            optional_array: typing.Optional[typing.List[int]] = None,
            optional_boolean: typing.Optional[bool] = None,
            optional_date: typing.Optional[datetime.date] = None,
            optional_datetime: typing.Optional[datetime.datetime] = None,
            optional_duration: typing.Optional[datetime.timedelta] = None,
            optional_float: typing.Optional[float] = None,
            optional_integer: typing.Optional[int] = None,
            optional_map: typing.Optional[typing.MutableMapping[str, int]] = None,
            optional_path: typing.Optional[pathlib.Path] = None,
            optional_string: typing.Optional[str] = None,
            optional_time: typing.Optional[datetime.time] = None,
            optional_time_zone: typing.Optional[str] = None,
            optional_reference: typing.Optional[Empty] = None,
            optional_embed: typing.Optional[SomeEmbed] = None,
            empties: typing.Optional[typing.MutableMapping[str, Empty]] = None) -> None:
        """
        initializes an instance of SomeGraph with the given values.

        The class registries are initialized with empty ordered dictionaries.
        :param optional_array: defines some optional array.
        :param optional_boolean: defines some optional boolean.
        :param optional_date: defines some optional date.
        :param optional_datetime: defines some optional datetime.
        :param optional_duration: defines some optional duration.
        :param optional_float: defines some optional float.
        :param optional_integer: defines some optional integer.
        :param optional_map: defines some optional map.
        :param optional_path: defines an optional path.
        :param optional_string: defines an optional string.
        :param optional_time: defines an optional time.
        :param optional_time_zone: defines an optional time zone.
        :param optional_reference: defines an optional reference to an instance.
        :param optional_embed: defines an optional embedded structure.
        :param empties:
            registry of instances of Empty;
            if not specified, it is initialized as a ``collections.OrderedDict``.

        """
        self.optional_array = optional_array if optional_array is not None else None
        self.optional_boolean = optional_boolean if optional_boolean is not None else None
        self.optional_date = optional_date if optional_date is not None else None
        self.optional_datetime = optional_datetime if optional_datetime is not None else None
        self.optional_duration = optional_duration if optional_duration is not None else None
        self.optional_float = optional_float if optional_float is not None else None
        self.optional_integer = optional_integer if optional_integer is not None else None
        self.optional_map = optional_map if optional_map is not None else None
        self.optional_path = optional_path if optional_path is not None else None
        self.optional_string = optional_string if optional_string is not None else None
        self.optional_time = optional_time if optional_time is not None else None
        self.optional_time_zone = optional_time_zone if optional_time_zone is not None else None
        self.optional_reference = optional_reference if optional_reference is not None else None
        self.optional_embed = optional_embed if optional_embed is not None else None

        if empties is not None:
            self.empties = empties
        else:
            self.empties = collections.OrderedDict()


# File automatically generated by mapry. DO NOT EDIT OR APPEND!