import json
import subprocess
from pathlib import Path

import pytest

from platval.inventory.native_probe import NativeProbeStatus, invoke_native_probe


def valid_response() -> dict[str, object]:
    return {
        "schema_version": 1,
        "probe_version": "0.1.0",
        "architecture": "x86_64",
        "vendor_id": "GenuineIntel",
        "brand_string": "Synthetic CPU",
        "max_basic_leaf": 7,
        "max_extended_leaf": 0x80000004,
        "features": {
            "sse2": True,
            "sse41": True,
            "sse42": True,
            "avx_hardware": True,
            "avx2_hardware": True,
            "avx_os_enabled": True,
            "aes": True,
            "vmx": True,
            "svm": False,
            "virtualization_hardware": True,
        },
        "caches": [
            {
                "level": 3,
                "kind": "unified",
                "size_bytes": 524288,
                "line_size_bytes": 64,
                "sets": 1024,
                "ways": 8,
                "partitions": 1,
            }
        ],
    }


def make_executable_placeholder(tmp_path: Path) -> Path:
    executable = tmp_path / "cpuid_probe.exe"
    executable.touch()
    return executable


def test_missing_probe_is_a_documented_capability_limit() -> None:
    outcome = invoke_native_probe(None)
    assert outcome.status is NativeProbeStatus.MISSING
    assert outcome.data is None
    assert "not installed" in (outcome.limitation or "")


def test_valid_probe_response_is_typed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    executable = make_executable_placeholder(tmp_path)

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(valid_response()), stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    outcome = invoke_native_probe(executable)
    assert outcome.status is NativeProbeStatus.AVAILABLE
    assert outcome.data is not None
    assert outcome.data.vendor_id == "GenuineIntel"
    assert outcome.data.features.avx_os_enabled is True


def test_incompatible_schema_degrades_cleanly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executable = make_executable_placeholder(tmp_path)
    response = valid_response()
    response["schema_version"] = 99
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(response), stderr="schema detail"
        ),
    )
    outcome = invoke_native_probe(executable)
    assert outcome.status is NativeProbeStatus.INCOMPATIBLE
    assert outcome.data is None
    assert outcome.stderr_summary == "schema detail"


def test_nonzero_exit_preserves_bounded_diagnostic(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executable = make_executable_placeholder(tmp_path)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=[], returncode=4, stdout="", stderr="internal failure\n"
        ),
    )
    outcome = invoke_native_probe(executable)
    assert outcome.status is NativeProbeStatus.ERROR
    assert outcome.stderr_summary == "internal failure"


def test_timeout_is_reported_without_exception(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executable = make_executable_placeholder(tmp_path)

    def raise_timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd="cpuid_probe", timeout=1)

    monkeypatch.setattr(subprocess, "run", raise_timeout)
    outcome = invoke_native_probe(executable, timeout_seconds=1)
    assert outcome.status is NativeProbeStatus.ERROR
    assert "1-second timeout" in (outcome.limitation or "")
