# ADR-0003: Static offline reports

## Status

Accepted

## Context

Validation evidence must remain reviewable after a run without requiring a service, network connection, JavaScript runtime, or third-party asset host. Reports also need to preserve the distinction between observations, configured thresholds, derived statistics, unavailable capabilities, and synthetic evidence.

## Decision

Generate Markdown and one self-contained HTML file from a typed report view model built only from persisted canonical evidence. Embed CSS and accessible SVG charts directly in the HTML. Do not include scripts, external fonts, CDNs, or remote resources. Treat reports as immutable derived artifacts: create them atomically, calculate SHA-256 metadata, register them in SQLite, and refuse overwrite. Return the original canonical artifact for JSON requests.

## Consequences

- Reports can be copied and opened offline in a standard browser.
- The CLI remains the only required user interface; there is no dashboard server or attack surface.
- Visualizations are deliberately small and evidence-focused rather than interactive.
- Changing report presentation for an existing run requires a new explicitly managed artifact policy instead of silently replacing evidence.
