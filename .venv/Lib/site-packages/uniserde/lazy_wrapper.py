"""
Provides functionality for lazily deserializing classes field-by-field.

When deserializing an object, rather than deserializing all of its fields
immediately, some additional fields/methods are added:

- `_uniserde_field_definitions_`: A dictionary mapping field names to tuples of
  (field document name, field type).

- `_uniserde_remaining_fields_`: A dictionary mapping field document names to
  unparsed field values.

- `_uniserde_serdeserializer_`: The serdeserializer instance that was used to
  deserialize the object.

- `__getattr__`: A function that deserializes fields when they are first
  accessed, and then caches them in the instance.

Note that this approach allows for doing a lot of gruntwork up-front: The class,
along with all of its fields, and the `__getattr__` method only have to be
created once and can be reused for all future deserializations of that class.
"""

from __future__ import annotations

import inspect
from typing import *  # type: ignore

from . import caching_serdeserializer
from .common import SerdeError

_FIELD_MAP_CACHE: dict[
    tuple[Type, Type[caching_serdeserializer.CachingSerDeserializer]], Type
] = {}


def _lazy_getattr(self, name: str) -> Any:
    # Fetch the field definitions. This will fail if this particular instance
    # isn't lazy
    try:
        field_definitions = vars(self)["_uniserde_field_definitions_"]
    except KeyError:
        raise AttributeError(name) from None

    # See if there is a field definition for this field. This will fail if the
    # field doesn't exist
    try:
        field_doc_name, field_type = field_definitions[name]
    except KeyError:
        raise AttributeError(name) from None

    # Get the field value
    try:
        field_raw_value = self._uniserde_remaining_fields_.pop(field_doc_name)
    except KeyError:
        raise SerdeError(f"Missing field `{field_doc_name!r}`") from None

    # Deserialize it
    field_handler = self._uniserde_serdeserializer_._get_handler(field_type)
    parsed_value = field_handler(
        self._uniserde_serdeserializer_,
        field_raw_value,
        field_type,
    )

    # Cache it
    vars(self)[name] = parsed_value

    # Return it
    return parsed_value


def _get_field_map(
    value_type: Type,
    serdeserializer: caching_serdeserializer.CachingSerDeserializer,
) -> dict[str, tuple[str, Type]]:
    # Already cached?
    try:
        return _FIELD_MAP_CACHE[(value_type, type(serdeserializer))]
    except KeyError:
        pass

    # Fetch the fields
    result = {
        field_py_name: (
            field_doc_name,
            field_type,
        )
        for (
            field_py_name,
            field_doc_name,
            field_type,
        ) in serdeserializer._get_class_fields(value_type)
    }

    # Cache the result
    _FIELD_MAP_CACHE[(value_type, type(serdeserializer))] = result

    # Return it
    return result


def can_create_lazy_instance(value_type: Type) -> bool:
    """
    Verify that some conditions are met for creating a lazy instance of the
    given type.
    """

    # The class mustn't have a `__getattr__` method, since that would be
    # overwritten. If it is already overwritten that's obviously also fine.
    try:
        return value_type.__getattr__ is _lazy_getattr
    except AttributeError:
        return True


def create_lazy_instance(
    serialized: dict[str, Any],
    serdeserializer: caching_serdeserializer.CachingSerDeserializer,
    value_type: Type,
) -> Any:
    assert isinstance(serialized, dict), serialized
    assert inspect.isclass(value_type), value_type
    assert serdeserializer._lazy, serdeserializer
    assert can_create_lazy_instance(value_type), value_type

    # Instantiate the result, skipping the constructor
    result = object.__new__(value_type)

    # Set additional, internal fields
    type(result).__getattr__ = _lazy_getattr
    result._uniserde_field_definitions_ = _get_field_map(value_type, serdeserializer)
    result._uniserde_serdeserializer_ = serdeserializer
    result._uniserde_remaining_fields_ = serialized

    # Done
    return result
