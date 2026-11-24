# Phase 2: Harden, Recover, and Troubleshoot

This extends the existing TeamX three-Mac Phase 1 system. Generated configurations and procedures are prepared; multi-Mac demonstrations are **not yet performed**. Never present expected output as an observation. Phase 1 files are preserved, including their inconsistent historical IP examples.

## Inventory and architecture

| Machine | Historical IP (verify before use) | Phase 2 role |
|---|---|---|
| Laptop 1 | 10.212.31.217 | Primary DNS; independent test client |
| Laptop 2 | 10.212.31.195 | Primary edge, backup DNS |
| Laptop 3 | 10.212.31.163 | Backend A:3001, B:3002; temporary standby edge |

Client → primary/backup DNS → primary or standby edge:8443 → backend A/B. Both backends remain on Laptop 3, consistent with Phase 1. One host failure therefore removes both backends. Backup DNS on Laptop 2 shares the primary edge failure domain. Port 8443 is explicitly allowed by the assignment; use it consistently in URLs and captures.

Verify IPs, prefix, gateway, interface and MAC with `ifconfig`, `route -n get default`, `networksetup -listallhardwareports`; update inventory.json. Run `python3 phase2/generate.py`. Generated files are deployment inputs, not evidence. Never silently apply last term's addresses.

## Prerequisites and launch

Install Python 3, dnsmasq, nginx, OpenSSL and Wireshark using the Macs' normal package setup. Save original service configs and resolver settings first. Avoid conflicting existing listeners. Use separate runtime directories for primary/standby nginx containing `logs/` and `certs/`. Preserve the Phase 1 CA and certificate if valid for BOTH app.teamX.test and api.teamX.test. Otherwise issue a new SAN certificate using your local CA; keep all private keys out of Git. Copy only the edge leaf key/certificate to each edge, and distribute the public CA certificate to clients. Never distribute the CA private key.

Run `nginx -t -p /absolute/runtime/ -c /absolute/path/nginx-primary.conf` before launching with the same arguments and without `-t`. On standby use nginx-standby.conf and a separate runtime. Relative certificate paths resolve under the nginx prefix. Validate HTTPS with `curl --cacert /path/ca.crt https://app.teamX.test:8443/api/status`; use the system trust store for the browser demonstration. No `-k`.

On Laptop 3, from repository root, launch in two terminals:

```sh
BACKEND=A PORT=3001 python3 backend/backend.py
BACKEND=B PORT=3002 python3 backend/backend.py
```

## A. Backup DNS

Run dnsmasq-primary.conf on Laptop 1 and dnsmasq-backup.conf on Laptop 2, using absolute paths with `sudo dnsmasq --keep-in-foreground --conf-file=/path/to/config`. Stop conflicting dnsmasq instances first. Set both DNS server addresses on at least two client Macs via Network settings. Save the previous resolver list for rollback. Verify both explicitly with `dig @IP app.teamX.test` and capture `scutil --dns`.

Start packet capture, stop only primary dnsmasq (Ctrl-C in its terminal), flush client cache, then resolve through the normal client resolver using `dscacheutil -q host -a name app.teamX.test` and perform HTTPS by name. Capture traffic to the backup IP:53. Resolver ordering/timing varies on macOS; listing two addresses does not guarantee strict primary-first behavior. A successful direct `dig @backup` alone does not prove automatic client failover. Restart primary and repeat. Record timings and observed queries.

## B. TTL and controlled change

Records have explicit TTL 30. Verify TTL directly with dig against both resolvers. `dig` is a direct query tool and does not demonstrate macOS cache reuse. Keep an HTTPS service working at both edge IPs before migration. Resolve through the system resolver, then change BOTH resolver configs to standby using `python3 phase2/generate.py --target standby`. Restart both dnsmasq processes: host-record config changes need restart, not merely SIGHUP. Record time before the change, remaining TTL, and timestamps of client lookups. Poll the system resolver plus fresh HTTPS connections and X-Edge. Cache retention can vary by client, so record what actually happens rather than claiming an exact 30-second guarantee.

Flush manually on a client using `sudo dscacheutil -flushcache` and `sudo killall -HUP mDNSResponder`; close browser connection pools as needed. Repeat the system lookup and HTTPS request to observe change. Do not flush during the unflushed TTL experiment. Restore primary records on BOTH resolvers and verify. DNS cutover does not move existing TCP connections or application connection pools.

## C. Backend isolation with rollback

Use Laptop 1 as the independent client: localhost requests on Laptop 3 do not prove LAN isolation. Back up `/etc/pf.conf`, current `sudo pfctl -sr`, enable status (`sudo pfctl -s info`) and any existing cn_phase2 anchor rules. Have local console access. Inspect current rules; do not replace the macOS ruleset with the small generated anchor file.

Add `anchor "cn_phase2" quick all` to the main ruleset BEFORE any broad pass quick rule (the anchor invocation itself must be quick so later main-ruleset rules cannot override a matching decision), preserving Apple anchors and all other rules. Syntax-check the complete candidate via `sudo pfctl -nf /path/candidate.conf`. Load the complete reviewed candidate, then load only this anchor using `sudo pfctl -a cn_phase2 -f /path/backend.pf`. Enable PF only if necessary, using `pfctl -E` and recording its token. Record active rules. Existing states may permit old connections: test new connections and remove only matching test states if needed; never flush all host states.

From Laptop 2 both direct backend curls must succeed. From Laptop 1 `nc -vz -G 3 10.212.31.163 3001` and port 3002 must fail; HTTPS through edge must succeed. Save outputs and packet capture. If any broad rule bypasses this anchor, fix ordering before claiming isolation.

Rollback: clear the dedicated anchor (`sudo pfctl -a cn_phase2 -F rules`), restore its earlier rules if any, restore the saved complete pf.conf and reload it after syntax validation. Release only your enable reference using `sudo pfctl -X TOKEN` if you acquired one. Do not globally disable PF or overwrite unrelated anchors.

## D. Backend HA

Nginx uses passive failure detection, not active health probes. A failed GET is retried against the other backend, one failed attempt marks a backend unavailable for 5 seconds. Start with 20 sequential fresh curl requests to /api/status; save status, X-Backend, X-Edge and access logs. Stop Backend A with Ctrl-C in its OWN terminal. Repeat requests: require successful responses from B. Restart A; wait at least 5 seconds and repeat until A/B both appear. All-failed upstreams should return 502/504; collect actual status. Keep edge error/access logs showing retry destinations. Do not expect alternating identities across concurrent clients or failed/recovering upstream states.

The single primary nginx edge remains a single point of failure until the MANUAL DNS migration below. Removing it needs a second edge plus a real automated health/cutover mechanism; DNS TTL and long-lived connections still limit recovery. Both co-located backends share a host failure domain.

## E. Standby edge migration

Start standby nginx on Laptop 3 with the same SAN-valid leaf certificate and backend pool; X-Edge differs intentionally for observation. First test it using curl --resolve app.teamX.test:8443:10.212.31.163 with --cacert. That preflight bypasses DNS and is NOT cutover evidence.

Because standby is co-located with backends, its local traffic cannot satisfy a literal edge-IP-only policy. Demonstrate C first, then document a temporary local standby exception during E (or restore original PF rules for the migration exercise). Prefer a fourth Mac as standby with an explicit second edge allow rule when available; do not claim simultaneous strict original-edge-only isolation and local standby access. Keep the independent Laptop 1 client.

Run the timed TTL procedure in B with both edges alive. Show old cached client → X-Edge primary and fresh lookup → X-Edge standby where actually observed. Update BOTH DNS servers, capture answers, timestamps and requests. Stop the old edge only after clients have migrated. Test normal resolver HTTPS, not --resolve. Restore both DNS records and original services after the demonstration. This is controlled manual migration, not automatic edge HA.

## F. Layered troubleshooting

Run `python3 phase2/diagnose.py --ca /path/ca.crt --out phase2/evidence/run-TIMESTAMP`. It records real command output, timestamps and exit codes. Diagnose in order:

| Layer | Check | Interpretation |
|---|---|---|
| DNS | direct dig both resolvers; system resolver | timeout/NXDOMAIN/wrong IP; compare system cache |
| TCP | nc to resolved edge:8443 | wrong port, listener, routing or PF |
| TLS | curl -v with CA and hostname | trust, expiry, SAN, protocol; no bypass |
| Application | status, X-Backend, nginx upstream logs | 502/504 versus backend 404; healthy upstream |

Faculty fault/results must be filled during the actual evaluation. Do not describe a rehearsal as faculty-injected. Repair one cause at a time and repeat checks in order.

## Evidence and final demonstration

Create evidence subfolders A-backup-dns, B-ttl, C-isolation, D-backend-ha, E-cutover, F-troubleshooting. Each run needs machine/role, verified addresses, timestamp, exact commands, actual output, outcome and rollback confirmation. Capture using Wireshark on the active interface, including `port 53 or tcp port 8443 or tcp port 3001 or tcp port 3002`. Store genuine pcapng and screenshots. In TLS 1.3 the certificate is normally encrypted after ServerHello; do not claim it is visible in an undecrypted capture.

Final sequence: topology/inventory → LAN reachability → DNS → trusted HTTPS → A/B load distribution → saved DNS/TCP/TLS capture → caching/304 → backend failure/recovery → backup DNS/TTL/cutover and isolation → faculty fault diagnosis → individual viva. Check assignment Section 8 for the full eleven steps.

## Learning notes

A: DNS redundancy protects name service, independently from application health. B: TTL limits cache freshness but does not relocate established connections. C: Backend network policy enforces edge access and must be verified from a separate host. D: Passive retries improve backend availability without protecting against shared host or edge failure. E: DNS cutover requires consistent records and certificate validity on both edges. F: Layer-by-layer observations distinguish lookup, transport, trust and application faults.
