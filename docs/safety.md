# Workload safety

The toolkit performs bounded functional validation. It is not an unrestricted stress test, overclocking tool, storage benchmark, or hardware-certification system.

## Enforced boundaries

The active `SafetyPolicy` limits worker count to no more than detected logical processors, main memory allocation to a conservative fraction of currently available memory, temporary files to 256 MiB, and individual workload timeouts to five minutes by default. Plans may request smaller limits but cannot exceed the active policy.

Default memory allocation is the least of 256 MiB, 10% of currently available memory, and the policy limit. The storage workload defaults to 64 MiB and preserves at least 64 MiB of free space in addition to the requested file. It never accesses a raw disk.

CPU work is divided into finite hash operations. Floating-point work has a finite iteration count. Every loop checks a monotonic deadline and a thread-safe cancellation token between bounded chunks. `platval run` connects `Ctrl+C` to the cancellation and cleanup path; library callers may cancel the supplied token directly.

## Temporary storage

Storage validation accepts an existing root directory, creates a uniquely named owned child directory, writes only `round-trip.bin` inside it, flushes the file, verifies its checksum, and removes the owned directory after success or failure. Tests exercise cancellation during the write and verify that no child remains.

The result is a local functional sample. Repeated writes cause storage wear, so plan sizes and repetitions should remain conservative. Throughput values must not be presented as universal device rankings.

## Temperature limitations

No trustworthy temperature source is currently available on the development machine. Missing temperature is reported as unavailable, never zero. Without a trusted sensor, the toolkit cannot claim that a thermal threshold was checked; it relies on conservative resource and duration limits instead. Optional sensor support must never automatically download or start monitoring software.

## Interpretation

Workloads verify application-visible computation, memory patterns, and filesystem round trips. A failure justifies further diagnostics but does not by itself prove that a processor, memory module, or storage device is defective. Timing variation can be caused by scheduling, power management, background activity, or thermal conditions and should initially produce a warning.

The toolkit does not access model-specific registers, raw disks, firmware settings, voltage, frequency controls, power limits, product identifiers, or operating-system security settings. Normal operation does not require administrator privileges.

## Fault injection

Fault injection is disabled unless a plan explicitly selects a supported mode or the user invokes `platval demo failure`. The checksum demonstration changes only an in-memory expected digest for one small bounded workload. It does not corrupt files, alter the actual computation, change hardware state, or weaken normal validation plans. Injected results are labelled synthetic throughout persistence and reporting.
