import psutil

from platval.collectors.capabilities import discover_psutil_capabilities


def test_missing_optional_readings_are_explicit(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(psutil, "cpu_freq", lambda: None)
    monkeypatch.delattr(psutil, "sensors_temperatures", raising=False)
    capabilities = {item.metric: item for item in discover_psutil_capabilities()}
    assert capabilities["cpu_frequency"].available is False
    assert capabilities["cpu_frequency"].limitation is not None
    assert capabilities["temperature"].available is False
    assert "conservative" in (capabilities["temperature"].limitation or "")


def test_supported_optional_readings_are_available(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(psutil, "cpu_freq", lambda: object())
    monkeypatch.setattr(psutil, "sensors_temperatures", lambda: {"cpu": [object()]}, raising=False)
    capabilities = {item.metric: item for item in discover_psutil_capabilities()}
    assert capabilities["cpu_frequency"].available is True
    assert capabilities["temperature"].available is True
    assert capabilities["temperature"].limitation is None
