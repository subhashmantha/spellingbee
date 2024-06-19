import enum
import inspect
import types
from abc import ABC, abstractmethod
from typing import *  # type: ignore

from typing_extensions import TypeAlias

from . import case_convert, common, lazy_wrapper, serde_class
from .common import SerdeError

IN = TypeVar("IN")
OUT = TypeVar("OUT")

Handler: TypeAlias = Callable[["CachingSerDeserializer[IN, OUT]", IN, Type[OUT]], OUT]


class CachingSerDeserializer(ABC, Generic[IN, OUT]):
    """
    Serializes/Deserializes objects, while caching any type-specific handlers it
    creates. This provides massive speedups over constantly trying to figure out
    what to do. (~3x compared to the old approach.)

    Despite the name, currently only handles deserialization.
    """

    # Types which are passed through without any processing. Must be defined by
    # subclasses.
    _passthrough_types: Set[Type[IN]]

    # Maps (lazy, type) to handlers. This acts as cache for previously seen
    # types.
    #
    # Must be defined by subclasses. (An empty dict is fine.)
    _handler_cache: dict[tuple[bool, Type[IN]], Handler]

    # If a method of this name is present in a class (and it isn't the one
    # inherited from `Serde`) this will be used for handling that class, rather
    # than the default behavior.
    _override_method_name: str

    def __init_subclass__(cls) -> None:
        # Add handlers for all of the class's passthrough types
        def make_handler_from_passthrough_type(
            passthrough_type: Type,
        ) -> Handler:
            def result(self, value: IN, as_type: Type[OUT]) -> OUT:
                if not isinstance(value, passthrough_type) and not (
                    isinstance(value, int) and passthrough_type is float
                ):
                    raise SerdeError(f"Expected `{passthrough_type}`, got `{value}`")

                return value  # type: ignore

            return result

        for typ in cls._passthrough_types:
            handler = make_handler_from_passthrough_type(typ)
            cls._handler_cache[(True, typ)] = handler
            cls._handler_cache[(False, typ)] = handler

    def __init__(
        self,
        *,
        custom_deserializers: dict[Type, Callable[[IN, Type[OUT]], OUT]],
        lazy: bool,
    ):
        self._custom_deserializers = custom_deserializers
        self._lazy = lazy

    @abstractmethod
    def _get_class_fields(self, value_type: Type) -> Iterable[tuple[str, str, Type]]:
        """
        Return a tuple (python_name, json_name, type) for each field in the
        class.
        """
        raise NotImplementedError()

    def process(self, value: IN, as_type: Type[OUT]) -> OUT:
        # Special case: rapidly handle simple passthrough types to increase
        # performance
        if as_type in self._passthrough_types:
            if not isinstance(value, as_type) and not (
                isinstance(value, int) and as_type is float
            ):
                raise SerdeError(f"Expected `{as_type}`, got `{value}`")

            return value  # type: ignore

        # Otherwise get a handler and use it
        handler = self._get_handler(as_type)
        return handler(self, value, as_type)

    def _get_handler(
        self,
        value_type: Type,
    ) -> Handler:
        # Find a matching serializer
        type_key = common.get_type_key(value_type)

        # Custom handlers take precedence
        try:
            custom_handler = self._custom_deserializers[type_key]
        except KeyError:
            pass
        else:
            return lambda self, value, as_type: custom_handler(value, as_type)

        # Use a cached handler if possible
        try:
            return self._handler_cache[(self._lazy, type_key)]
        except KeyError:
            pass

        # Otherwise create the appropriate handler and cache it for next time
        assert inspect.isclass(value_type), value_type
        handler = self._create_class_handler(value_type)
        self._handler_cache[(self._lazy, type_key)] = handler

        return handler

    def _create_class_handler(
        self,
        value_type: Type,
    ) -> Handler:
        # Case: The class has a custom method for handling it
        #
        # This needs care, depending on whether the method was just overwritten
        # as a regular method, or as a static/class method.
        try:
            override_method = getattr(value_type, self._override_method_name)
        except AttributeError:
            pass
        else:
            serde_class_method = getattr(serde_class.Serde, self._override_method_name)

            try:
                override_method_func = override_method.__func__
            except AttributeError:
                override_method_func = override_method

            if override_method_func is not serde_class_method.__func__:
                return lambda self, value, _type: override_method(value, {})

        # Case enum.Flag
        if issubclass(value_type, enum.Flag):

            def handle_flag(self, value, _type):
                if not isinstance(value, list):
                    raise SerdeError(f"Expected a list, got `{value}`")

                result = value_type(0)

                for item in value:
                    if not isinstance(item, str):
                        raise SerdeError(f"Expected enumeration string, got `{item}`")

                    try:
                        py_name = case_convert.camel_case_to_all_upper(
                            item
                        )  # ValueError if not camel case
                        result |= value_type[py_name]  # ValueError if not in enum
                    except KeyError:
                        raise SerdeError(
                            f"Invalid enumeration value `{item}`"
                        ) from None

                return result

            return handle_flag

        # Case: enum.Enum
        if issubclass(value_type, enum.Enum):

            def handle_enum(self, value, _type):
                if not isinstance(value, str):
                    raise SerdeError(f"Expected enumeration string, got `{value}`")

                try:
                    py_name = case_convert.camel_case_to_all_upper(
                        value
                    )  # ValueError if not camel case
                    return value_type[py_name]  # ValueError if not in enum
                except KeyError:
                    raise SerdeError(f"Invalid enumeration value `{value}`") from None

            return handle_enum

        # Case: Base which is serialized `@as_child`
        if common.should_serialize_as_child(value_type):
            # Precompute a set of all possible classes
            child_classes_and_handlers_by_doc_name = {
                case_convert.upper_camel_case_to_camel_case(cls.__name__): (
                    cls,
                    self._create_fieldwise_class_handler(cls),
                )
                for cls in common.all_subclasses(value_type, True)
            }

            def handle_as_child(self, value, _type):
                # Look up the real type
                try:
                    type_tag = value.pop("type")
                except KeyError:
                    raise SerdeError(f"Object is missing the `type` field") from None

                # Get the class
                try:
                    (
                        child_class,
                        child_class_handler,
                    ) = child_classes_and_handlers_by_doc_name[type_tag]
                except KeyError:
                    raise SerdeError(
                        f"Encountered invalid type tag `{type_tag}`"
                    ) from None

                # Delegate to that class's handler
                return child_class_handler(self, value, child_class)

            # TODO: The generated handler works for all subclasses, but will
            #       only be cached for the one class that has just been
            #       requested. Consider explicitly caching it for all classes.

            return handle_as_child

        # Case: Regular old class
        return self._create_fieldwise_class_handler(value_type)

    def _create_fieldwise_class_handler(self, value_type: Type) -> Handler:
        # Lazy?
        if self._lazy and lazy_wrapper.can_create_lazy_instance(value_type):

            def _handler(self, value, _type):
                return lazy_wrapper.create_lazy_instance(
                    value,
                    self,
                    value_type,
                )

            return _handler

        # Eager
        handler = FieldwiseClassHandler()

        for py_name, doc_name, field_type in self._get_class_fields(value_type):
            handler.add_field(
                py_name,
                doc_name,
                field_type,
                self._get_handler(field_type),
            )

        return handler


class FieldwiseClassHandler:
    """
    Deserializes a class, field by field. The fields and their handlers are
    already passed in the constructor to avoid having to recompute them for each
    instance.
    """

    fields: list[tuple[str, str, Type, Handler]]

    def __init__(self):
        self.fields = []

    def add_field(
        self,
        python_name: str,
        doc_name: str,
        field_type: Type,
        handler: Handler,
    ):
        self.fields.append((python_name, doc_name, field_type, handler))

    def __call__(
        self,
        calling_ser_deserializer: CachingSerDeserializer,
        raw: Any,
        value_type: Type,
    ) -> Any:
        # Make sure the raw value is a dict
        if not isinstance(raw, dict):
            raise SerdeError(f"Expected object, got `{raw!r}`")

        # Create an instance of the class
        result = object.__new__(value_type)
        result_dict = vars(result)

        # Handle all fields
        for py_name, doc_name, field_type, handler in self.fields:
            # Get the raw value
            try:
                raw_value = raw.pop(doc_name)
            except KeyError:
                raise SerdeError(f"Missing field `{doc_name!r}`") from None

            # Process it
            processed_value = handler(calling_ser_deserializer, raw_value, field_type)

            # Store it
            result_dict[py_name] = processed_value

        # Make sure there are no stray fields
        if len(raw) > 0:
            raise SerdeError(
                f"Superfluous object fields `{'`, `'.join(map(str, raw.keys()))}`"
            )

        return result
