#!/usr/bin/env python3
"""Render portable configs; does not install or change host networking."""
import argparse, ipaddress, json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--inventory',type=Path,default=Path(__file__).with_name('inventory.json'))
p.add_argument('--target',choices=['primary','standby'],default='primary')
p.add_argument('--cert-dir',type=Path,help='Absolute certificate directory; default: OUT/certs')
p.add_argument('--out',type=Path,default=Path(__file__).with_name('generated'))
a=p.parse_args(); c=json.loads(a.inventory.read_text())
for k in ('primary_dns','backup_dns','edge','standby_edge','backend_host'):
    ipaddress.IPv4Address(c[k])
if not c['interface'].isalnum(): raise ValueError('Invalid interface')
if not 1 <= int(c['ttl']) <= 86400: raise ValueError('Invalid TTL')
if not 1 <= int(c['https_port']) <= 65535: raise ValueError('Invalid port')
a.out.mkdir(parents=True,exist_ok=True)
cert_dir=(a.cert_dir or a.out/'certs').resolve()
address=c['edge'] if a.target=='primary' else c['standby_edge']
for role in ('primary','backup'):
    text=f"""# Run on {role} DNS Mac. Reload BOTH resolvers after a record change.
port=53
interface={c['interface']}
listen-address=127.0.0.1,{c[role+'_dns']}
bind-interfaces
no-resolv
no-hosts
local=/teamX.test/
local-ttl={c['ttl']}
host-record=app.teamX.test,{address},{c['ttl']}
host-record=api.teamX.test,{address},{c['ttl']}
# Cache outside names, forward explicitly.
server=1.1.1.1
cache-size=1000
"""
    (a.out/f'dnsmasq-{role}.conf').write_text(text)
for role in ('primary','standby'):
    text=f"""# Launch with nginx -p ABSOLUTE_RUNTIME_DIR/ -c ABSOLUTE_CONFIG_PATH
worker_processes 1;
pid nginx.pid;
error_log logs/error.log info;
events {{ worker_connections 1024; }}
http {{
    log_format proof '$time_iso8601 client=$remote_addr edge={role} '
                     'status=$status upstream=$upstream_addr upstream_status=$upstream_status '
                     'request_time=$request_time request="$request"';
    access_log logs/access.log proof;
    upstream backend {{
        server {c['backend_host']}:3001 max_fails=1 fail_timeout=5s;
        server {c['backend_host']}:3002 max_fails=1 fail_timeout=5s;
    }}
    server {{
        listen {c['https_port']} ssl;
        server_name app.teamX.test api.teamX.test;
        ssl_certificate "{cert_dir}/server.crt";
        ssl_certificate_key "{cert_dir}/server.key";
        ssl_protocols TLSv1.2 TLSv1.3;
        add_header X-Edge {role} always;
        location / {{
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 1s;
            proxy_read_timeout 5s;
            proxy_next_upstream error timeout http_502 http_503 http_504;
            proxy_next_upstream_tries 2;
        }}
    }}
}}
"""
    (a.out/f'nginx-{role}.conf').write_text(text)
# Dedicated anchor: evaluate BEFORE any broad pass quick rules in main pf.conf.
# Use quick on the anchor invocation so a matching anchor decision is final.
text=f"""# Backend host only. Anchor invocation: anchor "cn_phase2" quick all
# Phase C strict mode. Standby on this host requires a separately reviewed local exception during migration.
pass in quick on {c['interface']} inet proto tcp from {c['edge']} to {c['backend_host']} port {{ 3001, 3002 }} keep state
block return in quick on {c['interface']} inet proto tcp from any to {c['backend_host']} port {{ 3001, 3002 }}
"""
(a.out/'backend.pf').write_text(text)
print('Rendered configs in',a.out.resolve())
