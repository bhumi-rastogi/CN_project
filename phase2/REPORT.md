# TeamX Phase 2 Report — implementation and genuine local results

## Scope and architecture

On 24 November 2026, actual dnsmasq, Nginx and Python processes were exercised on **one physical Mac**. Separate service roles were not separate Macs. Test ports: DNS 15353/15354, client forwarders 15355/15356, backend A/B 13001/13002 and HTTPS 18443. Primary edge bound loopback; standby bound this Mac's actual LAN address, 10.3.0.246. High test ports avoid interference with existing services. Deployment inventory retains the historical three-Mac addresses and must be verified on-site.

The generated deployment configuration covers backup DNS, explicit 30-second TTL, passive backend health/retry behavior, a dedicated PF anchor, standby edge and layered diagnostics. Original Phase 1 configuration and proof files remain unchanged. They contain inconsistent historical IP examples; the shared inventory resolves future configuration drift.

## Observed results

Successful evidence run: [run 20261124T123305Z](local-evidence/20261124T123305Z/events.json). Read the [demonstration viewer](demonstrations.html) and [packet capture](local-evidence/20261124T123305Z/single-mac.pcapng).

| Extension | Actual observation | Assignment completion limit |
|---|---|---|
| A backup DNS | Forwarding client resolved through backup after primary stopped; successful query included client retransmission | Native macOS resolver failover on separate clients not tested |
| B TTL | Cached old answer remained after real A-record change, then new answer appeared after expiry; explicit forwarder cache flush changed answer immediately | Tested dnsmasq cache, not mDNSResponder/browser cache on other Macs |
| C isolation | Generated PF syntax validated successfully | PF not activated; no independent client allow/block proof or firewall rollback demonstration |
| D backend HA | Eight of eight requests returned 200 from B while A was stopped; A/B identities both returned after A restarted | Real Nginx process-level behavior demonstrated locally; shared-host failure resilience not claimed |
| E cutover | Old cached DNS answer reached X-Edge primary; fresh answer reached X-Edge standby with a valid hostname-checked certificate | Two real listeners on one Mac; curl used DNS-selected --resolve, not native-client DNS migration |
| F troubleshooting | DNS timeout (exit 9), wrong TCP port (exit 7), untrusted CA (exit 60), upstream 502 and subsequent 200 recovery distinguished | Automated rehearsal; faculty-injected evaluation still pending |

HTTP caching also produced a genuine 304 Not Modified response. Original deployment dnsmasq, nginx and PF configurations passed syntax validation. Actual traffic was captured in pcapng and DNS/TCP/TLS field exports include packet numbers for review. TLS 1.3 certificate messages are not claimed visible without decryption.

## Troubleshooting findings

An initial one-attempt DNS query timed out before the forwarding client retried a second resolver. Using bounded client retransmissions demonstrated backup service, illustrating that DNS redundancy depends on client retry behavior. An early full-backend-recovery test returned a transient 502 at the nominal five-second boundary; the final runner polls recovery with a bounded window and retains every observed response. Deployment validation also caught relative TLS certificate paths resolving from the config directory; the generator now emits explicit absolute paths and accepts --cert-dir. These earlier runs remain in local-evidence for transparency; they are not successful complete runs.

## Learning summary by extension

A: DNS redundancy protects name service independently of application health, but resolver selection and retry behavior must be measured on the actual clients.

B: A 30-second TTL limits a caching resolver's retained answer; an explicit flush affects that cache immediately. Existing connections and application pools have their own lifetimes.

C: Service isolation must be verified from an independent client. Syntax checks alone cannot establish enforcement, ordering, state handling or rollback success.

D: Passive failure detection and retries preserve service when one backend process stops. Both backend processes share a host, and the primary edge remains a separate single point of failure.

E: Both DNS servers must agree during cutover, both edges need valid certificates, and cached clients may continue to reach the old edge. This exercise demonstrated manual cutover, not automatic edge HA.

F: DNS, TCP, TLS and upstream failures produce different observations. Layered diagnosis isolates the cause; the real faculty fault and individual viva must occur during evaluation.

## Cleanup and remaining requirements

The runner terminated every service it started. No system DNS settings or PF rules were changed. Test CA keys remain in ignored local-runtime directories and are not committed. Evidence files have SHA-256 hashes.

To satisfy the PDF in full, deploy and verify the shared inventory on the actual team LAN; configure at least two macOS clients with both DNS addresses; measure their native cache/failover/cutover; activate backend PF rules with administrator access and collect independent-client isolation plus rollback proof; complete the faculty-injected challenge, live final sequence and individual viva. **This report does not claim those requirements are complete.**
