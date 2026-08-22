"""Independent bounded psutil telemetry sampling."""

import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil

from platval.models.telemetry import SensorReading, TelemetrySample


class PsutilTelemetrySampler:
    """Collect samples on a background thread while a workload runs."""

    def __init__(self, *, interval_seconds: float, storage_path: Path, max_samples: int = 3600):
        if interval_seconds <= 0:
            raise ValueError("sampling interval must be greater than zero")
        if max_samples <= 0:
            raise ValueError("maximum sample count must be greater than zero")
        self._interval = interval_seconds
        self._storage_path = storage_path.resolve()
        self._max_samples = max_samples
        self._stop_event = threading.Event()
        self._samples: list[TelemetrySample] = []
        self._thread: threading.Thread | None = None
        self._started_monotonic = 0.0
        self._process = psutil.Process()

    @property
    def samples(self) -> list[TelemetrySample]:
        return list(self._samples)

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("telemetry sampler has already started")
        self._started_monotonic = time.monotonic()
        self._process.cpu_percent(interval=None)
        self._thread = threading.Thread(
            target=self._sample_loop, name="platval-telemetry", daemon=True
        )
        self._thread.start()

    def stop(self) -> list[TelemetrySample]:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=max(2.0, self._interval + 1.0))
            if self._thread.is_alive():
                raise RuntimeError("telemetry sampler did not stop within its bounded join time")
        return self.samples

    def _sample_loop(self) -> None:
        while not self._stop_event.is_set() and len(self._samples) < self._max_samples:
            try:
                sample = self._collect_sample()
            except (OSError, RuntimeError, psutil.Error) as exc:
                sample = TelemetrySample(
                    elapsed_seconds=time.monotonic() - self._started_monotonic,
                    timestamp=datetime.now(UTC),
                    collector_errors=[f"sample:{type(exc).__name__}"],
                )
            self._samples.append(sample)
            self._stop_event.wait(self._interval)

    def _collect_temperatures(self) -> list[SensorReading]:
        function = getattr(psutil, "sensors_temperatures", None)
        if function is None:
            return []
        readings: list[SensorReading] = []
        for source, entries in function().items():
            for index, entry in enumerate(entries):
                readings.append(
                    SensorReading(
                        name=entry.label or f"sensor-{index}",
                        value=float(entry.current),
                        unit="degC",
                        source=f"psutil:{source}",
                    )
                )
        return readings

    def _collect_sample(self) -> TelemetrySample:
        errors: list[str] = []
        frequency: float | None = None
        temperatures: list[SensorReading] = []
        try:
            cpu_frequency = psutil.cpu_freq()
            frequency = cpu_frequency.current if cpu_frequency is not None else None
        except (AttributeError, NotImplementedError, OSError, RuntimeError) as exc:
            errors.append(f"cpu_frequency:{type(exc).__name__}")
        try:
            temperatures = self._collect_temperatures()
        except (AttributeError, NotImplementedError, OSError, RuntimeError) as exc:
            errors.append(f"temperature:{type(exc).__name__}")
        memory = psutil.virtual_memory()
        process_memory = self._process.memory_info().rss
        disk_free = psutil.disk_usage(str(self._storage_path)).free
        return TelemetrySample(
            elapsed_seconds=time.monotonic() - self._started_monotonic,
            timestamp=datetime.now(UTC),
            cpu_utilization_percent=psutil.cpu_percent(interval=None),
            per_core_utilization_percent=psutil.cpu_percent(interval=None, percpu=True),
            cpu_frequency_mhz=frequency,
            process_cpu_percent=self._process.cpu_percent(interval=None),
            process_memory_bytes=process_memory,
            available_memory_bytes=memory.available,
            disk_free_bytes=disk_free,
            temperatures=temperatures,
            collector_errors=errors,
        )
