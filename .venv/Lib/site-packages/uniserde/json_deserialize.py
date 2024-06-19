import base64
import typing
from datetime import datetime, timedelta
from pathlib import Path
from typing import *  # type: ignore

import dateutil.parser

from . import caching_serdeserializer, case_convert, common
from .common import SerdeError
from .objectid_proxy import ObjectId
from .typedefs import Jsonable

__all__ = [
    "from_json",
]


T = TypeVar("T")


class JsonDeserializer(caching_serdeserializer.CachingSerDeserializer[Jsonable, Any]):
    def _get_class_fields(self, value_type: Type) -> Iterable[tuple[str, str, Type]]:
        for field_name_py, field_type in common.custom_get_type_hints(
            value_type
        ).items():
            yield (
                field_name_py,
                case_convert.all_lower_to_camel_case(field_name_py),
                field_type,
            )

    def _deserialize_bytes_from_str(
        self,
        value: Any,
        value_type: Type[str],
    ) -> bytes:
        if not isinstance(value, str):
            raise SerdeError(f"Expected bytes encoded as string, got `{value}`")

        try:
            return base64.b64decode(value.encode("utf-8"))
        except ValueError:
            raise SerdeError("Received invalid base64 encoded string.")

    def _deserialize_datetime_from_str(
        self,
        value: Any,
        value_type: Type[datetime],
    ) -> datetime:
        if not isinstance(value, str):
            raise SerdeError(f"Expected date/time string, got `{value}`")

        try:
            result = dateutil.parser.isoparse(value)
        except ValueError:
            raise SerdeError(f"Expected date/time, got `{value}`") from None

        if result.tzinfo is None:
            raise SerdeError(f"The date/time value `{value}` is missing a timezone.")

        return result

    def _deserialize_timedelta_from_float(
        self,
        value: Any,
        value_type: Type[timedelta],
    ) -> timedelta:
        if not isinstance(value, (int, float)):
            raise SerdeError(f"Expected number, got `{value}`")

        return timedelta(seconds=value)

    def _deserialize_tuple_from_list(
        self,
        value: Any,
        value_type: Type[Tuple],
    ) -> tuple[Any]:
        if not isinstance(value, list):
            raise SerdeError(f"Expected list, got `{value}`")

        subtypes = get_args(value_type)

        if len(value) != len(subtypes):
            raise SerdeError(
                f"Expected list of length {len(subtypes)}, but received one of length {len(value)}"
            )

        return tuple(self.process(v, subtype) for v, subtype in zip(value, subtypes))

    def _deserialize_list_from_list(
        self,
        value: Any,
        value_type: Type[List],
    ) -> list[Any]:
        if not isinstance(value, list):
            raise SerdeError(f"Expected list, got `{value}`")

        subtype = get_args(value_type)[0]
        child_deserializer = self._get_handler(subtype)

        return [child_deserializer(self, v, subtype) for v in value]

    def _deserialize_set_from_list(
        self,
        value: Any,
        value_type: Type[Set],
    ) -> Set:
        if not isinstance(value, list):
            raise SerdeError(f"Expected list, got `{value}`")

        subtype = get_args(value_type)[0]

        return set(self.process(v, subtype) for v in value)

    def _deserialize_dict_from_dict(
        self,
        value: Any,
        value_type: Type[Dict],
    ) -> dict[Any, Any]:
        if not isinstance(value, dict):
            raise SerdeError(f"Expected dict, got `{value}`")

        subtypes = get_args(value_type)

        key_type = subtypes[0]
        key_deserializer = self._get_handler(key_type)

        value_type = subtypes[1]
        value_deserializer = self._get_handler(value_type)

        return {
            key_deserializer(self, k, key_type): value_deserializer(self, v, value_type)
            for k, v in value.items()
        }

    def _deserialize_object_id_from_str(
        self,
        value: Any,
        value_type: Type[ObjectId],
    ) -> ObjectId:
        if not isinstance(value, str):
            raise SerdeError(f"Expected ObjectId string, got `{value}`")

        try:
            result = ObjectId(value)
        except ValueError:
            raise SerdeError(f"Expected ObjectId string, got `{value}`") from None

        return result

    def _deserialize_optional(
        self,
        value: Any,
        value_type: Type,
    ) -> Any:
        if value is None:
            return None

        for subtype in typing.get_args(value_type):
            if subtype is not type(None):
                break
        else:
            assert False, "No `None` in an `Optional` type?"

        return self.process(value, subtype)

    def _deserialize_any(
        self,
        value: Any,
        value_type: Type[Any],
    ) -> Any:
        return value

    def _deserialize_literal_as_is(
        self,
        value: Any,
        value_type: Type[Any],
    ) -> str:
        options = get_args(value_type)
        if value not in options:
            raise SerdeError(f"Expected `{value_type}`, got `{value}`")

        return value

    def _deserialize_path_from_str(
        self,
        value: Any,
        value_type: Type[Path],
    ) -> Path:
        if not isinstance(value, str):
            raise SerdeError(f"Expected path string, got `{value}`")

        return Path(value)

    _passthrough_types = {
        bool,
        int,
        float,
        str,
    }  # type: ignore

    _handler_cache = {
        (True, bytes): _deserialize_bytes_from_str,
        (False, bytes): _deserialize_bytes_from_str,
        (True, datetime): _deserialize_datetime_from_str,
        (False, datetime): _deserialize_datetime_from_str,
        (True, timedelta): _deserialize_timedelta_from_float,
        (False, timedelta): _deserialize_timedelta_from_float,
        (True, tuple): _deserialize_tuple_from_list,
        (False, tuple): _deserialize_tuple_from_list,
        (True, list): _deserialize_list_from_list,
        (False, list): _deserialize_list_from_list,
        (True, set): _deserialize_set_from_list,
        (False, set): _deserialize_set_from_list,
        (True, dict): _deserialize_dict_from_dict,
        (False, dict): _deserialize_dict_from_dict,
        (True, Union): _deserialize_optional,
        (False, Union): _deserialize_optional,
        (True, Any): _deserialize_any,
        (False, Any): _deserialize_any,
        (True, ObjectId): _deserialize_object_id_from_str,
        (False, ObjectId): _deserialize_object_id_from_str,
        (True, Literal): _deserialize_literal_as_is,
        (False, Literal): _deserialize_literal_as_is,
        (True, Path): _deserialize_path_from_str,
        (False, Path): _deserialize_path_from_str,
        (True, type(Path())): _deserialize_path_from_str,
        (False, type(Path())): _deserialize_path_from_str,
    }  # type: ignore

    _override_method_name = "from_json"


def from_json(
    document: Any,
    as_type: Type[T],
    *,
    custom_deserializers: dict[Type, Callable[[Jsonable], Any]] = {},
    lazy: bool = False,
) -> T:
    """
    Deserialize an entire class from JSON, by applying the field deserializer to
    each field. Field names are converted from camel case.

    Warning: The document may be modified in-place by this function!
    """

    deserializer = JsonDeserializer(
        custom_deserializers={
            t: lambda v, _: cb(v) for t, cb in custom_deserializers.items()
        },
        lazy=lazy,
    )

    return deserializer.process(document, as_type)
