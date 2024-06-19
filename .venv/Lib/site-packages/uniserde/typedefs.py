from datetime import datetime
from typing import *  # type: ignore

from typing_extensions import TypeAlias

from .objectid_proxy import ObjectId

__all__ = [
    "Jsonable",
    "Bsonable",
    "JsonDoc",
    "BsonDoc",
]


Jsonable: TypeAlias = Union[
    None,
    bool,
    int,
    float,
    str,
    dict[str, "Jsonable"],
    list["Jsonable"],
    tuple["Jsonable", ...],
]

Bsonable: TypeAlias = Union[
    None,
    bool,
    int,
    float,
    str,
    dict[str, "Bsonable"],
    list["Bsonable"],
    tuple["Bsonable", ...],
    bytes,
    ObjectId,
    datetime,
]

JsonDoc = dict[str, Jsonable]
BsonDoc = dict[str, Bsonable]
