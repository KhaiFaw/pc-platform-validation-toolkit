# Native CPUID probe contract

`cpuid_probe` is an optional C++20 subprocess. It uses compiler intrinsics only, reads supported CPUID leaves, and performs no privileged operations. Diagnostics go to standard error; JSON is the only standard-output content for `--json` and `--pretty`.

## Commands and exit codes

| Command | Behaviour |
|---|---|
| `cpuid_probe --json` | Compact schema-versioned JSON |
| `cpuid_probe --pretty` | Indented schema-versioned JSON |
| `cpuid_probe --version` | Human-readable probe version |

Exit code 0 is success, 2 is unsupported architecture, 3 is invalid arguments, and 4 is an internal failure.

## Schema version 1

The response contains probe and schema versions, compiled architecture, CPUID vendor ID, optional normalized brand string, maximum supported basic and extended leaves, selected feature flags, and deterministic-cache descriptions. Python rejects unknown fields and incompatible schema versions.

`avx_hardware` records the CPUID AVX bit. `avx_os_enabled` additionally requires OSXSAVE and XCR0 state for XMM/YMM context. `avx2_hardware` records the leaf 7 hardware bit and does not by itself assert usable AVX2 state. `vmx` and `svm` describe hardware capability bits, not whether virtualization is enabled by firmware or available to a hypervisor.

Cache sizes use CPUID deterministic-cache parameters when basic leaf 4 is available:

```text
(ways + 1) * (partitions + 1) * (line size + 1) * (sets + 1)
```

The implementation checks the maximum supported leaf before every optional query and bounds cache-subleaf enumeration.

## Feature-bit references and simplifications

The decoder follows the CPUID instruction tables in Intel's *64 and IA-32 Architectures Software Developer's Manual*, Volume 2A, and AMD's *Architecture Programmer's Manual*, Volume 3. The implemented locations are leaf 1 EDX bit 26 (SSE2); leaf 1 ECX bits 19, 20, 25, 27, 28, and 5 (SSE4.1, SSE4.2, AES, OSXSAVE, AVX, and VMX); leaf 7 subleaf 0 EBX bit 5 (AVX2); and extended leaf `0x80000001` ECX bit 2 (SVM).

The first version does not decode hybrid topology, cache sharing, firmware enablement, or hypervisor policy. It uses basic deterministic-cache leaf 4 and does not yet fall back to AMD extended deterministic-cache leaf `0x8000001D`.
