"""
Utilities for getting metadata about your own package.
"""

import importlib.metadata
import inspect
import sys
from pathlib import Path
from typing import *  # type: ignore


def _get_root_directory(caller: inspect.FrameInfo) -> Path:
    """
    Return the root directory of the calling module, accounting for submodules.

    For example, if the calling module is `foo.bar.baz`, and `foo` is located
    at `/home/user/foo`, this function will return `/home/user/foo`.
    """
    caller_path = Path(caller.filename).absolute()

    # `__init__` files aren't their own submodules, so treat them as their
    # parent
    if caller_path.name == "__init__.py":
        caller_path = caller_path.parent

    # How deep is this submodule?
    depth: int = caller.frame.f_globals["__name__"].count(".")

    for _ in range(depth):
        caller_path = caller_path.parent

    return caller_path


def _find_pyproject_toml(module_directory: Path) -> Path:
    """
    Attempts to locate a project's `pyproject.toml` file. It will look in common
    locations and return the path if found, or raise a `FileNotFoundError` if
    not.
    """

    def _iter_toml_paths() -> Iterable[Path]:
        # In a typicical project the toml is right next to the module
        yield module_directory.parent / "pyproject.toml"

        # However, some projects have a `src` directory
        if module_directory.parent.name == "src":
            yield module_directory.parent.parent / "pyproject.toml"

    # Try to find the toml
    for toml_path in _iter_toml_paths():
        if toml_path.exists():
            return toml_path

    # Nothing was found
    raise FileNotFoundError("Could not find `pyproject.toml`")


def get_package_version(own_package_pypi_name: str) -> str:
    """
    Determine the version of **the calling package**. `own_package_pypi_name` is
    the name of the package, as you would type to install it from pypi.

    You can **not use this function to look up any packages other than your
    own**.
    """

    # Try to just ask python
    try:
        return importlib.metadata.version(own_package_pypi_name)
    except importlib.metadata.PackageNotFoundError:
        pass

    # While the approach above is clean, it fails during development. In that
    # case, read the version from the `pyproject.toml` file.
    import tomllib

    caller_frame = inspect.stack()[1]
    toml_path = _find_pyproject_toml(_get_root_directory(caller_frame))

    try:
        with open(toml_path, "rb") as f:
            toml_contents = tomllib.load(f)

    except FileNotFoundError:
        raise RuntimeError(f"Cannot find `pyproject.toml` at `{toml_path}`") from None

    except tomllib.TOMLDecodeError as e:
        raise RuntimeError(f"`{toml_path}` is invalid TOML: {e}") from None

    # The version can be stored in different places, depending on the tooling
    try:
        return toml_contents["project"]["version"]
    except KeyError:
        pass

    try:
        return toml_contents["tool"]["poetry"]["version"]
    except KeyError:
        pass

    raise RuntimeError(
        f"`{toml_path}` does not contain a `tool.poetry.version` field"
    ) from None
