# Results guide

## Reading status

- `PASS` means the implemented workload completed correctly and all explicit requirements were met.
- `FAIL` means correctness verification or at least one explicit requirement failed.
- `WARN` records a usable result with a material limitation or soft concern.
- `SKIP` means the test was intentionally not evaluated, commonly because an optional capability was unavailable.
- `ERROR` means execution or requirement configuration prevented a valid result.

The overall status uses the precedence `ERROR`, `FAIL`, `WARN`, `PASS`, `SKIP`. A run can therefore be useful while reporting expected WARN or SKIP degradation.

## Evidence labels

`measured` values are direct observations from the workload, operating system, native probe, or telemetry collector. `configured` values are plan requirements and thresholds. `derived` values are calculated from measured evidence, such as throughput, error, variability, or telemetry summaries. `unavailable` means no trustworthy reading existed; it never means numeric zero. `simulated` identifies deliberately injected evidence and must not be interpreted as a hardware observation.

## Timing and variance

Short workloads are useful for functional checks but are sensitive to timer resolution, scheduling, background activity, cache state, power policy, and virtualization. Very small measured durations can produce extreme throughput values and should not be treated as benchmarks. Compare repeated, similarly configured runs and prefer robust summaries such as medians and median absolute deviation.

## Telemetry gaps

Sampling is independent and bounded. A very short test may contain only one sample, so its chart is a point rather than a trend. Sensor support varies by operating system and hardware; unavailable temperature or frequency data is reported explicitly. Missing data does not convert a functional PASS into proof that thermal or power behavior was healthy.

## Diagnostic limits

These results are local software observations, not vendor endorsement or hardware certification. A failure supports investigation but does not alone identify a defective component.

## Regression thresholds

Baseline comparison is limited to registered numeric metrics whose direction is known. The default warning threshold is 10% adverse change and the failure threshold is 20%; changes within the warning band are classified unchanged, while similarly sized favorable changes are labelled improved. Both values are configurable per invocation and are recorded in the comparison evidence.

Numeric conclusions are withheld when platform fingerprints or plan hashes differ. A zero baseline cannot yield a meaningful percentage. Functional FAIL and ERROR take priority. Even a compatible threshold crossing is correlation only: repeat the plan and investigate background load, power policy, caching, scheduler activity, temperature evidence, and workload variability before drawing a conclusion.
