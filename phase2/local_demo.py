#!/usr/bin/env python3
"""Real service rehearsal on one Mac; never claims physical multi-host isolation."""
import datetime,hashlib,json,os,signal,socket,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
OUT=ROOT/'phase2/local-evidence'/RUN; OUT.mkdir(parents=True,exist_ok=True)
RUNTIME=ROOT/'phase2/local-runtime'/RUN;RUNTIME.mkdir(parents=True,exist_ok=True)
DNS='/usr/local/opt/dnsmasq/sbin/dnsmasq';NGINX='/opt/homebrew/bin/nginx';TSHARK='/Applications/Wireshark.app/Contents/MacOS/tshark'
IP=subprocess.check_output(['/usr/sbin/ipconfig','getifaddr','en0'],text=True).strip()
procs={}; handles=[]; events=[]
def record(name,**kw):
 e=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),name=name,**kw);events.append(e);print(json.dumps(e),flush=True)
def command(name,args,ok=True):
 r=subprocess.run(args,capture_output=True,text=True,timeout=20)
 (OUT/(name+'.txt')).write_text('$ '+ ' '.join(map(str,args))+'\n'+r.stdout+r.stderr+'\nEXIT '+str(r.returncode)+'\n')
 record(name,exit_code=r.returncode)
 if ok and r.returncode:raise RuntimeError(name+': '+r.stderr)
 return r

def start(name,args,env=None):
 f=(OUT/(name+'-process.log')).open('a');handles.append(f)
 procs[name]=subprocess.Popen(args,stdout=f,stderr=subprocess.STDOUT,env=env);time.sleep(.2)
 if procs[name].poll() is not None:raise RuntimeError(name+' exited: '+(OUT/(name+'-process.log')).read_text())
 record('start',role=name,pid=procs[name].pid)
def stop(name):
 p=procs.pop(name,None)
 if p:
  p.terminate()
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
  record('stop',role=name)
def dnsconfig(name,port,address=None,servers=None,cache=0):
 f=RUNTIME/(name+'.conf')
 text=f'port={port}\nlisten-address=127.0.0.1\nbind-interfaces\nno-resolv\nno-hosts\ncache-size={cache}\nlog-queries\nlog-facility=-\npid-file={RUNTIME}/{name}.pid\n'
 if address:text+=f'local=/teamX.test/\nhost-record=app.teamX.test,{address},30\nhost-record=api.teamX.test,{address},30\n'
 if servers:
  text+='strict-order\n'
  for upstream in servers:text+=f'server=127.0.0.1#{upstream}\n'
 f.write_text(text);return f

def dnsstart(name):start(name,[DNS,'--no-daemon','--conf-file='+str(RUNTIME/(name+'.conf'))])
def query(name,port):
 r=command(name,['/usr/bin/dig','@127.0.0.1','-p',str(port),'app.teamX.test','A','+time=2','+tries=4'])
 rows=[l.split() for l in r.stdout.splitlines() if l and not l.startswith(';') and ' IN ' in l.replace('\t',' ')]
 answers=[x for x in rows if len(x)>=5 and x[3]=='A']
 return [(int(x[1]),x[4]) for x in answers]
def curl(name,address='127.0.0.1',path='/api/status',ca=None,port=18443,headers=None,ok=True):
 args=['/usr/bin/curl','--noproxy','*','--connect-timeout','2','--max-time','5','--cacert',str(ca or RUNTIME/'certs/ca.crt'),'--resolve',f'app.teamX.test:{port}:{address}','-sS','-D','-']
 if headers:
  for h in headers:args+=['-H',h]
 args += [f'https://app.teamX.test:{port}{path}'];return command(name,args,ok)
def backend(label):start('backend-'+label,[sys.executable,str(ROOT/'backend/backend.py')],{**os.environ,'BACKEND':label,'PORT':str(13001 if label=='A' else 13002),'PYTHONUNBUFFERED':'1'})
try:
 for port in [13001,13002,15353,15354,15355,15356,18443]:
  s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port));s.close()
 record('scope',physical_machines=1,primary_edge='127.0.0.1',standby_edge=IP,dns_ports=[15353,15354],backends=[13001,13002],https_port=18443,system_dns_modified=False,firewall_modified=False)
 certs=RUNTIME/'certs';certs.mkdir(exist_ok=True)
 (certs/'ca.conf').write_text('[req]\ndistinguished_name=dn\nx509_extensions=ca\nprompt=no\n[dn]\nCN=TeamX Single-Mac Rehearsal CA\n[ca]\nbasicConstraints=critical,CA:TRUE\nkeyUsage=critical,keyCertSign,cRLSign\n')
 command('ca-generation',['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','2','-config',str(certs/'ca.conf'),'-keyout',str(certs/'ca.key'),'-out',str(certs/'ca.crt')])
 command('leaf-request',['openssl','req','-new','-newkey','rsa:2048','-nodes','-subj','/CN=app.teamX.test','-keyout',str(certs/'server.key'),'-out',str(certs/'server.csr')])
 (certs/'leaf.ext').write_text('basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=DNS:app.teamX.test,DNS:api.teamX.test\n')
 command('leaf-signing',['openssl','x509','-req','-in',str(certs/'server.csr'),'-CA',str(certs/'ca.crt'),'-CAkey',str(certs/'ca.key'),'-CAcreateserial','-days','2','-extfile',str(certs/'leaf.ext'),'-out',str(certs/'server.crt')])
 for f in certs.glob('*.key'):f.chmod(0o600)
 # Parse actual deployment configurations using their generated inventory, unmodified.
 command('deployment-dns-primary-syntax',[DNS,'--test','--conf-file='+str(ROOT/'phase2/generated/dnsmasq-primary.conf')])
 command('deployment-dns-backup-syntax',[DNS,'--test','--conf-file='+str(ROOT/'phase2/generated/dnsmasq-backup.conf')])
 command('deployment-pf-syntax',['/sbin/pfctl','-nf',str(ROOT/'phase2/generated/backend.pf')])
 # Nginx config generation uses same generator, adapted only to this rehearsal's ports/IPs.
 inv=json.loads((ROOT/'phase2/inventory.json').read_text());inv.update(backend_host='127.0.0.1',edge='127.0.0.1',standby_edge=IP,https_port=18443)
 (RUNTIME/'inventory.json').write_text(json.dumps(inv))
 command('local-config-generation',[sys.executable,str(ROOT/'phase2/generate.py'),'--inventory',str(RUNTIME/'inventory.json'),'--out',str(RUNTIME/'generated'),'--cert-dir',str(certs)])
 for role,addr in [('primary','127.0.0.1'),('standby',IP)]:
  d=RUNTIME/role;(d/'logs').mkdir(parents=True,exist_ok=True)
  (d/'certs').symlink_to(certs,target_is_directory=True) if not (d/'certs').exists() else None
  text=(RUNTIME/'generated'/f'nginx-{role}.conf').read_text().replace('listen 18443 ssl;',f'listen {addr}:18443 ssl;').replace(':3001 ',':13001 ').replace(':3002 ',':13002 ')
  (d/'nginx.conf').write_text(text)
  command(role+'-nginx-syntax',[NGINX,'-t','-p',str(d)+'/', '-c',str(d/'nginx.conf')])
 backend('A');backend('B')
 start('capture',[TSHARK,'-i','lo0','-f','port 15353 or port 15354 or port 15355 or port 15356 or tcp port 18443 or tcp port 13001 or tcp port 13002','-w',str(OUT/'single-mac.pcapng')])
 for role in ['primary','standby']:
  d=RUNTIME/role;start(role+'-edge',[NGINX,'-p',str(d)+'/', '-c',str(d/'nginx.conf'),'-g','daemon off;'])
 for name,port in [('dns-primary',15353),('dns-backup',15354)]:dnsconfig(name,port,'127.0.0.1');dnsstart(name)
 dnsconfig('client-failover',15355,servers=[15353,15354]);dnsstart('client-failover')
 assert query('A-before-failure',15355)[0][1]=='127.0.0.1'
 stop('dns-primary')
 assert query('A-primary-down-backup-resolution',15355)[0][1]=='127.0.0.1'
 dnsstart('dns-primary');record('A-rehearsal-pass',limitation='dnsmasq client forwarder; not native macOS client resolver failover')
 dnsconfig('client-cache',15356,servers=[15353],cache=100);dnsstart('client-cache')
 before=query('B-cache-fill',15356);assert before[0][1]=='127.0.0.1'
 for i in range(8):assert '200 OK' in curl(f'D-baseline-{i}').stdout
 r=curl('cache-info',path='/api/info');etag=next(l.split(':',1)[1].strip() for l in r.stdout.splitlines() if l.lower().startswith('etag:'))
 assert '304 Not Modified' in curl('cache-conditional-304',path='/api/info',headers=['If-None-Match: '+etag]).stdout
 # Cut over real DNS A records to another actual local address, same TLS port.
 for name,port in [('dns-primary',15353),('dns-backup',15354)]:
  stop(name);dnsconfig(name,port,IP);dnsstart(name)
 old=query('B-cached-old-answer',15356);new=query('B-fresh-new-answer',15353)
 assert old[0][1]=='127.0.0.1' and new[0][1]==IP
 assert 'X-Edge: primary' in curl('E-cached-client-primary',address=old[0][1]).stdout
 assert 'X-Edge: standby' in curl('E-fresh-client-standby',address=new[0][1]).stdout
 # Poll rather than pretend expiry is instantaneous.
 deadline=time.monotonic()+35
 while True:
  answer=query('B-ttl-poll-'+str(len(events)),15356)
  if answer[0][1]==IP:break
  if time.monotonic()>deadline:raise AssertionError('TTL did not expire')
  time.sleep(2)
 record('B-expiry-pass',answer=answer)
 # Fill old again then show actual forwarder cache flush via SIGHUP.
 for name,port in [('dns-primary',15353),('dns-backup',15354)]:
  stop(name);dnsconfig(name,port,'127.0.0.1');dnsstart(name)
 assert query('B-before-cache-flush-still-standby',15356)[0][1]==IP
 procs['client-cache'].send_signal(signal.SIGHUP);time.sleep(.2)
 assert query('B-after-cache-flush-primary',15356)[0][1]=='127.0.0.1'
 record('B-flush-pass',limitation='dnsmasq caching forwarder; not macOS mDNSResponder cache')
 stop('backend-A')
 for i in range(8):
  r=curl(f'D-A-down-{i}');assert '200 OK' in r.stdout and 'X-Backend: B' in r.stdout
 backend('A');time.sleep(5.2)
 results=[]
 for i in range(20):
  results.append(curl(f'D-recovery-{i}').stdout)
  if any('X-Backend: A' in x for x in results) and any('X-Backend: B' in x for x in results):break
  time.sleep(.5)
 assert any('X-Backend: A' in x for x in results) and any('X-Backend: B' in x for x in results)
 record('D-backend-ha-pass')
 # Rehearsed faults, not faculty injected.
 command('F-dns-fault',['/usr/bin/dig','@127.0.0.1','-p','15999','app.teamX.test','+time=1','+tries=1'],ok=False)
 r=curl('F-tcp-wrong-port',port=18444,ok=False);assert r.returncode!=0
 r=command('F-tls-untrusted-ca',['/usr/bin/curl','--noproxy','*','--resolve','app.teamX.test:18443:127.0.0.1','--max-time','5','-v','https://app.teamX.test:18443/api/status'],ok=False);assert r.returncode==60
 stop('backend-A');stop('backend-B')
 r=curl('F-application-both-backends-down');assert '502 Bad Gateway' in r.stdout or '504 Gateway' in r.stdout
 backend('A');backend('B');time.sleep(5.2)
 for attempt in range(10):
  recovery=curl('F-recovery-attempt-'+str(attempt))
  if '200 OK' in recovery.stdout:break
  time.sleep(1)
 else:raise AssertionError('Backend recovery exceeded bounded retry window')
 assert '200 OK' in curl('F-recovered').stdout
 record('F-rehearsal-pass',faculty_injected=False)
 record('C-status',syntax_valid=True,firewall_activated=False,independent_client_test=False,reason='administrator password and independent Mac unavailable')
 record('rehearsal-complete',scope='one physical Mac')
except Exception as error:
 record('rehearsal-error',error=str(error))
 raise
finally:
 for name in list(procs):stop(name)
 for role in ['primary','standby']:
  d=RUNTIME/role/'logs'
  if d.exists():
   for f in d.iterdir():
    if f.is_file():(OUT/(role+'-'+f.name)).write_bytes(f.read_bytes())
 for h in handles:h.close()
 (OUT/'events.json').write_text(json.dumps(events,indent=2)+'\n')
 for f in OUT.iterdir():
  if f.is_file() and f.suffix=='.log':
   pass
 (OUT/'SHA256SUMS').write_text('\n'.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name for f in sorted(OUT.iterdir()) if f.is_file() and f.name!='SHA256SUMS')+'\n')
