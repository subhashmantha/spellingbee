import dataclasses
import inspect
import types
from typing import *  # type: ignore

T = TypeVar("T")


Recur = Callable[[Any, Type], Any]
Serializer = Callable[[Any, Type, Recur], Any]
Deserializer = Callable[[Any, Type, Recur], Any]


class SerdeError(Exception):
    """
    Signals an error during serialization or deserialization.
    """

    def __init__(self, user_message: str):
        self.user_message = user_message


def as_child(cls: Type[T]) -> Type[T]:
    """
    Marks the class to be serialized as one of its children. This will add an
    additional "type" field in the result, so the child can be deserialized
    properly.

    This decorator applies to children of the class as well, i.e. they will also
    be serialized with the "type" field.
    """
    assert inspect.isclass(cls), cls
    cls.__serde_serialize_as_child__ = cls  # type: ignore
    return cls


def should_serialize_as_child(cls: Type) -> bool:
    """
    Checks whether the given class should be serialized as a child, i.e. it, or
    any parent has been marked with the `as_child` decorator.
    """
    assert inspect.isclass(cls), cls
    return hasattr(cls, "__serde_serialize_as_child__")


def get_type_key(cls: Type) -> Type:
    """
    Given a type, return a more standardized type, suitable for use as a key to
    find serializers/deserializers.
    """

    # See what `get_origin` can do
    result: Any = get_origin(cls)

    if result is None:
        result = cls

    # Convert new-style unions to old-style
    if result is types.UnionType:
        result = Union

    # Pass through the rest
    return result


def common_serialize(
    value: Any,
    value_type: Optional[Type],
    class_serializer: Serializer,
    serializers: dict[Type, Serializer],
    user_serializers: dict[Type, Callable[[Any], Any]],
) -> Any:
    # Find the type
    if value_type is None:
        value_type = type(value)

    # Is there a custom serializer for this class?
    try:
        serializer = user_serializers[value_type]
    except KeyError:
        pass
    else:
        return serializer(value)

    # Find a matching serializer
    key = get_type_key(value_type)

    try:
        serializer = serializers[key]
    except KeyError:
        if inspect.isclass(value_type):
            serializer = class_serializer
        else:
            raise ValueError(f"Unsupported field of type {value_type}") from None

    # Define the recursion function
    def recur(value: Any, value_type: Type) -> Any:
        return common_serialize(
            value,
            value_type,
            class_serializer,
            serializers,
            user_serializers,
        )

    # Apply it
    return serializer(value, value_type, recur)


def common_deserialize(
    value: Any,
    value_type: Type,
    class_deserializer: Serializer,
    deserializers: dict[Type, Deserializer],
    user_deserializers: dict[Type, Callable[[Any], Any]],
) -> Any:
    # Is there a custom deserializer for this class?
    try:
        deserializer = user_deserializers[value_type]
    except KeyError:
        pass
    else:
        return deserializer(value)

    # Find a matching serializer
    key = get_type_key(value_type)

    try:
        deserializer = deserializers[key]
    except KeyError:
        if inspect.isclass(value_type):
            deserializer = class_deserializer
        else:
            raise ValueError(f"Unsupported field of type {value_type}") from None

    # Define the recursion function
    def recur(value: Any, value_type: Type) -> Any:
        return common_deserialize(
            value,
            value_type,
            class_deserializer,
            deserializers,
            user_deserializers,
        )

    # Apply it
    return deserializer(value, value_type, recur)


def all_subclasses(cls: Type, include_cls: bool) -> Iterable[Type]:
    """
    Yields all classes directly on indirectly inheriting from `cls`. Does not
    perform any sort of cycle checks.

    :param cls: The class to start from.
    :param include_cls: Whether to include `cls` itself in the results.
    """

    if include_cls:
        yield cls

    for subclass in cls.__subclasses__():
        yield from all_subclasses(subclass, include_cls=True)


def custom_get_type_hints(typ: Type) -> dict[str, Type]:
    """
    Returns the type hints for the given type, applying some uniserde specific
    logic.
    """
    hints = get_type_hints(typ)

    # Drop any value named '_' if it's just `dataclasses.KW_ONLY`
    if hasattr(typ, "__dataclass_fields__"):
        try:
            val = hints["_"]
        except KeyError:
            pass
        else:
            if val is dataclasses.KW_ONLY:
                del hints["_"]

    return hints
