#!/usr/bin/env python3
"""Read-only layered checks. Captures real output and exit codes."""
import argparse, datetime, json, subprocess
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--ca',required=True); p.add_argument('--out',type=Path,required=True)
a=p.parse_args(); c=json.loads(Path(__file__).with_name('inventory.json').read_text()); a.out.mkdir(parents=True,exist_ok=True)
checks=[('dns-primary',['dig','+time=2','+tries=1','@'+c['primary_dns'],'app.teamX.test']),('dns-backup',['dig','+time=2','+tries=1','@'+c['backup_dns'],'app.teamX.test']),('system-resolvers',['scutil','--dns']),('tcp',['nc','-vz','-G','3',c['edge'],str(c['https_port'])]),('https-system-dns',['curl','--noproxy','*','--cacert',a.ca,'--connect-timeout','3','--max-time','10','-v','https://app.teamX.test:'+str(c['https_port'])+'/api/status']),('https-bypass-dns',['curl','--noproxy','*','--cacert',a.ca,'--resolve','app.teamX.test:'+str(c['https_port'])+':'+c['edge'],'--max-time','10','-v','https://app.teamX.test:'+str(c['https_port'])+'/api/status'])]
results=[]
for name,cmd in checks:
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=20); code=r.returncode; output=r.stdout+r.stderr
    except (OSError,subprocess.TimeoutExpired) as e: code=-1; output=str(e)
    (a.out/(name+'.txt')).write_text(output)
    results.append(dict(name=name,command=cmd,exit_code=code,time=datetime.datetime.now(datetime.timezone.utc).isoformat()))
(a.out/'manifest.json').write_text(json.dumps(results,indent=2)+'\n')
print('Evidence saved. Inspect DNS ANSWER/status even when dig exits 0. --resolve isolates DNS; it does not prove resolver failover.')
