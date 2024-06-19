from __future__ import annotations

from typing import *  # type: ignore

import uniserde

from .typedefs import *

__all__ = [
    "Serde",
]


T = TypeVar("T", bound="Serde")


class Serde:
    def as_bson(
        self,
        *,
        as_type: Optional[Type] = None,
        custom_serializers: dict[Type, Callable[[Any], Any]] = {},
    ) -> BsonDoc:
        """
        Serialize the entire instance to BSON, by applying the field serializer
        to each field. Field names are converted to camel case.
        """
        assert as_type is None or issubclass(self.__class__, as_type), as_type
        return uniserde.as_bson(
            self,
            as_type=as_type,
            custom_serializers=custom_serializers,
        )  # type: ignore

    def as_json(
        self,
        *,
        as_type: Optional[Type] = None,
        custom_serializers: dict[Type, Callable[[Any], Any]] = {},
    ) -> JsonDoc:
        """
        Serialize the entire instance to JSON, by applying the field serializer
        to each field. Field names are converted to camel case.
        """
        assert as_type is None or issubclass(self.__class__, as_type), as_type
        return uniserde.as_json(
            self,
            as_type=as_type,
            custom_serializers=custom_serializers,
        )  # type: ignore

    @classmethod
    def from_bson(
        cls: Type[T],
        document: BsonDoc,
        *,
        custom_deserializers: dict[Type, Callable[[Any], Any]] = {},
        lazy: bool = False,
    ) -> T:
        """
        Deserialize an entire data class from BSON, by applying the field
        deserializer to each field. Field names are converted from camel case.

        Warning: The document may be modified in-place by this function!
        """
        return uniserde.from_bson(
            document,
            as_type=cls,
            custom_deserializers=custom_deserializers,
            lazy=lazy,
        )

    @classmethod
    def from_json(
        cls: Type[T],
        document: JsonDoc,
        *,
        custom_deserializers: dict[Type, Callable[[Any], Any]] = {},
        lazy: bool = False,
    ) -> T:
        """
        Deserialize an entire class from JSON, by applying the field
        deserializer to each field. Field names are converted from camel case.

        Warning: The document may be modified in-place by this function!
        """
        return uniserde.from_json(
            document,
            as_type=cls,
            custom_deserializers=custom_deserializers,
            lazy=lazy,
        )

    @classmethod
    def as_mongodb_schema(
        cls,
        *,
        custom_handlers: dict[Type, Callable[[Any], Any]] = {},
    ) -> Any:
        """
        Return a MongoDB schema for this class. The schema matches values
        resulting from `as_bson`.
        """
        return uniserde.as_mongodb_schema(
            cls,
            custom_handlers=custom_handlers,
        )
