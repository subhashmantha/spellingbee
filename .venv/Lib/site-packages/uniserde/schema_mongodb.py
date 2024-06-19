import enum
import inspect
import types
from datetime import datetime, timedelta
from pathlib import Path
from typing import *  # type: ignore

from . import case_convert, common, serde_class
from .common import *
from .objectid_proxy import ObjectId
from .typedefs import Jsonable


class MongoDbSchemaBuilder:
    def __init__(self, custom_handlers: dict[Type, Callable[[Type], Jsonable]]):
        self._custom_handlers = custom_handlers

    def process(self, value_type: Type) -> Jsonable:
        # Find a matching serializer
        key = common.get_type_key(value_type)

        # Custom handlers take precedence
        try:
            handler = self._custom_handlers[key]
        except KeyError:
            pass
        else:
            return handler(value_type)

        # Plain old default handler
        try:
            handler = self._handlers[key]
        except KeyError:
            pass
        else:
            return handler(self, value_type)

        # Class handler
        assert inspect.isclass(value_type), value_type
        return self._make_schema_class(value_type)

    def _make_schema_bool_to_bool(self, value_type: Type) -> Jsonable:
        return {"type": "boolean"}

    def _make_schema_int_to_int(self, value_type: Type) -> Jsonable:
        return {"bsonType": ["int", "long"]}

    def _make_schema_float_to_float(self, value_type: Type) -> Jsonable:
        return {"bsonType": ["int", "long", "double"]}

    def _make_schema_bytes_to_bytes(self, value_type: Type) -> Jsonable:
        return {"bsonType": "binData"}

    def _make_schema_str_to_str(self, value_type: Type) -> Jsonable:
        return {"type": "string"}

    def _make_schema_datetime_to_datetime(self, value_type: Type) -> Jsonable:
        return {"bsonType": "date"}

    def _make_schema_timedelta_to_float(self, value_type: Type) -> Jsonable:
        return {"bsonType": ["int", "long", "double"]}

    def _make_schema_tuple_to_list(self, value_type: Type) -> Jsonable:
        return {
            "type": "array",
            "items": [self.process(subtype) for subtype in get_args(value_type)],
        }

    def _make_schema_list_to_list(self, value_type: Type) -> Jsonable:
        return {
            "type": "array",
            "items": self.process(get_args(value_type)[0]),
        }

    def _make_schema_set_to_list(self, value_type: Type) -> Jsonable:
        return {
            "type": "array",
            "items": self.process(get_args(value_type)[0]),
        }

    def _make_schema_path_to_str(self, value_type: Type) -> Jsonable:
        return {"type": "string"}

    def _make_schema_dict_to_dict(self, value_type: Type) -> Jsonable:
        subtypes = get_args(value_type)
        assert subtypes[0] is str, value_type

        return {
            "type": "object",
            "items": self.process(subtypes[1]),
        }

    def _make_schema_object_id_to_object_id(self, value_type: Type) -> Jsonable:
        return {"bsonType": "objectId"}

    def _make_schema_literal_to_str(self, value_type: Type) -> Jsonable:
        return {"type": "string"}

    def _make_schema_union(self, value_type: Type) -> Jsonable:
        # Convert each subtype to a BSON schema
        sub_schemas = []
        for subtype in get_args(value_type):
            # Union is used by Python to represent "Optional"
            if subtype is type(None):
                sub_schemas.append({"type": "null"})
                continue

            sub_schemas.append(self.process(subtype))

        # Prettify the result: instead of `{anyof {type ...} {type ...}}` just
        # create one `type`
        types = []
        bson_types = []
        others = []

        for schema in sub_schemas:
            if len(schema) == 1:
                # Standard Json Schema type
                try:
                    type_field = schema["type"]
                except KeyError:
                    pass
                else:
                    if isinstance(type_field, list):
                        types.extend(type_field)
                    else:
                        types.append(type_field)

                    continue

                # BSON type
                try:
                    type_field = schema["bsonType"]
                except KeyError:
                    pass
                else:
                    if isinstance(type_field, list):
                        bson_types.extend(type_field)
                    else:
                        bson_types.append(type_field)

                    continue

            # General case
            others.append(schema)

        # Create new, merged schemas
        sub_schemas = []

        if bson_types:
            sub_schemas.append({"bsonType": types + bson_types})
        elif types:
            sub_schemas.append({"type": types})

        sub_schemas.extend(others)

        if len(sub_schemas) == 1:
            return sub_schemas[0]

        return {"anyOf": sub_schemas}

    def _make_schema_any(self, value_type: Type) -> Jsonable:
        return {}

    def _create_class_schema_ignore_serialize_as_child(
        self, value_type: Type
    ) -> Jsonable:
        doc_field_names = []
        doc_properties = {}
        result = {
            "type": "object",
            "properties": doc_properties,
            "additionalProperties": False,
        }

        for field_py_name, field_type in common.custom_get_type_hints(
            value_type
        ).items():
            field_doc_name = case_convert.all_lower_to_camel_case(field_py_name)

            if field_py_name == "id":
                field_doc_name = "_id"

            doc_field_names.append(field_doc_name)
            doc_properties[field_doc_name] = self.process(field_type)

        # The `required` field may only be present if it contains at least one value
        if doc_field_names:
            result["required"] = doc_field_names

        return result

    def _make_schema_class(self, value_type: Type) -> Jsonable:
        assert inspect.isclass(value_type), value_type

        # Case: The class has a custom schema method
        try:
            override_method = getattr(value_type, "as_mongodb_schema")
        except AttributeError:
            pass
        else:
            serde_class_method = serde_class.Serde.as_mongodb_schema

            try:
                override_method_func = override_method.__func__
            except AttributeError:
                override_method_func = override_method

            if override_method_func is not serde_class_method.__func__:
                return override_method()

        # Case: enum.Flag
        if issubclass(value_type, enum.Flag):
            return {
                "type": "array",
                "items": {
                    "enum": [
                        case_convert.all_upper_to_camel_case(variant.name)  # type: ignore
                        for variant in value_type
                    ],
                },
            }

        # Case: enum.Enum
        if issubclass(value_type, enum.Enum):
            return {
                "enum": [
                    case_convert.all_upper_to_camel_case(variant.name)
                    for variant in value_type
                ],
            }

        # Case: Class, and definitely not one of it's children
        if not should_serialize_as_child(value_type):
            return self._create_class_schema_ignore_serialize_as_child(value_type)

        # Case: Class or one of its children

        # Create the schemas for all allowable classes
        sub_schemas = []
        for subtype in all_subclasses(value_type, True):
            schema: Any = self._create_class_schema_ignore_serialize_as_child(subtype)
            assert schema["type"] == "object", schema

            schema["properties"]["type"] = {
                "enum": [case_convert.upper_camel_case_to_camel_case(subtype.__name__)]
            }

            required = schema.setdefault("required", [])
            required.insert(0, "type")

            sub_schemas.append(schema)

        # Create the final, combined schema
        if len(sub_schemas) == 1:
            return sub_schemas[0]
        else:
            return {"anyOf": sub_schemas}

    _handlers: dict[Type, Callable[["MongoDbSchemaBuilder", Type], Jsonable]] = {
        bool: _make_schema_bool_to_bool,
        int: _make_schema_int_to_int,
        float: _make_schema_float_to_float,
        bytes: _make_schema_bytes_to_bytes,
        str: _make_schema_str_to_str,
        datetime: _make_schema_datetime_to_datetime,
        timedelta: _make_schema_timedelta_to_float,
        list: _make_schema_list_to_list,
        dict: _make_schema_dict_to_dict,
        Union: _make_schema_union,
        Any: _make_schema_any,
        ObjectId: _make_schema_object_id_to_object_id,
        Literal: _make_schema_literal_to_str,
        tuple: _make_schema_tuple_to_list,
        set: _make_schema_set_to_list,
        Path: _make_schema_path_to_str,
        type(Path()): _make_schema_path_to_str,
    }


def as_mongodb_schema(
    value_type: Type,
    *,
    custom_handlers: dict[Type, Callable[[Type], Jsonable]] = {},
) -> Any:
    """
    Return a MongoDB schema for this class. The schema matches values resulting
    from `as_bson`.
    """

    builder = MongoDbSchemaBuilder(custom_handlers)
    return builder.process(value_type)
