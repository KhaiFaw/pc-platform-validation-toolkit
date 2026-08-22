import json
from pathlib import Path

from platval.inventory.collector import _parse_power_plan, collect_platform_inventory


def test_power_plan_parser_extracts_display_name() -> None:
    output = "Power Scheme GUID: 00000000-0000-0000-0000-000000000000  (Balanced)"
    assert _parse_power_plan(output) == "Balanced"
    assert _parse_power_plan("localized output without a display name") is None


def test_inventory_is_sanitized_and_structurally_valid(tmp_path: Path) -> None:
    snapshot = collect_platform_inventory(storage_path=tmp_path)
    serialized = snapshot.model_dump_json()
    parsed = json.loads(serialized)
    assert parsed["platform"]["logical_processor_count"] > 0
    assert parsed["platform"]["total_memory_bytes"] > 0
    assert len(parsed["platform"]["sanitized_platform_fingerprint"]) == 64
    lowered = serialized.lower()
    for forbidden in ("username", "hostname", "serial_number", "mac_address", "product_key"):
        assert forbidden not in lowered
    assert str(Path.home()).lower() not in lowered


def test_inventory_rejects_non_directory_storage_path(tmp_path: Path) -> None:
    file_path = tmp_path / "not-a-directory"
    file_path.write_text("content", encoding="utf-8")
    try:
        collect_platform_inventory(storage_path=file_path)
    except ValueError as exc:
        assert "existing directory" in str(exc)
    else:
        raise AssertionError("a file must not be accepted as a storage directory")
