# 🌐 TeamX — Private Network Service Platform

### Computer Networks Course Project — Phase 1

> **LAN → Private DNS → TCP → TLS → HTTPS → Nginx Reverse Proxy → Load Balancing → Backend → HTTP Caching → Wireshark Analysis**

A fully local private network service platform built using three macOS machines connected to the same private LAN.

The project demonstrates how a client request for `app.teamX.test` or `api.teamX.test` travels from DNS resolution through an Nginx HTTPS edge server to one of two backend services, with caching and packet-level analysis.

---

# 📌 Table of Contents

- [Project Overview](#-project-overview)
- [Project Objectives](#-project-objectives)
- [Phase 1 Architecture](#-phase-1-architecture)
- [Machine and IP Configuration](#-machine-and-ip-configuration)
- [Network Topology](#-network-topology)
- [Complete Request Flow](#-complete-request-flow)
- [Protocol Stack](#-protocol-stack)
- [Phase 1 Tasks](#-phase-1-tasks)
  - [01 — LAN Setup](#01--lan-setup)
  - [02 — Private DNS](#02--private-dns)
  - [03 — Backend Services](#03--backend-services)
  - [04 — Nginx Reverse Proxy and Load Balancing](#04--nginx-reverse-proxy-and-load-balancing)
  - [05 — TLS and HTTPS](#05--tls-and-https)
  - [06 — HTTP Caching](#06--http-caching)
  - [07 — Wireshark Analysis](#07--wireshark-analysis)
  - [08 — Failure Demonstration](#08--failure-demonstration)
- [Request Lifecycle](#-request-lifecycle)
- [Repository Structure](#-repository-structure)
- [Evidence Structure](#-evidence-structure)
- [Tools Used](#-tools-used)
- [Security](#-security)
- [Testing Commands](#-testing-commands)
- [Phase 1 Demonstration Flow](#-phase-1-demonstration-flow)
- [Final Architecture](#-final-architecture)

---

# 📌 Project Overview

Team **TeamX** implemented a private network service platform using three macOS machines connected to the same local Wi-Fi network.

The private `.test` domains used by the project are:

```text
app.teamX.test
api.teamX.test
```

The client does not directly access the backend application services.

Instead, requests follow this path:

```text
Laptop 3
  │
  │ DNS Query — UDP 53
  ▼
Laptop 1 — Private DNS / dnsmasq
  │
  │ DNS Response
  │ app.teamX.test → 10.212.31.195
  ▼
Laptop 3
  │
  │ HTTPS — TCP 443
  ▼
Laptop 2 — Nginx Edge Server
  │
  │ Reverse Proxy / Load Balancing
  ├──────────────────────┐
  ▼                      ▼
Backend A              Backend B
:3001                  :3002
  │                      │
  └──────────┬───────────┘
             ▼
        HTTP Response
             │
             ▼
         Laptop 2
             │
             │ HTTPS
             ▼
         Laptop 3
```

The main purpose of Phase 1 is to build the core networking infrastructure, demonstrate the interaction between networking protocols and services, and provide packet-level and command-line evidence.

---

# 🎯 Project Objectives

The main objectives of Phase 1 are:

- Build a private LAN using three macOS machines.
- Configure a private DNS server using `dnsmasq`.
- Use the reserved `.test` namespace.
- Resolve `app.teamX.test` and `api.teamX.test`.
- Run two backend application services.
- Configure Nginx as a reverse proxy.
- Configure Nginx as a load balancer.
- Configure HTTPS using a local Certificate Authority.
- Verify TLS certificate validation.
- Demonstrate HTTP caching using `Cache-Control` and `ETag`.
- Capture and analyze DNS, TCP and TLS traffic using Wireshark.
- Demonstrate a controlled backend failure.
- Capture screenshots and terminal output as evidence.
- Demonstrate the complete end-to-end request flow.

---

# 🏗️ Phase 1 Architecture

The Phase 1 system uses three macOS machines.

```text
                         PRIVATE LAN / WI-FI
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        ┌────────────┐    ┌────────────┐    ┌────────────┐
        │  Laptop 1  │    │  Laptop 2  │    │  Laptop 3  │
        │ DNS Server │    │ Nginx Edge │    │ Client +   │
        │  dnsmasq   │    │ Reverse    │    │ Backends + │
        │    :53     │    │ Proxy / LB │    │ Wireshark  │
        └────────────┘    │    :443    │    └─────┬──────┘
                          └─────┬──────┘          │
                                │                 │
                                │ HTTP            │
                                ├─────────────────┤
                                │                 │
                                ▼                 ▼
                         Backend A           Backend B
                           :3001               :3002
```

Both Backend A and Backend B run on **Laptop 3**.

---

# 🖥️ Machine and IP Configuration

| Machine | Role | IP Address | Service / Port |
|---|---|---|---|
| **Laptop 1** | Private DNS Server | `10.212.31.217` | DNS `53` |
| **Laptop 2** | Nginx Edge / Reverse Proxy / Load Balancer | `10.212.31.195` | HTTPS `443` |
| **Laptop 3** | Client + Backend A + Backend B + Wireshark | `10.212.31.163` | HTTP `3001`, `3002` |

All three machines are connected to the same private Wi-Fi network.

---

# 🗺️ Network Topology

The logical topology is:

```text
                         ┌─────────────────────────┐
                         │      PRIVATE WI-FI      │
                         │        / LAN            │
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
     ┌────────────────┐     ┌────────────────┐     ┌────────────────────┐
     │    Laptop 1    │     │    Laptop 2    │     │     Laptop 3       │
     │   DNS Server   │     │ Edge / Nginx   │     │ Client + Backends  │
     │ 10.212.31.217  │     │ 10.212.31.195  │     │  10.212.31.163     │
     │   dnsmasq :53  │     │    HTTPS :443  │     │                    │
     └────────────────┘     └───────┬────────┘     │ Backend A :3001   │
             ▲                      │              │ Backend B :3002   │
             │                      │ HTTP         │ Wireshark         │
             │                      └─────────────►│                    │
             │                                     └────────────────────┘
             │
             │ DNS Query / Response
             └────────────────────────────────────
```

### DNS Mapping

```text
app.teamX.test → 10.212.31.195
api.teamX.test → 10.212.31.195
```

The DNS server is Laptop 1, but the DNS records point both application names to Laptop 2 because Laptop 2 is the HTTPS/Nginx edge server.

---

# 🔄 Complete Request Flow

The complete request flow is:

```text
1. Laptop 3 requests app.teamX.test
              │
              ▼
2. DNS query is sent to Laptop 1
              │
              │ UDP 53
              ▼
3. Laptop 1 / dnsmasq resolves the domain
              │
              │ app.teamX.test → 10.212.31.195
              ▼
4. Laptop 3 connects to Laptop 2
              │
              │ TCP 443
              ▼
5. TLS handshake is completed
              │
              ▼
6. Laptop 3 sends HTTPS request
              │
              ▼
7. Nginx receives the request
              │
              ▼
8. Nginx load-balances to Backend A or B
          ┌───┴───────────┐
          ▼               ▼
     Backend A        Backend B
     :3001             :3002
          │               │
          └───────┬───────┘
                  ▼
9. Backend returns HTTP response
                  │
                  ▼
10. Nginx returns HTTPS response to Laptop 3
```

---

# 🧱 Protocol Stack

| Layer / Concept | Technology | Purpose |
|---|---|---|
| Application | DNS | Converts domain names to IP addresses |
| Application | HTTP | Backend/application communication |
| Application | HTTPS | Secure web communication |
| Transport | TCP | Reliable connection |
| Security | TLS | Encryption and authentication |
| Network | IPv4 | Addressing between machines |
| Link | Wi-Fi | Local network communication |

---

# 🧩 Phase 1 Tasks

```text
01. LAN Setup
      │
      ▼
02. Private DNS
      │
      ▼
03. Backend Services
      │
      ▼
04. Nginx + Load Balancing
      │
      ▼
05. TLS / HTTPS
      │
      ▼
06. HTTP Caching
      │
      ▼
07. Wireshark Analysis
      │
      ▼
08. Failure Demonstration
```

---

# 01 — LAN Setup

## Objective

Establish communication between all three macOS machines on the same private Wi-Fi network.

## Machine Addresses

```text
Laptop 1 → 10.212.31.217
Laptop 2 → 10.212.31.195
Laptop 3 → 10.212.31.163
```

## Connectivity

LAN connectivity can be verified using:

```bash
ping 10.212.31.195
ping 10.212.31.163
```

The three machines must be reachable over the local network.

---

# 02 — Private DNS

## Objective

Configure a private DNS server on Laptop 1 using `dnsmasq`.

```text
DNS Server:
10.212.31.217:53
```

The private application domains are:

```text
app.teamX.test
api.teamX.test
```

Both resolve to the Nginx edge server:

```text
10.212.31.195
```

## DNS Configuration

The important records are:

```text
address=/app.teamX.test/10.212.31.195
address=/api.teamX.test/10.212.31.195
```

Other DNS queries can be forwarded to an external DNS server.

## DNS Flow

```text
Laptop 3
    │
    │ UDP 53
    │ app.teamX.test?
    ▼
Laptop 1
10.212.31.217
dnsmasq
    │
    │ 10.212.31.195
    ▼
Laptop 3
```

## Verification

```bash
dig @10.212.31.217 app.teamX.test
```

Expected result:

```text
app.teamX.test.    A    10.212.31.195
```

For the API domain:

```bash
dig @10.212.31.217 api.teamX.test
```

Expected result:

```text
api.teamX.test.    A    10.212.31.195
```

---

# 03 — Backend Services

Both backend services run on Laptop 3.

## Backend A

```text
Machine: Laptop 3
IP:      10.212.31.163
Port:    3001
Name:    A
```

Start with:

```bash
cd ~/Downloads/cn-phase1
BACKEND=A PORT=3001 python3 backend.py
```

Expected output:

```text
Backend A listening on 0.0.0.0:3001
```

## Backend B

```text
Machine: Laptop 3
IP:      10.212.31.163
Port:    3002
Name:    B
```

Start with:

```bash
cd ~/Downloads/cn-phase1
BACKEND=B PORT=3002 python3 backend.py
```

Expected output:

```text
Backend B listening on 0.0.0.0:3002
```

## Backend Architecture

```text
                    Nginx
                      │
             ┌────────┴────────┐
             │                 │
             ▼                 ▼
       Backend A          Backend B
       10.212.31.163      10.212.31.163
          :3001              :3002
```

The response includes:

```text
X-Backend: A
```

or:

```text
X-Backend: B
```

This makes load-balancing behavior directly observable.

---

# 04 — Nginx Reverse Proxy and Load Balancing

Nginx runs on Laptop 2:

```text
IP:   10.212.31.195
Port: 443
```

Nginx provides:

1. HTTPS termination
2. Reverse proxying
3. Load balancing
4. HTTP caching behavior

## Upstream Backends

```text
Backend A → 10.212.31.163:3001
Backend B → 10.212.31.163:3002
```

## Reverse Proxy

The client never needs to connect directly to the backend ports.

```text
Laptop 3
   │
   │ HTTPS :443
   ▼
Laptop 2
  Nginx
   │
   ├──────────────► 10.212.31.163:3001
   │                   Backend A
   │
   └──────────────► 10.212.31.163:3002
                       Backend B
```

## Load Balancing

Multiple HTTPS requests can be distributed between the two backend services.

Example observed behavior:

```text
Request 1 → X-Backend: A
Request 2 → X-Backend: B
Request 3 → X-Backend: A
Request 4 → X-Backend: B
...
```

The exact sequence may vary because of Nginx's active upstream state.

## Configuration Validation

```bash
nginx -t
```

A successful test reports:

```text
syntax is ok
test is successful
```

---

# 05 — TLS and HTTPS

TLS is terminated at Nginx on Laptop 2.

The application is accessed through:

```text
https://app.teamX.test
```

and:

```text
https://api.teamX.test
```

## Certificate

A local Certificate Authority was used to create a server certificate for the private `.test` domains.

The certificate uses:

```text
CN=app.teamX.test
```

with appropriate SAN entries for the application domains.

## TLS Flow

```text
Laptop 3
    │
    │ TCP connection
    ▼
Laptop 2 / Nginx
    │
    │ TLS handshake
    ├── Certificate
    ├── Key exchange
    └── Secure session
    │
    ▼
Encrypted HTTPS traffic
```

## HTTPS Verification

A successful test:

```bash
curl -v https://app.teamX.test
```

should show successful TLS negotiation and certificate verification.

Observed working configuration included:

```text
SSL connection using TLSv1.3
```

and:

```text
SSL certificate verify ok.
```

The HTTP response was:

```text
HTTP/1.1 200 OK
```

with an `X-Backend` header identifying the selected backend.

---

# 06 — HTTP Caching

The project demonstrates HTTP caching using:

- `Cache-Control`
- `ETag`
- Conditional requests
- `304 Not Modified`

## Cacheable Endpoint

```text
/api/info
```

A successful first request returns:

```text
HTTP/1.1 200 OK
Cache-Control: max-age=60
ETag: "<etag-value>"
```

Example:

```json
{
  "service": "cn-project",
  "version": 1,
  "note": "cacheable endpoint"
}
```

## Conditional Request

The client can send the ETag back:

```bash
curl -i -H 'If-None-Match: "<etag-value>"' \
https://app.teamX.test/api/info
```

A matching resource returns:

```text
HTTP/1.1 304 Not Modified
```

This demonstrates conditional HTTP caching without transferring the complete resource again.

---

# 07 — Wireshark Analysis

Wireshark is used on Laptop 3 to observe the actual network traffic.

The main protocols and traffic include:

- DNS
- TCP
- TLS
- HTTPS
- Backend HTTP traffic
- TCP ports
- Packet source and destination addresses

## DNS Capture

Display filter:

```text
dns
```

The capture should show the DNS query and response for:

```text
app.teamX.test
```

with the response address:

```text
10.212.31.195
```

## TCP Handshake

Display filter:

```text
tcp
```

The TCP connection to Nginx can be observed as:

```text
SYN
 ↓
SYN-ACK
 ↓
ACK
```

## TLS

Display filter:

```text
tls
```

The TLS handshake can be observed after the TCP connection is established.

Because HTTPS is encrypted, application data is not visible as ordinary HTTP payload content.

---

# 08 — Failure Demonstration

Phase 1 includes a controlled backend failure demonstration.

## Backend Failure

One backend is stopped while the other remains available.

```text
                  Nginx
                    │
             ┌──────┴──────┐
             │             │
             ▼             X
        Backend A       Backend B
         :3001            :3002
        RUNNING           STOPPED
```

The purpose is to demonstrate how the edge server behaves when one upstream service becomes unavailable.

After the demonstration, the stopped backend is restarted and normal operation is restored.

---

# 🔁 Request Lifecycle

The complete request lifecycle is:

```text
┌─────────────────────────┐
│       Laptop 3          │
│     Client / curl       │
└───────────┬─────────────┘
            │
            │ 1. DNS Query
            ▼
┌─────────────────────────┐
│       Laptop 1          │
│  dnsmasq — UDP 53       │
│    10.212.31.217        │
└───────────┬─────────────┘
            │
            │ 2. DNS Response
            │    10.212.31.195
            ▼
┌─────────────────────────┐
│       Laptop 3          │
└───────────┬─────────────┘
            │
            │ 3. TCP :443
            ▼
┌─────────────────────────┐
│       Laptop 2          │
│        Nginx            │
│    10.212.31.195        │
└───────────┬─────────────┘
            │
            │ 4. TLS Handshake
            │
            │ 5. HTTPS Request
            ▼
      ┌─────┴─────┐
      │           │
      ▼           ▼
┌───────────┐ ┌───────────┐
│ Backend A │ │ Backend B │
│ :3001     │ │ :3002     │
│ Laptop 3  │ │ Laptop 3  │
└─────┬─────┘ └─────┬─────┘
      │              │
      └──────┬───────┘
             │
             │ 6. HTTP Response
             ▼
        ┌─────────┐
        │  Nginx  │
        └────┬────┘
             │
             │ 7. HTTPS Response
             ▼
        ┌─────────┐
        │ Laptop 3│
        └─────────┘
```

---

# 📂 Suggested Repository Structure

```text
teamX-cn-phase1/
│
├── architecture/
│   ├── lan-topology.png
│   └── request-flow.png
│
├── backend/
│   └── backend.py
│
├── config/
│   ├── dns/
│   │   └── dnsmasq.conf
│   ├── nginx/
│   │   └── nginx.conf
│   └── tls/
│       └── README.md
│
├── demo/
│   └── CN_Phase1_[Section]_[TeamName]_[InfraType].mp4
│
├── evidence/
│   └── phase1/
│       ├── 01-lan/
│       ├── 02-dns/
│       ├── 03-backend/
│       ├── 04-nginx/
│       ├── 05-tls/
│       ├── 06-caching/
│       ├── 07-wireshark/
│       └── 08-failures/
│
├── wireshark/
│   └── captures/
│
├── .gitignore
└── README.md
```

---

# 📸 Evidence Structure

Evidence should be organized according to the Phase 1 components:

```text
evidence/phase1/

├── 01-lan/
│   ├── ip-addresses/
│   ├── ping-tests/
│   └── topology/
│
├── 02-dns/
│   ├── dnsmasq-config/
│   ├── app-resolution/
│   ├── api-resolution/
│   └── client-dns-settings/
│
├── 03-backend/
│   ├── backend-a/
│   └── backend-b/
│
├── 04-nginx/
│   ├── nginx-config/
│   ├── nginx-test/
│   └── load-balancing/
│
├── 05-tls/
│   ├── certificate/
│   ├── certificate-verification/
│   └── https/
│
├── 06-caching/
│   ├── cache-control/
│   ├── etag/
│   └── 304/
│
├── 07-wireshark/
│   ├── dns/
│   ├── tcp/
│   └── tls/
│
└── 08-failures/
    └── backend-failure/
```

---

# 🛠️ Tools Used

| Tool | Purpose |
|---|---|
| macOS Terminal | Network and service configuration |
| `ping` | LAN connectivity testing |
| `dig` | DNS testing |
| `dnsmasq` | Private DNS server |
| Nginx | Reverse proxy and load balancing |
| OpenSSL | TLS certificate generation and verification |
| `curl` | HTTP and HTTPS testing |
| Wireshark | Packet capture and protocol analysis |
| Python | Backend HTTP services |
| Git | Version control |

---

# 🔐 Security

The project uses a local Certificate Authority for HTTPS.

Private cryptographic keys must not be committed to a public repository.

Sensitive files include:

```text
server.key
ca.key
```

These should be excluded using `.gitignore`.

The project is intended for a controlled private LAN environment and uses `.test` domains rather than public DNS.

---

# 🧪 Testing Commands

## DNS

```bash
dig app.teamX.test
```

```bash
dig api.teamX.test
```

Or query the DNS server directly:

```bash
dig @10.212.31.217 app.teamX.test
```

```bash
dig @10.212.31.217 api.teamX.test
```

## Backend A

From Laptop 2 or another machine on the LAN:

```bash
curl -i http://10.212.31.163:3001/
```

## Backend B

```bash
curl -i http://10.212.31.163:3002/
```

## HTTPS

```bash
curl -v https://app.teamX.test/
```

## Load Balancing

```bash
for i in {1..6}; do
  curl -s -D - https://app.teamX.test/ -o /dev/null | grep X-Backend
done
```

The output should demonstrate requests being handled by Backend A and Backend B when both upstreams are active.

## HTTP Caching

```bash
curl -i https://app.teamX.test/api/info
```

Copy the returned ETag and use:

```bash
curl -i -H 'If-None-Match: "<ETAG>"' \
https://app.teamX.test/api/info
```

Expected conditional response:

```text
HTTP/1.1 304 Not Modified
```

## Nginx Configuration Test

On Laptop 2:

```bash
nginx -t
```

Expected:

```text
syntax is ok
test is successful
```

## Nginx HTTPS Listener

```bash
sudo lsof -nP -iTCP:443 -sTCP:LISTEN
```

Expected to show Nginx listening on:

```text
*:443
```

---

# 🎥 Phase 1 Demonstration Flow

The 5-minute demonstration can follow this sequence:

```text
01. Team Introduction
        │
        ▼
02. LAN + Machine Roles
        │
        ▼
03. DNS Resolution
        │
        ▼
04. HTTPS / TLS
        │
        ▼
05. Nginx Reverse Proxy
        │
        ▼
06. Load Balancing
        │
        ▼
07. HTTP Caching
        │
        ▼
08. Wireshark Evidence
        │
        ▼
09. Failure Demonstration
        │
        ▼
10. Final Working Request
```

## Suggested Evidence to Show

### DNS

```bash
dig app.teamX.test
```

Show:

```text
SERVER: 10.212.31.217#53
ANSWER:
app.teamX.test → 10.212.31.195
```

### TLS / HTTPS

```bash
curl -v https://app.teamX.test/
```

Show successful TLS negotiation and:

```text
HTTP/1.1 200 OK
X-Backend: A
```

or:

```text
X-Backend: B
```

### Load Balancing

```bash
for i in {1..6}; do
  curl -s -D - https://app.teamX.test/ -o /dev/null | grep X-Backend
done
```

### Caching

```bash
curl -i https://app.teamX.test/api/info
```

Show:

```text
Cache-Control: max-age=60
ETag: "..."
```

Then show:

```text
HTTP/1.1 304 Not Modified
```

### Failure Demonstration

Stop one backend and repeat the HTTPS request to demonstrate the effect of an unavailable upstream.

---

# 📊 Architecture Summary

```text
                         CLIENT
                    Laptop 3
                 10.212.31.163
                         │
                         │ DNS Query
                         ▼
              ┌─────────────────────┐
              │     Laptop 1        │
              │   Private DNS       │
              │ 10.212.31.217:53   │
              │      dnsmasq        │
              └──────────┬──────────┘
                         │
                         │ IP = 10.212.31.195
                         ▼
              ┌─────────────────────┐
              │     Laptop 2        │
              │       Nginx         │
              │ 10.212.31.195:443  │
              │                     │
              │ Reverse Proxy       │
              │ Load Balancer       │
              │ TLS Termination     │
              └──────────┬──────────┘
                         │
                    ┌────┴────┐
                    │         │
                    ▼         ▼
             ┌──────────┐ ┌──────────┐
             │Backend A │ │Backend B │
             │ :3001    │ │ :3002    │
             │          │ │          │
             │ Laptop 3 │ │ Laptop 3 │
             └────┬─────┘ └────┬─────┘
                  │             │
                  └──────┬──────┘
                         │
                         ▼
                    HTTP Response
                         │
                         ▼
                       Nginx
                         │
                         │ HTTPS
                         ▼
                     Laptop 3
```

---

# 🔬 Wireshark Protocol View

The project can be observed packet-by-packet:

```text
┌────────────────────────────────────────────────────┐
│                    APPLICATION                     │
│                                                    │
│       DNS                 HTTP / HTTPS             │
│        │                      │                    │
├────────┼──────────────────────┼────────────────────┤
│        │          TLS         │                    │
│        │           │          │                    │
├────────┼───────────┼──────────┼────────────────────┤
│                 TCP Transport                       │
│                                                    │
│              SYN → SYN-ACK → ACK                  │
├────────────────────────────────────────────────────┤
│                     IPv4                           │
├────────────────────────────────────────────────────┤
│                     Wi-Fi                          │
└────────────────────────────────────────────────────┘
```

---

# 🚀 Final Result

The TeamX Phase 1 platform provides a complete local network service path:

```text
LAN
 │
 ├── Private DNS
 │
 ├── TCP
 │
 ├── TLS
 │
 ├── HTTPS
 │
 ├── Nginx Reverse Proxy
 │
 ├── Load Balancing
 │
 ├── Backend A / Backend B
 │
 ├── HTTP Caching
 │
 ├── Wireshark Analysis
 │
 └── Failure Demonstration
```

The final system demonstrates how DNS, TCP, TLS, HTTPS, reverse proxying, load balancing, backend services, HTTP caching, and packet analysis work together as one private network service platform.
