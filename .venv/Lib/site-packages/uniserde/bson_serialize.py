from datetime import datetime
from typing import *  # type: ignore

from . import json_serialize, serde_class
from .common import *
from .objectid_proxy import ObjectId
from .typedefs import BsonDoc

__all__ = [
    "as_bson",
]


def serialize_bytes_to_bytes(
    value: Any,
    value_type: Type,
    recur: Recur,
) -> bytes:
    assert isinstance(value, bytes), value
    return value


def serialize_datetime_to_datetime(
    value: Any,
    value_type: Type,
    recur: Recur,
) -> datetime:
    assert isinstance(value, datetime), value
    assert (
        value.tzinfo is not None
    ), f"Encountered datetime without a timezone. Please always set timezones, or expect hard to find bugs."

    return value


def serialize_object_id_to_object_id(
    value: Any,
    value_type: Type,
    recur: Recur,
) -> ObjectId:
    assert isinstance(value, ObjectId), value
    return value


def serialize_class(
    value: Any,
    value_type: Type,
    recur: Recur,
) -> BsonDoc:
    result = json_serialize.serialize_class(value, value_type, recur)

    # Case: The class has a custom serialization method
    try:
        override_method = getattr(value, "as_bson")
    except AttributeError:
        pass
    else:
        if override_method.__func__ is not serde_class.Serde.as_bson:
            return override_method()

    # Map "id" to "_id", as is done in MongoDB.
    if isinstance(result, dict) and "_id" not in result:
        try:
            result["_id"] = result.pop("id")
        except KeyError:
            pass

    return result


BSON_SERIALIZERS: dict[Type, Serializer] = json_serialize.JSON_SERIALIZERS.copy()
BSON_SERIALIZERS.update(
    {
        bytes: serialize_bytes_to_bytes,
        datetime: serialize_datetime_to_datetime,
        ObjectId: serialize_object_id_to_object_id,
    }
)


def as_bson(
    value: Any,
    *,
    as_type: Optional[Type] = None,
    custom_serializers: dict[Type, Callable[[Any], Any]] = {},
) -> BsonDoc:
    return common_serialize(
        value,
        type(value) if as_type is None else as_type,
        serialize_class,
        BSON_SERIALIZERS,
        custom_serializers,
    )
