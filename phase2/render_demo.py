from pathlib import Path
import json,html
root=Path(__file__).resolve().parent
runs=[p.parent for p in (root/'local-evidence').glob('*/events.json') if any(e['name']=='rehearsal-complete' for e in json.loads(p.read_text()))]
run=sorted(runs)[-1]
events=json.loads((run/'events.json').read_text())
def block(name,title):
 f=run/(name+'.txt')
 return '<details><summary>'+html.escape(title)+'</summary><pre>'+html.escape(f.read_text())+'</pre></details>' if f.exists() else ''
body='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TeamX — genuine local demonstrations</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 24px;background:#101721;color:#edf2f7}h1{font-size:36px}p{line-height:1.6;color:#cbd5e1}.scope{padding:20px;background:#27354a;border-left:5px solid #f5bc53;border-radius:8px}details{margin:14px 0;padding:16px;background:#1c2838;border-radius:8px}summary{cursor:pointer;font-weight:650}pre{font:13px ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere;color:#c4edd9}a{color:#93c5fd}table{border-collapse:collapse;width:100%}td,th{text-align:left;border-bottom:1px solid #425267;padding:12px}h2{margin-top:36px}</style><h1>TeamX: Phase 2 demonstrations</h1><div class="scope"><strong>REAL SINGLE-MAC REHEARSAL</strong><p>These are actual dnsmasq, Nginx, Python backend and Wireshark results from one physical Mac. Separate processes represent service roles. This is not evidence of separate physical Macs, macOS client DNS failover, activated firewall isolation or a faculty-injected fault.</p></div>'''
body+='<p>Run: '+run.name+' · <a href="'+str(Path('local-evidence')/run.name/'single-mac.pcapng')+'">Open genuine packet capture</a> · <a href="'+str(Path('local-evidence')/run.name/'events.json')+'">Timestamped events</a></p>'
body+='<h2>A · Backup DNS</h2><p>The forwarding client resolved through primary DNS, then continued through backup after primary stopped. A single-attempt initial test timed out; enabling client retransmissions produced failover after roughly two seconds. This tests a dnsmasq forwarder, not the macOS native resolver.</p>'
for n,t in [('A-before-failure','Primary available'),('A-primary-down-backup-resolution','Primary stopped: backup resolved')]:body+=block(n,t)
body+='<h2>B · TTL and cache flush</h2><p>A real caching forwarder retained the original IP after the authoritative record changed. Polling showed the old answer until expiry, then the new IP. SIGHUP flushed that forwarder’s cache; system DNS settings were not modified.</p>'
for n,t in [('B-cache-fill','Fill cache: TTL 30'),('B-cached-old-answer','Cached old answer after record change'),('B-fresh-new-answer','Fresh answer points at standby'),('B-before-cache-flush-still-standby','Before explicit cache flush'),('B-after-cache-flush-primary','After explicit cache flush')]:body+=block(n,t)
for e in events:
 if e['name'].startswith('B-ttl-poll'):body+=block(e['name'],'TTL observation '+e['time'])
body+='<h2>C · Firewall isolation</h2><p>Generated PF rules passed syntax validation. No firewall rules were activated. An administrator password and an independent client are required to prove the specified allow/block behavior and rollback. This extension remains incomplete.</p>'+block('deployment-pf-syntax','PF syntax validation')
body+='<h2>D · Backend failure and recovery</h2><p>Eight baseline requests reached both backends. Backend A was stopped; all eight requests returned HTTP 200 from B. A restarted and both backend identities returned during bounded recovery polling after the failure window.</p>'
for prefix,label in [('D-baseline-','Baseline'),('D-A-down-','A stopped'),('D-recovery-','A recovered')]:
 for f in sorted(run.glob(prefix+'*.txt')):body+=block(f.stem,label+' · '+f.stem)
body+='<h2>E · DNS cutover</h2><p>Real A records changed from the loopback edge to a second Nginx listener on this same Mac’s LAN address. Client requests selected the address returned by DNS using curl --resolve, preserving TLS hostname verification. This makes the DNS-to-edge choice explicit; it does not test a browser’s resolver or existing connection migration.</p>'
for n,t in [('E-cached-client-primary','Old cached answer reaches primary edge'),('E-fresh-client-standby','New answer reaches standby edge')]:body+=block(n,t)
body+='<h2>F · Troubleshooting rehearsal</h2><p>These faults were injected by the automated runner, not faculty. DNS timeout, wrong TCP port, untrusted certificate and unavailable upstreams produced distinguishable symptoms. Recovery returned HTTP 200.</p>'
for n,t in [('F-dns-fault','DNS fault'),('F-tcp-wrong-port','TCP fault'),('F-tls-untrusted-ca','TLS fault'),('F-application-both-backends-down','Application fault'),('F-recovered','Recovered application'),('cache-conditional-304','HTTP cache validation: 304')]:body+=block(n,t)
body+='<h2>Evidence integrity and cleanup</h2><p>All runner-started processes were terminated. No system DNS or firewall changes were made. SHA256SUMS hashes the evidence files. Private certificate keys are excluded from Git. See REPORT.md for remaining assignment requirements.</p></html>'
(root/'demonstrations.html').write_text(body)
print(root/'demonstrations.html')
