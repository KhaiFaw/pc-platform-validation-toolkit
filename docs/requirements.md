# Requirements and verification map

This is the accepted MVP requirements set. Each row identifies the evidence that supports it.

| ID | Requirement | Planned evidence |
|---|---|---|
| FR-001 | Load versioned YAML plans and reject invalid or unknown fields. | Plan model, malformed YAML, schema, field-location, and hash tests (passing) |
| FR-002 | Collect sanitized platform inventory and report capability availability. | `test_inventory.py`, `test_capabilities.py`, and inspection CLI integration tests (passing) |
| FR-003 | Execute deterministic CPU, memory, and temporary-storage checks within limits. | Workload correctness, boundary, timeout, cancellation, and cleanup tests (passing) |
| FR-004 | Assign PASS, FAIL, WARN, SKIP, or ERROR to every test. | Evaluator, aggregation, and quick-run integration tests (passing) |
| FR-005 | Persist canonical runs and produce JSON, Markdown, and self-contained HTML reports. | Repository, artifact, renderer, CLI, and browser visual checks (passing) |
| FR-006 | Create immutable named baselines and compare compatible runs. | Baseline service, repository, threshold, compatibility, CLI, and source-protection tests (passing) |
| FR-007 | Demonstrate safe deterministic failure handling through disabled-by-default software fault injection. | Failure-plan and demo/report integration tests (passing) |
| NFR-001 | Support Python 3.12+ and Windows 11 x86-64 as the primary environment. | Isolated install and end-to-end release verifier (passing) |
| NFR-002 | Continue with reduced capability when optional sensors or the native probe are unavailable. | Native-probe, capability, doctor, and inventory tests (passing) |
| NFR-003 | Keep default automated tests fast and mark hardware-dependent tests. | Pytest marker checks and CI duration |
| NFR-004 | Verify portable behavior on Windows and Ubuntu without secrets or stress workloads. | SHA-pinned GitHub Actions matrix with portable gates, native CTest, and synthetic artifacts |
| SAFE-001 | Every workload supports timeout, cancellation, and bounded resource use. | Workload timeout, cancellation, and boundary tests (passing) |
| SAFE-002 | Storage validation uses only an owned temporary directory and cleans up. | Round-trip and cancellation cleanup tests (passing) |
| SAFE-003 | The toolkit never changes voltage, frequency, power, firmware, or security settings. | Design review and command allowlist review |
| PRIV-001 | Default inventory excludes usernames, hostnames, serial numbers, MAC addresses, and product identifiers. | Serialized inventory unit and CLI integration tests (passing) |
| PRIV-002 | Platform fingerprints use only stable non-sensitive configuration fields. | Fingerprint stability/privacy unit tests (passing) |

Status aggregation uses this precedence: ERROR, FAIL, WARN, PASS, SKIP. A mixture of PASS and SKIP remains PASS because an unavailable optional capability is not itself a failure; reports still expose the skipped count and limitation.
