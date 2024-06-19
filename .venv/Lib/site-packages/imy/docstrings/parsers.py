from __future__ import annotations

import collections
import dataclasses
import inspect
import textwrap
import typing
import warnings
from dataclasses import is_dataclass
from typing import *  # type: ignore

import introspection
import introspection.types
import introspection.typing
from uniserde import Jsonable

from . import data_models


def split_docstring_into_sections(docstring: str) -> tuple[str, dict[str, str]]:
    """
    Splits the given docstring into sections separated by markdown headings. The
    result is the part of the string before the first heading, and a dictionary
    mapping the heading names to the text of the sections ("the summary").

    If the docstring starts with a heading it will not create a separate section
    and the text of that section will be considered part of the summary.
    """
    # Drop the title if it exists
    if docstring.startswith("#") and not docstring.startswith("##"):
        docstring = docstring.split("\n", 1)[1]

    # Split the docstring into sections
    sections: dict[str, list[str]] = {}
    details: list[str] = []
    current_section: list[str] = details
    currently_inside_code_block: bool = False

    # Process the individual lines
    for line in docstring.splitlines():
        # Code block?
        if line.startswith("```"):
            currently_inside_code_block = not currently_inside_code_block
            current_section.append(line)

        # Section Header
        elif line.startswith("#") and not currently_inside_code_block:
            section_name = line.strip()
            current_section = sections.setdefault(section_name, [])

        # Nothing to see here
        else:
            current_section.append(line)

    # Post-process the sections
    def postprocess(section: list[str]) -> str:
        return "\n".join(section).strip()

    return postprocess(details), {
        name: postprocess(section) for name, section in sections.items()
    }


def parse_key_value_section(section_string: str) -> dict[str, str]:
    """
    Some docstring sections are formatted as a list of key-value pairs, such as
    this:

    ```
    key: A description of the key.
    `key_in_code`: A description of the key in code.
    ```

    (Note the optional backticks around the key - these are stripped if present)

    This function splits such a section into a dictionary of key-value pairs.
    """
    result_lines: dict[str, list[str]] = {}
    current_value: list[str] = []

    # Process the lines individually
    for raw_line in section_string.splitlines():
        # Strip the line and calculate the indentation
        strip_line = raw_line.lstrip()
        indent = len(raw_line) - len(strip_line)
        strip_line = strip_line.rstrip()

        # Continuation of the previous value
        if indent > 0 or not strip_line:
            current_value.append(raw_line)
            continue

        # New value?
        parts = strip_line.split(":", 1)

        # Kinda, but it's mistyped
        if len(parts) == 1:
            # TODO: Warn somehow?
            current_value.append(raw_line)
            continue

        # Yes, for real this time
        key, value = parts
        key = key.strip().strip("`").strip()
        value = value.lstrip()
        current_value = [value]
        result_lines[key] = current_value

    # Postprocess the values. The lines need to be joined and the values
    # dedented.
    result: dict[str, str] = {}

    for key, lines in result_lines.items():
        assert lines, (key, lines)

        # The first line has weird indendation, due to following the separator.
        # Strip it.
        value = lines[0].lstrip()

        # The remaining lines need to be dedented
        if len(lines) > 1:
            tail = "\n".join(lines[1:])
            tail = textwrap.dedent(tail)
            value = f"{value}\n{tail}"

        result[key] = value

    return result


def parse_details(details: str) -> tuple[str | None, str | None]:
    """
    Given the details part of a docstring, split it into summary and details.
    Either value may be Nonne if they are not present in the original string.
    """
    details = details.strip()

    # Split into summary & details
    lines = details.split("\n")

    short_lines: list[str] = []
    long_lines: list[str] = []
    cur_lines = short_lines

    for raw_line in lines:
        strip_line = raw_line.strip()

        cur_lines.append(raw_line)

        if not strip_line:
            cur_lines = long_lines

    # Join the lines
    short_description = "\n".join(short_lines).strip()
    long_description = "\n".join(long_lines).strip()

    if not short_description:
        short_description = None

    if not long_description:
        long_description = None

    # Done
    return short_description, long_description


def parse_docstring(
    docstring: str,
    *,
    key_sections: Iterable[str],
) -> data_models.Docstring:
    """
    Parses a docstring into

    - summary
    - details
    - sections

    Any sections listed in `key_sections` will be parsed as key-value pairs and
    returned as sections. Any remaining sections will be re-joined into the
    details.

    Any sections listed in `key_sections` that are not present in the docstring
    will be imputed as empty.
    """
    # Remove consistent indentation
    docstring = textwrap.dedent(docstring).strip()

    # Split the docstring into (summary + details) and sections
    summary_and_details, sections = split_docstring_into_sections(docstring)

    # Split into summary and details
    summary, details = parse_details(summary_and_details)
    del summary_and_details

    if details is None:
        details = ""

    # Find and parse all key-value sections
    key_sections = set(key_sections)
    key_value_sections: dict[str, dict[str, str]] = {}

    for section_name, section_contents in sections.items():
        # Key section?
        normalized_section_name = section_name.lstrip("#").strip().lower()

        if normalized_section_name in key_sections:
            key_value_sections[normalized_section_name] = parse_key_value_section(
                section_contents
            )

        # Text section
        else:
            details += f"\n\n{section_name}\n\n{section_contents}"

    # Don't keep around an empty details section
    details = details.strip()

    if not details:
        details = None

    # Make sure all requested sections are present
    missing_sections = key_sections - key_value_sections.keys()

    for missing_section in missing_sections:
        key_value_sections[missing_section] = {}

    # Done
    return data_models.Docstring(
        summary=summary,
        details=details,
        key_sections=key_value_sections,
    )


def parse_function(
    func: Callable[..., Any] | classmethod | staticmethod,
) -> data_models.FunctionDocs:
    """
    Given a function, parse its signature and docstring into a `FunctionDocs`
    object.
    """

    def parse_annotation(
        annotation: object,
    ) -> introspection.types.TypeAnnotation | data_models.Unset:
        if annotation is inspect.Parameter.empty:
            return data_models.UNSET

        # Recursive types can cause issues. In particular, we have `Jsonable`,
        # which is a recursive type, and `JsonDoc`, which references `Jsonable`.
        # So if a module imports `JsonDoc` but doesn't import `Jsonable`, it's
        # impossible to evaluate the forward reference `"Jsonable"` in that
        # module.
        #
        # A similar problem exists due to dataclasses: Every `Component`
        # subclass receives a constructor based on the type annotations in
        # `Component`, but of course the relevant imports aren't there.
        #
        # As a workaround, we'll make the missing names available in every
        # module.
        extra_globals = collections.ChainMap(
            {"Jsonable": Jsonable},
            vars(typing),  # type: ignore
        )

        return introspection.typing.resolve_forward_refs(
            annotation,  # type: ignore
            func.__module__,
            extra_globals=extra_globals,
            mode="ast",
            treat_name_errors_as_imports=True,
            strict=True,
        )

    is_class_method = is_static_method = False

    if isinstance(func, staticmethod):
        is_static_method = True
        func = func.__func__
    elif isinstance(func, classmethod):
        is_class_method = True
        func = func.__func__

    # Parse the parameters
    signature = inspect.signature(func)
    parameters: dict[str, data_models.FunctionParameter] = {}

    for param_name, param in signature.parameters.items():
        if param.default == inspect.Parameter.empty:
            param_default = data_models.UNSET
        else:
            param_default = param.default

        parameters[param_name] = data_models.FunctionParameter(
            name=param_name,
            type=parse_annotation(param.annotation),
            default=param_default,
            kw_only=param.kind == inspect.Parameter.KEYWORD_ONLY,
            collect_positional=param.kind == inspect.Parameter.VAR_POSITIONAL,
            collect_keyword=param.kind == inspect.Parameter.VAR_KEYWORD,
            description=None,
        )

    # Parse the docstring
    docstring = inspect.getdoc(func)

    if docstring is None:
        parsed = data_models.Docstring(summary=None, details=None, key_sections={})
        raises = []
        metadata = data_models.FunctionMetadata.from_dictionary({})
    else:
        parsed = parse_docstring(
            docstring,
            key_sections=[
                "parameters",
                "raises",
                "metadata",
            ],
        )

        # Add any information learned about parameters from the docstring
        for param_name, param_details in parsed.key_sections["parameters"].items():
            try:
                result_param = parameters[param_name]
            except KeyError:
                warnings.warn(
                    f"The docstring for function `{func.__name__}` mentions a parameter `{param_name}` that does not exist in the function signature."
                )
                continue

            result_param.description = param_details

        # Add information about raised exceptions
        raises = list(parsed.key_sections["raises"].items())

        # Parse the metadata
        metadata = data_models.FunctionMetadata.from_dictionary(
            parsed.key_sections["metadata"]
        )

    # Build the result
    return data_models.FunctionDocs(
        object=func,
        name=func.__name__,
        parameters=list(parameters.values()),
        return_type=parse_annotation(signature.return_annotation),
        synchronous=not inspect.iscoroutinefunction(func),
        class_method=is_class_method,
        static_method=is_static_method,
        summary=parsed.summary,
        details=parsed.details,
        raises=raises,
        metadata=metadata,
    )


def _parse_class_docstring_with_inheritance(
    cls: type,
    *,
    key_sections: Iterable[str],
    merge_key_section: Callable[
        [str, dict[str, str], dict[str, str]], dict[str, str]
    ] = lambda name, parent, child: {**parent, **child},
) -> data_models.Docstring:
    """
    Parses the docstring of a class in the same format as `parse_docstring`, but
    accounts for inheritance: Key-Value sections of all classes are merged, in a
    way that preserves child docs over parent docs.
    """

    # Parse the docstring for this class
    raw_docs = inspect.getdoc(cls)

    key_sections = set(key_sections)
    parsed_docs = parse_docstring(
        "" if raw_docs is None else raw_docs,
        key_sections=key_sections,
    )

    # Get the docstrings for the base classes
    base_docs: list[data_models.Docstring] = []

    for base in cls.__bases__:
        base_docs.append(
            _parse_class_docstring_with_inheritance(
                base,
                key_sections=key_sections,
                merge_key_section=merge_key_section,
            )
        )

    # Merge the docstrings
    result_sections: dict[str, dict[str, str]] = {}
    all_in_order = base_docs + [parsed_docs]

    for cur_docs in all_in_order:
        for section_name, cur_section in cur_docs.key_sections.items():
            result_section = result_sections.get(section_name, {})
            result_section = merge_key_section(
                section_name, result_section, cur_section
            )
            result_sections[section_name] = result_section

    parsed_docs.key_sections = result_sections

    # Done
    return parsed_docs


def parse_class(cls: type) -> data_models.ClassDocs:
    """
    Given a class, parse its signature an docstring into a `ClassDocs` object.
    """

    # Parse the functions
    #
    # Make sure to add functions from base classes as well
    functions_by_name: dict[str, data_models.FunctionDocs] = {}

    def add_functions(cls: type) -> None:
        # Chain to the base classes
        for base in cls.__bases__:
            add_functions(base)

        # Then process this class. This way locals functions override inherited
        # ones.
        for name, func in vars(cls).items():
            if (
                inspect.isfunction(func)
                or isinstance(func, classmethod)
                or isinstance(func, staticmethod)
            ):
                func_docs = parse_function(func)
                functions_by_name[name] = func_docs

    add_functions(cls)

    # Do the same for fields
    fields_by_name: dict[str, data_models.ClassField] = {}
    properties: list[data_models.Property] = []

    def add_fields(cls: type) -> None:
        # Chain to the base classes
        for base in cls.__bases__:
            add_fields(base)

        # Then process this class. This way locals fields override inherited
        # ones.
        for attribute_name, annotation in vars(cls).get("__annotations__", {}).items():
            attribute_type = introspection.typing.resolve_forward_refs(
                annotation=annotation,
                context=cls.__module__,
                mode="ast",
                strict=True,
                treat_name_errors_as_imports=True,
            )

            fields_by_name[attribute_name] = data_models.ClassField(
                name=attribute_name,
                type=attribute_type,  # type: ignore
                default=None,
                description=None,
            )

        # Properties are also fields
        for prop in vars(cls).values():
            if isinstance(prop, property):
                properties.append(data_models.Property.from_property(prop))

    add_fields(cls)

    # Is this a dataclass? If so, get the fields from there
    if is_dataclass(cls):
        for dataclass_field in dataclasses.fields(cls):
            doc_field = fields_by_name[dataclass_field.name]

            # Default value?
            if dataclass_field.default is not dataclasses.MISSING:
                doc_field.default = repr(dataclass_field.default)

            # Default factory?
            elif dataclass_field.default_factory is not dataclasses.MISSING:
                doc_field.default = repr(dataclass_field.default_factory())

    # Prepare a function for merging key sections
    def merge_key_section(
        name: str,
        parent: dict[str, str],
        child: dict[str, str],
    ) -> dict[str, str]:
        # Metadata is special: The parent doesn't matter, the child always wins.
        # This is to avoid unexpected situations, where a class would be e.g.
        # private, just because the parent is private.
        if name == "metadata":
            return child

        # Otherwise merge the two. Child values override parent values.
        return {**parent, **child}

    # Parse the docstring
    docs = _parse_class_docstring_with_inheritance(
        cls,
        key_sections=[
            "attributes",
            "metadata",
        ],
        merge_key_section=merge_key_section,
    )

    # Add any information learned about fields from the docstring
    for field_name, field_details in docs.key_sections["attributes"].items():
        try:
            result_field = fields_by_name[field_name]
        except KeyError:
            # Warn about the missing field, unless there's a property with that
            # name
            if not isinstance(getattr(cls, field_name, None), property):
                warnings.warn(
                    f"The docstring for class `{cls.__name__}` mentions a field `{field_name}` that does not exist in the class."
                )
            continue

        result_field.description = field_details

    # If `__init__` is missing documentation for any parameters, try to copy the
    # values from matching fields.
    for func_docs in functions_by_name.values():
        if func_docs.name != "__init__":
            continue

        for param in func_docs.parameters:
            if param.description is not None:
                continue

            try:
                field = fields_by_name[param.name]
            except KeyError:
                continue

            param.description = field.description

        break

    # Build the result
    return data_models.ClassDocs(
        object=cls,
        name=cls.__name__,
        attributes=list(fields_by_name.values()),
        properties=properties,
        functions=list(functions_by_name.values()),
        summary=docs.summary,
        details=docs.details,
        metadata=data_models.ClassMetadata.from_dictionary(
            docs.key_sections["metadata"]
        ),
    )
