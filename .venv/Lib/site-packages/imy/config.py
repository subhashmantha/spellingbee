"""
Utilities for loading configuration from JSON files and environment variables.
"""

from __future__ import annotations

import enum
import os
from collections.abc import Iterable
from datetime import datetime, timedelta
from pathlib import Path
from typing import *  # type: ignore

import introspection.typing
import json5
import uniserde
import uniserde.case_convert
from typing_extensions import dataclass_transform
from uniserde import Jsonable, ObjectId

__all__ = [
    "ConfigurationError",
    "Config",
]


_DEFAULTS_BY_TYPE: dict[Type, uniserde.Jsonable] = {
    Any: None,
    bool: False,
    bytes: b"",
    datetime: datetime.now().isoformat(),
    dict: {},
    enum.Enum: "",
    enum.Flag: [],
    float: 0.0,
    int: 0,
    list: [],
    Literal: "",
    set: set(),
    str: "",
    timedelta: 0,
    tuple: tuple(),
    Union: None,
    ObjectId: "",
}  # type: ignore


class ConfigurationError(ValueError):
    """
    Raised when the configuration couldn't be loaded, for whichever reason.
    """

    pass


@dataclass_transform()
class Config:
    @classmethod
    def _get_fields(cls) -> Iterable[tuple[str, type]]:
        """
        Returns iterators over all fields and their types.
        """
        for attr_name, type_info in introspection.typing.get_type_annotations(
            cls
        ).items():
            if type_info.arguments:
                raw_type = introspection.typing.parameterize(
                    type_info.type, type_info.arguments
                )
            else:
                raw_type = type_info.type

            yield attr_name, raw_type  # type: ignore

    @staticmethod
    def _create_json_template(fields: Iterable[tuple[str, Type]]) -> str:
        """
        Create an empty JSON template for the provided fields.
        """

        # Build a JSON containing the default values for each field
        default_values_dict: dict[str, Jsonable] = {}

        for field_py_name, field_type in fields:
            field_doc_name = uniserde.case_convert.all_lower_to_camel_case(
                field_py_name
            )
            default_values_dict[field_doc_name] = _DEFAULTS_BY_TYPE.get(
                field_type, None
            )

        # Serialize the instance into formatted JSON
        serialized: str = json5.dumps(  # type: ignore
            default_values_dict,
            indent=4,
            quote_keys=True,
            trailing_commas=True,
        )

        # Add comments describing the fields
        serialized = serialized.strip()
        lines = serialized.splitlines()

        for ii, line in enumerate(lines[1:-1], start=1):
            lines[ii] = "  // " + line.strip()

        # Done
        return "\n".join(lines) + "\n"

    @classmethod
    def _parse_fields(
        cls,
        *,
        fields: Iterable[tuple[str, Type]],
        values: Iterable[tuple[str, Any]],
        case_transform: Callable[[str], str],
        raise_on_superfluous: bool,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Parses the provided fields and values into a dictionary, transforming
        the field names using the provided `case_transform` function. The result
        is a tuple of two dictionaries: the first contains the parsed fields,
        the second any unparsed, i.e. superfluous values.

        ## Raises

        `ConfigurationError`: if any fields are missing, or of the wrong type.
        """
        # Prepare everything as dictionaries for quick lookup
        field_dict: dict[str, Type] = dict(fields)
        value_dict: dict[str, Any] = dict(values)

        # Parse the fields, popping them from the value dictionary
        parsed_fields: dict[str, Any] = {}

        for py_name, py_type in field_dict.items():
            doc_name = case_transform(py_name)

            try:
                raw_value = value_dict.pop(doc_name)
            except KeyError:
                raise ConfigurationError(
                    f"The config is missing the field `{doc_name}`"
                )

            try:
                parsed_value = uniserde.from_json(raw_value, py_type)
            except uniserde.SerdeError as err:
                raise ConfigurationError(
                    f"`{raw_value}` is not a valid value for `{doc_name}`"
                ) from err

            parsed_fields[py_name] = parsed_value

        # Are superfluous values allowed?
        if raise_on_superfluous and value_dict:
            raise ConfigurationError(
                f"The config contains superfluous fields: `{'`, `'.join(value_dict)}`"
            )

        # Done
        return parsed_fields, value_dict

    @classmethod
    def _load_from_values(
        cls,
        *,
        values: Iterable[tuple[str, Any]],
        case_transform: Callable[[str], str],
    ) -> Self:
        """
        Loads an instance of the config from the provided values.

        ## Raises

        `ConfigurationError`: if any fields are missing, superfluous or of the wrong
            type.
        """
        # Parse the fields
        parsed_fields, unparsed_fields = cls._parse_fields(
            fields=cls._get_fields(),
            values=values,
            case_transform=case_transform,
            raise_on_superfluous=True,
        )
        assert not unparsed_fields, (
            unparsed_fields,
            "Superfluous values present, despite them being disallowed?",
        )

        # Instantiate the class
        self = object.__new__(cls)

        for field_name, field_value in parsed_fields.items():
            setattr(self, field_name, field_value)

        return self

    @classmethod
    def load_from_json(
        cls,
        source: Path | IO[str] | IO[bytes] | Jsonable,
    ) -> Self:
        """
        Loads an instance of the config from the provided JSON source. The
        source can either be a path to a file, an open file-like object, or the
        result of `json.parse`.

        Note that **strings are not treated as paths**, but rather as already
        parsed string values.

        If `source` is a `Path`, and the file doesn't exist, a template will be
        dumped to the location to help out the user.

        ## Raises

        `ConfigurationError`: if any fields are missing, superfluous or of the wrong
            type.
        """

        # Load the JSON
        #
        # If a path was provided but doesn't exist, dump a template
        if isinstance(source, Path):
            try:
                with open(source, "r") as f:
                    raw_values = json5.load(f)

            except FileNotFoundError:
                source.parent.mkdir(parents=True, exist_ok=True)
                with open(source, "w") as f:
                    f.write(cls._create_json_template(cls._get_fields()))

                raise ConfigurationError(
                    f"Could not find the config file at `{source}`. A template has been created for you. Please fill out the values, then try again"
                )

            except ValueError as err:
                raise ConfigurationError(f"`{source}` is not a valid JSON file: {err}")

        # If the source is already parsed, use it as-is
        elif isinstance(source, (type(None), bool, int, float, str, tuple, list, dict)):
            raw_values = source

        # Read & parse file-like objects
        else:
            try:
                raw_values = json5.load(source)

            except ValueError as err:
                raise ConfigurationError(f"`{source}` is not valid JSON: {err}")

        # Make sure the JSON has parsed into a dictionary
        if not isinstance(raw_values, dict):
            raise ConfigurationError("The config JSON must be a dictionary.")

        # Parse the values into an instance
        return cls._load_from_values(
            values=raw_values.items(),
            case_transform=uniserde.case_convert.all_lower_to_camel_case,
        )

    @classmethod
    def load_from_environment(
        cls,
    ) -> Self:
        """
        Loads an instance of the config from the provided JSON source. The
        source can either be a path to a file, an open file-like object, or the
        result of `json.parse`.

        Note that **strings are not treated as paths**, but rather as already
        parsed string values.

        ## Raises

        `ConfigurationError`: if any fields are missing, superfluous or of the wrong
            type.
        """

        raise NotImplementedError("TODO: This function is entirely untested")

        # Fetch all fields from the environment
        raw_values: dict[str, str] = {}

        for py_field_name, field_type in cls._get_fields():
            env_name = py_field_name.upper()

            try:
                raw_value = os.environ[env_name]
            except KeyError:
                raise ConfigurationError(
                    f"There is no environment variable set for `{env_name}`"
                )

            raw_values[env_name] = raw_value

        # Right now all values are strings. Parse them into something more
        # adequate using JSON.
        semi_parsed: dict[str, Any] = {}

        for py_field_name, raw_value in raw_values.items():
            # Keep strings as-is
            if field_type is str:
                semi_parsed[py_field_name] = raw_value
                continue

            # Otherwise drag them through the JSON parser
            try:
                semi_parsed[py_field_name] = json5.loads(raw_value)
            except ValueError as err:
                raise ConfigurationError(f"`{raw_value}` is not a valid value") from err

        # Parse the fields into an instance
        return cls._load_from_values(
            values=semi_parsed.items(),
            case_transform=str.upper,
        )
