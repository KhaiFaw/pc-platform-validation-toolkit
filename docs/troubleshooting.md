# Troubleshooting

## Python or installation errors

Confirm `python --version` reports 3.12 or newer and that the virtual environment is active. Recreate `.venv` if it was built with another interpreter, then run `python -m pip install -e ".[dev]"`. Use `python -m platval.cli --help` to distinguish a PATH issue from a package issue.

## Native probe unavailable

`platval doctor` reports a warning when the optional executable is missing. The Python toolkit remains usable, but CPU feature checks may skip. Install CMake and a supported C++20 compiler, run `scripts\build_native.ps1`, and pass the resulting executable with `--native-probe`. If CMake configuration fails, verify the compiler is available in the same shell.

## Temperature or other telemetry unavailable

Sensor exposure varies by operating system, firmware, driver, virtualization layer, and privileges. Unavailable values are expected capability evidence and are never converted to zero. Do not install or start third-party monitoring software solely to make the warning disappear. Interpret results with the documented limitation.

## A report already exists

Reports are immutable evidence. Repeating the same format for the same run intentionally refuses to overwrite the file. Use the existing registered artifact, generate another format, or create a new validation run after changing report code.

## Baseline creation or comparison fails

Baseline names use lowercase letters, digits, dots, underscores, and hyphens. Existing names cannot be replaced. A FAIL or ERROR run cannot become known-good. Comparison requires the baseline source run to remain stored; deletion is blocked while referenced.

Different platform fingerprints or plan hashes cause numeric conclusions to be withheld. This is a safety decision, not a database error. Create a separate baseline for the new platform or plan instead of weakening compatibility checks.

## Unexpected performance change

Repeat the same plan under comparable power policy, background load, storage state, and temperature conditions. Inspect absolute values, units, variability, and unavailable telemetry before treating a threshold crossing as actionable. Regression status indicates correlation, not cause.

## Interrupted run or leftover temporary data

The runner uses cooperative cancellation and owned temporary directories. If the process was terminated externally rather than through `Ctrl+C`, inspect only `.platval/tmp` for an abandoned owned directory. Do not delete broad system temporary locations. Persisted runs can be removed with `platval runs delete <run-id>`, which requires confirmation and moves artifacts into local recoverable trash.

## Clean verification fails

Run `scripts\verify.ps1 -UseExistingEnvironment` after the documented development setup. Without `-UseExistingEnvironment`, provide a Python 3.12 executable using `-PythonPath`. A pre-existing `.tmp\verification` directory is treated as a prior interrupted verification and is not overwritten; inspect and remove that exact directory before retrying.
