"""
This module provides the `ObjectId` class. If the `bson` module is available, it
is imported from there. Otherwise it falls back to a class with an identical,
albeit incomplete, interface.

uniserde expects the `bson` package provided by `pymongo`, NOT the one called
`bson` on pypi. However, both seem to work fine.
"""

import binascii
import os
import struct
import time
from typing import *  # type: ignore

from typing_extensions import TypeAlias

__all__ = ["ObjectId"]


class _ObjectId:
    """
    This is an incomplete clone of `bson.ObjectId`. Use this as a stand-in
    if the `bson` library isn't available. While this class aims to be
    similar to the original, it does not provide the same stringent
    uniqueness guarantees.
    """

    def __init__(
        self,
        oid: str | Literal["ObjectId"] | bytes | None = None,  # type: ignore
    ) -> None:
        if oid is None:
            self._id_blob = struct.pack(">I", int(time.time())) + os.urandom(8)

        elif isinstance(oid, bytes) and len(oid) == 12:
            self._id_blob = oid

        elif isinstance(oid, str) and len(oid) == 24:
            try:
                self._id_blob = bytes.fromhex(oid)
            except (TypeError, ValueError):
                raise ValueError(f"Invalid hex in ObjectId: {oid}")

        else:
            raise TypeError(
                f"ObjectIds must be 12 bytes or 24-character hex strings. Got {oid!r}"
            )

    @property
    def binary(self) -> bytes:
        """12-byte binary representation of this ObjectId."""
        return self._id_blob

    def __str__(self) -> str:
        return binascii.hexlify(self._id_blob).decode()

    def __repr__(self):
        return f"ObjectId('{str(self)}')"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ObjectId):
            return self._id_blob == other.binary

        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._id_blob)


try:
    import bson  # type: ignore

    ObjectId: TypeAlias = bson.ObjectId  # type: ignore
except ImportError:
    ObjectId: TypeAlias = _ObjectId  # type: ignore
