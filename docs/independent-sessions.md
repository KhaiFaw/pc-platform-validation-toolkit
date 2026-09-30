# Independent-session capture and native validation

This workflow runs two separate bounded quick-plan processes, creates a baseline from the first UUID and compares the second. It records context without turning short timings into a performance guarantee. See the [actual paired evidence](../examples/independent-sessions/README.md).

## Native build

Install or use a portable CMake and C++20 toolchain in your own environment. Nothing in the toolkit downloads a compiler, installs monitoring software or changes hardware settings. The local 30 September build used official [CMake 4.4.3](https://github.com/Kitware/CMake/releases/tag/v4.4.3) and [LLVM/MinGW 20260922](https://github.com/mstorsjo/llvm-mingw/releases/tag/20260922) archives, verified before extraction, with no system installation.

Standard supported compiler:

```powershell
.\scripts\build_native.ps1
```

For portable LLVM/MinGW, put its `bin` and CMake's `bin` on PATH for the current shell, then explicitly choose the tools:

```powershell
.\scripts\build_native.ps1 -Generator 'MinGW Makefiles' `
    -CxxCompiler '<toolchain>\bin\x86_64-w64-mingw32-clang++.exe' `
    -MakeProgram '<toolchain>\bin\mingw32-make.exe'
```

The placeholders are paths in your environment. Do not switch generators inside an existing CMake build directory; use the generator/compiler that initialized it. MSVC multi-configuration builds normally produce `build\Release\cpuid_probe.exe`; MinGW single-configuration builds produce `build\cpuid_probe.exe`. The native runtime DLL directory must remain on the current shell PATH when Python invokes a dynamically linked binary. `build_native.ps1` always runs CTest after a successful build.

## Capture a fresh pair

Use the Python environment into which this checkout was installed with `python -m pip install -e ".[dev]"`:

```powershell
.\scripts\capture_sessions.ps1 `
    -PythonPath '.\.venv\Scripts\python.exe' `
    -NativeProbePath '.\cpp\cpuid_probe\build\cpuid_probe.exe' `
    -PauseSeconds 15 `
    -BackgroundContext 'Normal interactive desktop; applications left running; no injected load.'
```

Omit `-NativeProbePath` to intentionally exercise graceful degradation. An explicitly requested missing or invalid probe is rejected instead of silently substituted with missing-native results. The script also refuses an imported `platval` package from another checkout, records an origin boolean rather than a private path, and hashes the actual binary and source files. It refuses to finalize a comparison if those source files or the binary change during capture.

By default, generated public-review artifacts go to a new UUID directory under ignored `.tmp/session-evidence/`; canonical runs and SQLite persistence live under ignored `.platval/sessions/`. `-OutputDirectory <new-directory>` chooses an export location, which must not already exist. No prior evidence is overwritten or deleted. Review the files before publishing them; do not put personal identifiers in the free-text background context.

The script samples two seconds of system CPU load, available memory and process count before each run; records battery/AC observations only if exposed; and retains the active power plan from each run's inventory. It does not close applications, enforce idle conditions, alter power policy or claim temperature support. Distinct UUIDs prove separate executions, not separate days, reboots, controlled background activity or thermal equilibrium.

## Timing correction and legacy baselines

On the local Python 3.12 Windows environment, `time.monotonic()` uses `GetTickCount64()` with 15.625 ms resolution, while `time.perf_counter()` uses `QueryPerformanceCounter()` with 100 ns reported resolution. The original tiny quick-plan workloads sometimes recorded zero elapsed time and divided by an artificial `1e-12` denominator, yielding extreme rates and misleading comparisons.

Workload and test duration measurement now uses the high-resolution performance counter. Cooperative safety deadlines still use their existing monotonic clock. Zero or non-finite elapsed time produces an unavailable rate, not an invented duration; unmeasurable stability produces WARN, not a quantitative PASS. Regression tests model both a coarse deadline clock and an unmeasurable performance clock.

**Recapture baselines created before this correction.** The MVP version and plan hash did not change, so compatibility checks alone cannot identify older timer semantics. Historical `examples/measured` files are retained for functional/report provenance, not current timing regression interpretation. New native-enabled captures also have a different platform fingerprint because they expose more CPU identity; do not bypass compatibility checks to compare them to missing-native runs.

## Interpretation and acceptance

The comparator warns about self-comparisons and changed recorded power plans and rejects non-finite thresholds. Numeric changes still cannot identify a hardware cause. Keep any FAIL/WARN classification and investigate absolute duration, background load, caching, power policy and available sensor evidence before drawing conclusions.

The updated verifier performs a second real functional quick run instead of comparing the baseline source to itself and forwards a successfully built or explicitly supplied probe to both diagnostics and runs:

```powershell
.\scripts\verify.ps1 -UseExistingEnvironment
# Or use an already prepared environment outside the checkout:
.\scripts\verify.ps1 -UseExistingEnvironment -PythonPath '<python.exe>'
```

Python quality gates, native build/tests and functional quick-plan failures remain hard errors. A valid compatible performance comparison can return WARN or FAIL and is displayed as evidence rather than used as a flaky microbenchmark quality gate. The separate injected checksum demo still proves the labelled synthetic failure path. A trusted sensor source and longer controlled repeated sessions remain outside this short acceptance scope.
