import time
from pathlib import Path

from platval.collectors.sampler import PsutilTelemetrySampler


def test_sampler_collects_bounded_samples_and_stops(tmp_path: Path) -> None:
    sampler = PsutilTelemetrySampler(
        interval_seconds=0.01,
        storage_path=tmp_path,
        max_samples=3,
    )
    sampler.start()
    time.sleep(0.06)
    samples = sampler.stop()
    assert 1 <= len(samples) <= 3
    assert all(sample.elapsed_seconds >= 0 for sample in samples)
    assert all(sample.available_memory_bytes is not None for sample in samples)


def test_sampler_rejects_invalid_bounds(tmp_path: Path) -> None:
    try:
        PsutilTelemetrySampler(interval_seconds=0, storage_path=tmp_path)
    except ValueError as exc:
        assert "interval" in str(exc)
    else:
        raise AssertionError("zero interval must be rejected")
