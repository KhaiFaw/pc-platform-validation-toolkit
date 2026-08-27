"""Command-line entry point for inspection and validation workflows."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from platval.baselines import compare_run, create_baseline, get_baseline, list_baselines
from platval.constants import TOOL_VERSION
from platval.demo import failure_demo_plan
from platval.doctor import DoctorStatus, run_doctor
from platval.inventory import collect_platform_inventory, locate_native_probe
from platval.models.status import ResultStatus
from platval.persistence import (
    ArtifactError,
    BaselineExistsError,
    BaselineNotFoundError,
    BaselineSourceError,
    PersistenceError,
    RunNotFoundError,
    SQLiteRepository,
    StoredRun,
    delete_run_recoverably,
    load_stored_run,
    persist_execution,
)
from platval.reporting import ReportFormat, generate_report
from platval.runner import PlanLoadError, load_test_plan, run_validation_plan
from platval.workloads import CancellationToken, WorkloadCancelled

app = typer.Typer(
    name="platval",
    help="Run bounded, requirements-based PC platform validation.",
    no_args_is_help=True,
    add_completion=False,
)
runs_app = typer.Typer(help="List, inspect, or remove persisted validation runs.")
baseline_app = typer.Typer(help="Create and inspect immutable known-good baselines.")
demo_app = typer.Typer(help="Run safe, explicitly synthetic demonstrations.")
app.add_typer(runs_app, name="runs")
app.add_typer(baseline_app, name="baseline")
app.add_typer(demo_app, name="demo")


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
    """Execute and persist a bounded validation plan."""
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


@app.command("report")
def report_command(
    run_id: Annotated[str, typer.Argument(help="Persisted run UUID.")],
    report_format: Annotated[
        ReportFormat,
        typer.Option("--format", help="Report format: html, markdown, or json."),
    ] = ReportFormat.HTML,
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit generated artifact metadata as JSON.")
    ] = False,
    runtime_directory: Annotated[
        Path, typer.Option("--runtime-dir", help="Runtime data directory.")
    ] = Path(".platval"),
) -> None:
    """Create a static report from one persisted run."""
    try:
        generated = generate_report(
            run_id,
            runtime_directory=runtime_directory,
            report_format=report_format,
        )
    except (ArtifactError, PersistenceError, OSError, ValueError) as exc:
        typer.echo(f"Report error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=2) from None
    if json_output:
        typer.echo(generated.model_dump_json(indent=2))
    else:
        action = "Using" if generated.reused else "Created"
        typer.echo(f"{action} {generated.format.value} report: {generated.path}")


@baseline_app.command("create")
def baseline_create_command(
    from_run: Annotated[str, typer.Option("--from-run", help="Known-good source run UUID.")],
    name: Annotated[str, typer.Option("--name", help="Immutable baseline name.")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit baseline metadata as JSON.")
    ] = False,
    runtime_directory: Annotated[
        Path, typer.Option("--runtime-dir", help="Runtime data directory.")
    ] = Path(".platval"),
) -> None:
    """Create an immutable named baseline from a successful stored run."""
    try:
        baseline = create_baseline(name, from_run, runtime_directory=runtime_directory)
    except (BaselineExistsError, PersistenceError, OSError, ValueError) as exc:
        typer.echo(f"Baseline error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=2) from None
    if json_output:
        typer.echo(baseline.model_dump_json(indent=2))
    else:
        typer.echo(f"Created baseline {baseline.name!r} from run {baseline.source_run_id}")


@baseline_app.command("list")
def baseline_list_command(
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit baseline metadata as JSON.")
    ] = False,
    runtime_directory: Annotated[
        Path, typer.Option("--runtime-dir", help="Runtime data directory.")
    ] = Path(".platval"),
) -> None:
    """List immutable baselines by name."""
    try:
        baselines = list_baselines(runtime_directory=runtime_directory)
    except (PersistenceError, OSError) as exc:
        typer.echo(f"Baseline error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=2) from None
    if json_output:
        typer.echo(json.dumps([item.model_dump(mode="json") for item in baselines], indent=2))
        return
    table = Table(title="Known-good baselines")
    table.add_column("Name")
    table.add_column("Source run")
    table.add_column("Plan")
    table.add_column("Created")
    for baseline in baselines:
        table.add_row(
            baseline.name,
            baseline.source_run_id,
            baseline.plan_name,
            baseline.created_at.isoformat(),
        )
    Console().print(table)


@baseline_app.command("show")
def baseline_show_command(
    name: Annotated[str, typer.Argument(help="Baseline name.")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit baseline metadata as JSON.")
    ] = False,
    runtime_directory: Annotated[
        Path, typer.Option("--runtime-dir", help="Runtime data directory.")
    ] = Path(".platval"),
) -> None:
    """Show one baseline and its compatibility identity."""
    try:
        baseline = get_baseline(name, runtime_directory=runtime_directory)
    except (BaselineNotFoundError, PersistenceError, OSError) as exc:
        typer.echo(f"Baseline error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=2) from None
    if json_output:
        typer.echo(baseline.model_dump_json(indent=2))
    else:
        table = Table(title=f"Baseline {baseline.name}", show_header=False)
        table.add_column("Field", style="bold")
        table.add_column("Value")
        table.add_row("Source run", baseline.source_run_id)
        table.add_row("Plan", baseline.plan_name)
        table.add_row("Plan hash", baseline.plan_hash)
        table.add_row("Platform fingerprint", baseline.platform_fingerprint)
        table.add_row("Created", baseline.created_at.isoformat())
        Console().print(table)


@app.command("compare")
def compare_command(
    baseline_name: Annotated[str, typer.Option("--baseline", help="Baseline name.")],
    run_id: Annotated[str, typer.Option("--run", help="Run UUID to compare.")],
    warning_threshold: Annotated[
        float, typer.Option("--warn-percent", min=0, help="Warning regression threshold.")
    ] = 10.0,
    failure_threshold: Annotated[
        float, typer.Option("--fail-percent", min=0, help="Failure regression threshold.")
    ] = 20.0,
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit the comparison as JSON.")
    ] = False,
    runtime_directory: Annotated[
        Path, typer.Option("--runtime-dir", help="Runtime data directory.")
    ] = Path(".platval"),
) -> None:
    """Compare registered metrics against a compatible known-good run."""
    try:
        comparison = compare_run(
            baseline_name,
            run_id,
            runtime_directory=runtime_directory,
            warning_threshold_percent=warning_threshold,
            failure_threshold_percent=failure_threshold,
        )
    except (BaselineNotFoundError, PersistenceError, OSError, ValueError) as exc:
        typer.echo(f"Comparison error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=2) from None
    if json_output:
        typer.echo(comparison.model_dump_json(indent=2))
    else:
        table = Table(title=f"Comparison: {comparison.overall_status.value}")
        table.add_column("Outcome")
        table.add_column("Test")
        table.add_column("Metric")
        table.add_column("Baseline", justify="right")
        table.add_column("Current", justify="right")
        table.add_column("Difference", justify="right")
        for item in comparison.comparisons:
            difference = (
                "UNAVAILABLE"
                if item.percent_difference is None
                else f"{item.percent_difference:+.2f}%"
            )
            table.add_row(
                item.outcome.value,
                item.test_id,
                item.metric,
                f"{item.baseline_value:.8g}",
                f"{item.current_value:.8g}",
                difference,
            )
        console = Console()
        console.print(table)
        for warning in comparison.warnings:
            console.print(f"[yellow]WARN[/yellow] {warning}")
        console.print(comparison.interpretation)
    if comparison.overall_status is ResultStatus.ERROR:
        raise typer.Exit(code=2)
    if comparison.overall_status is ResultStatus.FAIL:
        raise typer.Exit(code=1)


@demo_app.command("failure")
def demo_failure_command(
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit the labelled synthetic run as JSON.")
    ] = False,
    runtime_directory: Annotated[
        Path, typer.Option("--runtime-dir", help="Runtime data directory.")
    ] = Path(".platval/demo"),
) -> None:
    """Produce one safe deterministic injected failure and its reports."""
    try:
        execution = run_validation_plan(
            failure_demo_plan(),
            runtime_directory=runtime_directory,
            token=CancellationToken(),
        )
        canonical = persist_execution(execution, runtime_directory=runtime_directory)
        html_report = generate_report(
            execution.run.run_id,
            runtime_directory=runtime_directory,
            report_format=ReportFormat.HTML,
        )
        markdown_report = generate_report(
            execution.run.run_id,
            runtime_directory=runtime_directory,
            report_format=ReportFormat.MARKDOWN,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        typer.echo(f"Demo error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=2) from None
    stored = StoredRun(
        execution=execution,
        artifacts=[canonical, html_report.artifact, markdown_report.artifact],
    )
    if json_output:
        typer.echo(stored.model_dump_json(indent=2))
    else:
        typer.echo("Synthetic failure demonstration completed as intended: FAIL")
        typer.echo(f"Run ID: {execution.run.run_id}")
        typer.echo(f"HTML report: {html_report.path}")
        typer.echo(f"Markdown report: {markdown_report.path}")


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
