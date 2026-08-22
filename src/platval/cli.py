"""Command-line entry point for inspection and validation workflows."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from platval.constants import TOOL_VERSION
from platval.doctor import DoctorStatus, run_doctor
from platval.inventory import collect_platform_inventory, locate_native_probe
from platval.models.status import ResultStatus
from platval.persistence import (
    ArtifactError,
    BaselineSourceError,
    PersistenceError,
    RunNotFoundError,
    SQLiteRepository,
    StoredRun,
    delete_run_recoverably,
    load_stored_run,
    persist_execution,
)
from platval.runner import PlanLoadError, load_test_plan, run_validation_plan
from platval.workloads import CancellationToken, WorkloadCancelled

app = typer.Typer(
    name="platval",
    help="Run bounded, requirements-based PC platform validation.",
    no_args_is_help=True,
    add_completion=False,
)
runs_app = typer.Typer(help="List, inspect, or remove persisted validation runs.")
app.add_typer(runs_app, name="runs")


def version_callback(value: bool) -> None:
    """Print the package version and exit."""
    if value:
        typer.echo(f"platval {TOOL_VERSION}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=version_callback, is_eager=True, help="Show version."),
    ] = None,
) -> None:
    """PC Platform Validation Toolkit."""


@app.command("inventory")
def inventory_command(
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit the complete sanitized JSON snapshot.")
    ] = False,
    storage_path: Annotated[
        Path,
        typer.Option(
            "--storage-path",
            help="Directory whose containing volume will be used for storage validation.",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ] = Path("."),
    native_probe: Annotated[
        Path | None,
        typer.Option("--native-probe", help="Explicit cpuid_probe executable path."),
    ] = None,
) -> None:
    """Collect sanitized platform identity and capability information."""
    try:
        snapshot = collect_platform_inventory(
            storage_path=storage_path,
            native_probe_path=locate_native_probe(native_probe),
        )
    except (OSError, ValueError) as exc:
        typer.echo(f"Inventory failed: {exc}", err=True)
        raise typer.Exit(code=2) from None

    if json_output:
        typer.echo(snapshot.model_dump_json(indent=2))
        return

    platform = snapshot.platform
    table = Table(title="Sanitized platform inventory", show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row(
        "Operating system", f"{platform.operating_system} {platform.operating_system_version}"
    )
    table.add_row("Architecture", platform.architecture)
    table.add_row("CPU", platform.cpu_brand or "UNAVAILABLE")
    table.add_row(
        "Processors",
        f"{platform.physical_processor_count or 'UNAVAILABLE'} physical / "
        f"{platform.logical_processor_count} logical",
    )
    table.add_row("Memory", f"{platform.total_memory_bytes / (1024**3):.2f} GiB")
    table.add_row("Power plan", platform.power_plan_name or "UNAVAILABLE")
    table.add_row("Native probe", platform.native_probe_version or "UNAVAILABLE")
    table.add_row("Fingerprint", platform.sanitized_platform_fingerprint)
    console = Console()
    console.print(table)
    for limitation in snapshot.limitations:
        console.print(f"[yellow]WARN[/yellow] {limitation}")


@app.command("doctor")
def doctor_command(
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit the diagnostic report as JSON.")
    ] = False,
    runtime_directory: Annotated[
        Path,
        typer.Option("--runtime-dir", help="Runtime data directory to verify."),
    ] = Path(".platval"),
    native_probe: Annotated[
        Path | None,
        typer.Option("--native-probe", help="Explicit cpuid_probe executable path."),
    ] = None,
) -> None:
    """Check prerequisites and optional platform capabilities."""
    report = run_doctor(
        runtime_directory=runtime_directory,
        native_probe_path=locate_native_probe(native_probe),
    )
    if json_output:
        typer.echo(report.model_dump_json(indent=2))
    else:
        table = Table(title=f"platval doctor: {report.overall_status}")
        table.add_column("Status")
        table.add_column("Check")
        table.add_column("Detail")
        for check in report.checks:
            style = {
                DoctorStatus.PASS: "green",
                DoctorStatus.WARN: "yellow",
                DoctorStatus.FAIL: "red",
            }[check.status]
            table.add_row(f"[{style}]{check.status}[/{style}]", check.name, check.detail)
        Console().print(table)
    if report.overall_status is DoctorStatus.FAIL:
        raise typer.Exit(code=3)


@app.command("run")
def run_command(
    plan_path: Annotated[
        Path,
        typer.Option(
            "--plan",
            help="Versioned YAML test plan.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit the structured run and raw telemetry as JSON.")
    ] = False,
    runtime_directory: Annotated[
        Path, typer.Option("--runtime-dir", help="Directory for temporary runtime data.")
    ] = Path(".platval"),
    native_probe: Annotated[
        Path | None,
        typer.Option("--native-probe", help="Explicit cpuid_probe executable path."),
    ] = None,
) -> None:
    """Execute a bounded validation plan without persisting it."""
    try:
        plan = load_test_plan(plan_path)
    except PlanLoadError as exc:
        typer.echo(f"Plan error: {exc}", err=True)
        raise typer.Exit(code=2) from None

    token = CancellationToken()
    try:
        execution = run_validation_plan(
            plan,
            runtime_directory=runtime_directory,
            native_probe_path=locate_native_probe(native_probe),
            token=token,
        )
        artifact = persist_execution(execution, runtime_directory=runtime_directory)
    except (KeyboardInterrupt, WorkloadCancelled):
        token.cancel()
        typer.echo("Validation cancelled; workload cleanup completed.", err=True)
        raise typer.Exit(code=130) from None
    except (OSError, ValueError, RuntimeError) as exc:
        typer.echo(f"Run error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=2) from None

    if json_output:
        typer.echo(StoredRun(execution=execution, artifacts=[artifact]).model_dump_json(indent=2))
    else:
        table = Table(title=f"Validation run: {execution.run.overall_status}")
        table.add_column("Status")
        table.add_column("Test ID")
        table.add_column("Duration", justify="right")
        table.add_column("Reason")
        for result in execution.run.test_results:
            style = {
                ResultStatus.PASS: "green",
                ResultStatus.FAIL: "red",
                ResultStatus.WARN: "yellow",
                ResultStatus.SKIP: "cyan",
                ResultStatus.ERROR: "red bold",
            }[result.status]
            table.add_row(
                f"[{style}]{result.status}[/{style}]",
                result.test_id,
                f"{result.duration_seconds:.3f}s",
                result.failure_reason or "",
            )
        console = Console()
        console.print(table)
        console.print(f"Run ID: {execution.run.run_id}")
        console.print(f"Artifact: {runtime_directory.resolve() / artifact.relative_path}")

    if execution.run.overall_status is ResultStatus.ERROR:
        raise typer.Exit(code=2)
    if execution.run.overall_status is ResultStatus.FAIL:
        raise typer.Exit(code=1)


@runs_app.command("list")
def runs_list_command(
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit run summaries as JSON.")
    ] = False,
    limit: Annotated[int, typer.Option("--limit", min=1, max=1000)] = 50,
    runtime_directory: Annotated[
        Path, typer.Option("--runtime-dir", help="Runtime data directory.")
    ] = Path(".platval"),
) -> None:
    """List persisted runs newest first."""
    try:
        summaries = SQLiteRepository(runtime_directory.resolve() / "platval.db").list_runs(
            limit=limit
        )
    except (OSError, PersistenceError, ValueError) as exc:
        typer.echo(f"Repository error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=2) from None
    if json_output:
        typer.echo(json.dumps([summary.model_dump(mode="json") for summary in summaries], indent=2))
        return
    table = Table(title="Persisted validation runs")
    table.add_column("Run ID")
    table.add_column("Plan")
    table.add_column("Started")
    table.add_column("Status")
    for summary in summaries:
        table.add_row(
            summary.run_id,
            summary.plan_name,
            summary.started_at.isoformat(),
            summary.overall_status.value,
        )
    Console().print(table)


@runs_app.command("show")
def runs_show_command(
    run_id: Annotated[str, typer.Argument(help="Persisted run UUID.")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit the stored run and artifact metadata as JSON.")
    ] = False,
    runtime_directory: Annotated[
        Path, typer.Option("--runtime-dir", help="Runtime data directory.")
    ] = Path(".platval"),
) -> None:
    """Inspect a persisted run."""
    try:
        stored = load_stored_run(run_id, runtime_directory=runtime_directory)
    except (OSError, PersistenceError) as exc:
        typer.echo(f"Repository error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=2) from None
    if json_output:
        typer.echo(stored.model_dump_json(indent=2))
        return
    table = Table(title=f"Run {run_id}")
    table.add_column("Status")
    table.add_column("Test ID")
    table.add_column("Duration", justify="right")
    table.add_column("Reason")
    for result in stored.execution.run.test_results:
        table.add_row(
            result.status.value,
            result.test_id,
            f"{result.duration_seconds:.3f}s",
            result.failure_reason or "",
        )
    console = Console()
    console.print(table)
    for artifact in stored.artifacts:
        console.print(f"Artifact: {artifact.relative_path} ({artifact.sha256})")


@runs_app.command("delete")
def runs_delete_command(
    run_id: Annotated[str, typer.Argument(help="Persisted run UUID.")],
    yes: Annotated[
        bool, typer.Option("--yes", help="Confirm deletion without an interactive prompt.")
    ] = False,
    runtime_directory: Annotated[
        Path, typer.Option("--runtime-dir", help="Runtime data directory.")
    ] = Path(".platval"),
) -> None:
    """Delete database evidence and move artifacts to recoverable local trash."""
    if not yes and not typer.confirm(f"Delete run {run_id}? Artifacts will be moved to trash"):
        typer.echo("Deletion cancelled.")
        raise typer.Exit
    try:
        archived = delete_run_recoverably(run_id, runtime_directory=runtime_directory)
    except (ArtifactError, BaselineSourceError, RunNotFoundError, OSError) as exc:
        typer.echo(f"Delete error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=2) from None
    if archived is None:
        typer.echo("Run deleted; no artifact directory was present.")
    else:
        typer.echo(f"Run deleted; artifacts moved to {archived}")


if __name__ == "__main__":
    app()
