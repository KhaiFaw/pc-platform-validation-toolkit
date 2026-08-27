# Continuous integration

GitHub Actions runs the portable suite on current GitHub-hosted Windows and Ubuntu images with Python 3.12. Each matrix job checks formatting, lint, strict typing, and coverage-gated tests; configures and builds the C++20 probe; and runs the native decoder tests. A small opt-in synthetic failure report is generated on both systems and uploaded from Linux as inspectable workflow evidence.

The workflow grants only `contents: read` and uses no secrets, publishing, deployment, administrator access, or real stress workloads. Dependency caching is limited to pip packages.

External actions are pinned to full release commit hashes with adjacent version comments. This makes workflow execution reproducible while leaving the human-readable release intent visible. The pins should be reviewed deliberately when updating GitHub-hosted runner compatibility.

Tests marked `hardware` or `extended` are excluded. Hosted-runner platform identity, optional sensors, virtualization, scheduler behavior, and performance are not representative of a user's machine; treating those observations as validation evidence would be misleading. Portable inventory behavior, capability degradation, workload correctness, persistence, reports, baseline rules, and fault injection remain covered.
