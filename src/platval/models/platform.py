"""Sanitized platform identity model and stable fingerprinting."""

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from pydantic import Field, field_validator

from platval.constants import FINGERPRINT_SCHEMA_VERSION
from platval.models.common import DomainModel


def sanitized_platform_fingerprint(values: Mapping[str, Any]) -> str:
    """Hash stable configuration fields while excluding free space and capabilities."""
    raw_caches = values.get("caches") or []
    caches = [
        cache.model_dump() if isinstance(cache, DomainModel) else cache for cache in raw_caches
    ]
    raw_storage = values.get("storage_volume") or {}
    storage = (
        raw_storage.model_dump() if isinstance(raw_storage, DomainModel) else dict(raw_storage)
    )
    canonical = {
        "schema_version": FINGERPRINT_SCHEMA_VERSION,
        "operating_system": values.get("operating_system"),
        "operating_system_version": values.get("operating_system_version"),
        "architecture": values.get("architecture"),
        "cpu_vendor": values.get("cpu_vendor"),
        "cpu_brand": values.get("cpu_brand"),
        "logical_processor_count": values.get("logical_processor_count"),
        "physical_processor_count": values.get("physical_processor_count"),
        "caches": sorted(
            caches,
            key=lambda cache: (
                cache.get("level", 0),
                cache.get("kind", ""),
                cache.get("size_bytes", 0),
            ),
        ),
        "total_memory_bytes": values.get("total_memory_bytes"),
        "storage_volume": {
            "filesystem": storage.get("filesystem"),
            "capacity_bytes": storage.get("capacity_bytes"),
        },
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class CacheDescriptor(DomainModel):
    level: int = Field(ge=1, le=4)
    kind: str = Field(min_length=1, max_length=32)
    size_bytes: int = Field(gt=0)
    line_size_bytes: int | None = Field(default=None, gt=0)


class StorageVolume(DomainModel):
    filesystem: str | None = Field(default=None, max_length=32)
    capacity_bytes: int = Field(gt=0)
    free_bytes: int = Field(ge=0)


class PlatformIdentity(DomainModel):
    tool_version: str = Field(min_length=1)
    operating_system: str = Field(min_length=1)
    operating_system_version: str = Field(min_length=1)
    operating_system_build: str | None = None
    python_version: str = Field(min_length=1)
    architecture: str = Field(min_length=1)
    cpu_vendor: str | None = None
    cpu_brand: str | None = None
    logical_processor_count: int = Field(gt=0)
    physical_processor_count: int | None = Field(default=None, gt=0)
    caches: list[CacheDescriptor] = Field(default_factory=list)
    total_memory_bytes: int = Field(gt=0)
    storage_volume: StorageVolume
    power_plan_name: str | None = Field(default=None, max_length=128)
    native_probe_version: str | None = None
    capability_flags: dict[str, bool] = Field(default_factory=dict)
    sanitized_platform_fingerprint: str

    @field_validator("sanitized_platform_fingerprint")
    @classmethod
    def fingerprint_is_sha256(cls, value: str) -> str:
        if re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError("fingerprint must be a lowercase SHA-256 digest")
        return value
