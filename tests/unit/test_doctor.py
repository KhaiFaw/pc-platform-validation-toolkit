from pathlib import Path

from platval.doctor import DoctorStatus, run_doctor


def test_doctor_verifies_runtime_and_reports_optional_probe(tmp_path: Path) -> None:
    report = run_doctor(runtime_directory=tmp_path / "runtime")
    checks = {check.name: check for check in report.checks}
    assert checks["Python version"].status is DoctorStatus.PASS
    assert checks["Python dependencies"].status is DoctorStatus.PASS
    assert checks["runtime directory"].status is DoctorStatus.PASS
    assert checks["temporary disk space"].status is DoctorStatus.PASS
    assert checks["native CPUID probe"].status in {DoctorStatus.PASS, DoctorStatus.WARN}
    assert report.overall_status in {DoctorStatus.PASS, DoctorStatus.WARN}
