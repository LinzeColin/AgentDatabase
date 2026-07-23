"""Strict, bounded YAML loading for governed public or private policy files."""

from __future__ import annotations

import hashlib
import stat
from pathlib import Path
from typing import Any, Mapping, Tuple

import yaml


class GovernedConfigError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


class _NoAliasSafeLoader(yaml.SafeLoader):
    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(yaml.AliasEvent):
            raise yaml.YAMLError("YAML aliases are forbidden")
        return super().compose_node(parent, index)

    def construct_mapping(self, node: Any, deep: bool = False) -> Any:
        if not isinstance(node, yaml.MappingNode):
            return super().construct_mapping(node, deep=deep)
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in mapping
            except TypeError as exc:
                raise yaml.YAMLError("unhashable YAML mapping key is forbidden") from exc
            if duplicate:
                raise yaml.YAMLError("duplicate YAML mapping keys are forbidden")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def load_governed_yaml_mapping(path: Path, *, max_bytes: int) -> Tuple[Mapping[str, Any], str]:
    """Return an exact mapping and file SHA256 after path/type/size gates."""

    value = Path(path)
    try:
        metadata = value.lstat()
    except OSError as exc:
        raise GovernedConfigError("CONFIG_UNAVAILABLE", "governed config cannot be accessed") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise GovernedConfigError("CONFIG_PATH_UNSAFE", "governed config must be a single-link regular file")
    if type(max_bytes) is not int or max_bytes <= 0 or metadata.st_size > max_bytes:
        raise GovernedConfigError("CONFIG_SIZE_LIMIT", "governed config exceeds its byte ceiling")
    try:
        payload = value.read_bytes()
        raw = yaml.load(payload.decode("utf-8"), Loader=_NoAliasSafeLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise GovernedConfigError("CONFIG_PARSE", "governed config is not strict UTF-8 YAML") from exc
    if not isinstance(raw, dict) or any(not isinstance(key, str) for key in raw):
        raise GovernedConfigError("CONFIG_SCHEMA", "governed config root must be a string-keyed mapping")
    return raw, hashlib.sha256(payload).hexdigest()
