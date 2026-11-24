# TeamX Phase 2 Report — implementation and validation status

## Changes from Phase 1

Added a shared inventory/config generator, backup DNS with identical project records, explicit 30-second TTL, primary/standby TLS edges, passive backend failure detection and bounded retries, a dedicated backend PF anchor, layered diagnostics, and deployment/rollback procedures. Phase 1 artifacts remain unchanged. Historical DNS and nginx files disagree with the README IP inventory; Phase 2 uses that inventory only as a starting value requiring on-site verification.

## Results

| Extension | Prepared | Live three-Mac result |
|---|---|---|
| A backup DNS | Both resolver configs and procedure | Pending |
| B TTL | TTL configs and timed cache procedure | Pending |
| C isolation | PF anchor and rollback procedure | Pending |
| D backend HA | Retry config and recovery procedure | Pending |
| E edge migration | Standby config and dual-resolver cutover | Pending |
| F troubleshooting | Diagnostic evidence collector | Faculty evaluation pending |

Local verification is recorded in validation.txt. It does not prove network deployment. No teammate machine was accessed and no screenshots or packet evidence were fabricated.

## Resilience findings and limits

Backends share Laptop 3, so process-level failover does not survive loss of that host. Primary edge is still a single point of failure until manual DNS migration. Backup DNS shares Laptop 2 with the primary edge. Co-locating standby with backends needs an explicit local exception during migration; strict isolation is demonstrated separately. macOS resolver cache behavior must be measured on real clients.

## Troubleshooting findings

Configuration review discovered inconsistent Phase 1 IP addresses. Other runtime findings, faculty fault, diagnosis, fix and recovery timings must be added from actual tests. For each extension record before/after outputs, packet IDs, timestamp, machine and rollback completion.

## Learning summary

See README.md for one learning note per extension and the complete demonstration procedure. Complete this report with observed results before submission; this draft is not a completed live-evidence report.
