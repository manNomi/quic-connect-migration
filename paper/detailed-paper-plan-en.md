# Detailed Paper Plan: Assessing the Deployment Maturity of HTTP/3 Connection Migration for Web Task Continuity

Date: 2026-06-24  
Document type: result-driven detailed paper plan  
Purpose: advisor discussion, paper structure finalization, follow-up experiment planning

## 1. Core Direction

### 1.1 Working Title

**Assessing the Deployment Maturity of HTTP/3 Connection Migration for Web Task Continuity**

Korean title:

**HTTP/3 Connection Migration의 배포 성숙도와 웹 작업 연속성 평가**

### 1.2 Problem Statement

QUIC connection migration allows a connection to survive client IP or port changes by using connection IDs and path validation. This feature appears useful for HTTP/3 applications operating under changing access networks, such as Wi-Fi-to-cellular transitions, mobile field work, large media uploads, and long-running dashboard sessions.

The evidence collected in this project suggests that the practical question is not simply:

> Why is this useful feature not used?

The stronger research question is:

> QUIC connection migration exists as an implementation-level transport primitive in several stacks, but what additional conditions are required before it becomes deployable HTTP/3 web task continuity?

Therefore, this paper evaluates connection migration across three layers:

1. implementation maturity,
2. deployment-path maturity,
3. application task continuity.

### 1.3 Main Claim

The central claim is:

> QUIC connection migration already exists as a testable transport primitive in multiple major implementations. However, deployable HTTP/3 web task continuity requires CID-aware routing, proxy/CDN behavior, client/browser migration policy, observability, and application workload semantics to align.

The result-driven version is:

> Under a controlled quic-go client and AWS NLB `TCP_QUIC :443` passthrough deployment, HTTP/3 request continuity and 1MiB mid-flight upload/download body continuity were preserved when backend-generated CIDs matched the AWS NLB QUIC-LB plaintext Server ID format. However, the HAProxy negative control and NLB CID mismatch controls show that HTTP/3 support alone does not imply connection migration support.

## 2. Research Questions

### RQ1. Implementation Maturity

**To what extent do major QUIC implementations support connection migration primitives?**

Sub-questions:

- Is there an active migration API?
- Is passive NAT rebinding handled?
- Is path validation implemented?
- Are qlog, PathEvent, NetLog, or equivalent observability mechanisms available?
- Are failure cases, disabled migration, zero-length CID, and preferred address tested?

Current answer:

- quic-go, quiche, picoquic, s2n-quic, ngtcp2, Quinn, Neqo, and aioquic provide migration primitives or test evidence.
- Therefore, it is inaccurate to say that connection migration is simply not implemented.
- However, API exposure, observability, and deployment readiness differ substantially across implementations.

### RQ2. Deployment-Path Maturity

**Which HTTP/3 deployment paths preserve or break connection migration?**

Sub-questions:

- Does active migration work in a direct-origin deployment?
- Does an HTTP/3 reverse proxy support active migration?
- Behind a load balancer, do packets continue to reach the same backend after the client tuple changes?
- Is CID-aware routing necessary for load-balanced migration continuity?

Current answer:

- EC2 direct-origin positive control: PASS.
- HAProxy HTTP/3 negative control: baseline HTTP/3 succeeds, active migration path validation fails.
- AWS NLB preserves continuity when the CID format and registered `QuicServerId` match.
- Malformed CID and mismatched Server ID controls fail.

### RQ3. HTTP/3 Task Continuity

**Does transport-level migration translate into HTTP/3 application task completion?**

Sub-questions:

- Can the same HTTP/3 connection complete requests before and after migration?
- During an upload body transfer, does the server receive the complete body after migration?
- During a streaming download response, does the client receive the complete body after migration?

Current answer:

- Local HTTP/3 post-migration request continuity: PASS.
- AWS NLB `TCP_QUIC :443` HTTP/3 post-migration request continuity: PASS.
- Local HTTP/3 mid-flight upload/download: PASS.
- AWS NLB `TCP_QUIC :443` mid-flight upload/download: PASS.

### RQ4. Remaining Browser/Mobile Question

**Can controlled quic-go results be generalized to real browser and mobile handover behavior?**

Current answer:

- Not yet.
- Chrome/Android/Cronet policy, real Wi-Fi-to-cellular handover, and CloudFront viewer-edge continuity remain future work.

## 3. Contributions

### Contribution 1. Maturity Taxonomy

The paper classifies major QUIC implementations by source evidence, test evidence, public control API, observability, and deployment implications.

Candidate sentence:

> We provide a source-backed maturity taxonomy of QUIC connection migration implementations, distinguishing transport mechanisms, public control APIs, observability, test coverage, and deployment readiness.

### Contribution 2. Separating HTTP/3 Support from Migration Support

The HAProxy negative control shows that HTTP/3 endpoint availability does not imply active connection migration support.

Candidate sentence:

> We experimentally show that HTTP/3 endpoint availability does not imply end-to-end QUIC connection migration support.

Key evidence:

- HAProxy 3.4.0 HTTP/3 baseline request succeeds.
- quiche `--perform-migration` active migration attempt fails.
- 3 `PATH_CHALLENGE` frames, 0 `PATH_RESPONSE` frames.
- migrated path ends in `validation_state=Failed`.

### Contribution 3. CID-Aware Load Balancing

AWS NLB experiments show that load-balanced migration continuity is sensitive to CID format and registered Server ID.

Candidate sentence:

> We demonstrate that deployable migration behind AWS NLB requires CID-aware routing compatibility: the backend-generated QUIC CID must encode the registered Server ID in the expected QUIC-LB plaintext format.

Key evidence:

- AWS NLB `QUIC :4242`: PASS.
- AWS NLB `TCP_QUIC :443`: PASS.
- malformed CID: FAIL, CloudWatch unknown Server ID drops.
- explicit Server ID mismatch: FAIL, target health 2/2 but handshake/application payload fails.

### Contribution 4. HTTP/3 Workload Continuity

The paper extends beyond transport streams to HTTP/3 post-migration requests and mid-flight body transfers.

Candidate sentence:

> We extend transport-level migration validation to HTTP/3 task continuity by testing post-migration requests and mid-flight 1MiB upload/download body transfers.

Key evidence:

- local HTTP/3 post-migration request continuity: PASS.
- AWS NLB HTTP/3 post-migration request continuity: PASS.
- local mid-flight upload/download: PASS.
- AWS NLB mid-flight upload/download: PASS.

## 4. Detailed Paper Structure

## 4.1 Introduction

### Purpose

Explain why the study is needed.

Argument flow:

1. QUIC can use connection IDs to preserve connections across IP/port changes.
2. This is attractive for HTTP/3 web task continuity.
3. However, HTTP/3 support, QUIC implementation support, CDN/LB deployment behavior, browser policy, and application recovery are separate layers.
4. Therefore, the paper evaluates when connection migration preserves web task continuity, rather than asking whether HTTP/3 is simply enabled.

Previewed results:

- Multiple implementations provide migration primitives.
- HAProxy supports HTTP/3 but fails active migration.
- AWS NLB preserves continuity when CID conditions are correct.
- Controlled quic-go experiments preserve HTTP/3 mid-flight upload/download.

## 4.2 Background

### Required Topics

1. QUIC connection IDs.
2. Path validation.
3. Active migration vs. passive NAT rebinding.
4. Distinguishing preferred address, multipath, and server-side migration.
5. HTTP/3 deployment paths.
6. Definition of web task continuity.

### Key Terms

| Term | Meaning in this paper |
| --- | --- |
| Connection migration | RFC 9000 single-path client-side active migration and NAT rebinding focus |
| Passive rebinding | Peer address changes due to NAT or path change |
| Active migration | Client intentionally validates and switches to a new path |
| Path validation | Reachability verification using `PATH_CHALLENGE` and `PATH_RESPONSE` |
| HTTP/3 task continuity | HTTP/3 task completes without application reconnect, manual retry, or checksum failure |
| Deployment maturity | Migration remains valid across LB/CDN/proxy/client-policy layers |

### Wording to Avoid

Avoid:

- "guarantees"
- "works on all mobile networks"
- "works in Chrome"

Use instead:

- "preserved under controlled conditions"
- "observed under AWS NLB `TCP_QUIC :443` passthrough"
- "browser/Cronet policy remains future work"

## 4.3 Related Work

### Categories

| Category | Sources | Role |
| --- | --- | --- |
| Standards | RFC 9000, RFC 9308, RFC 9312 | CID, path validation, manageability |
| Internet-wide measurement | An Analysis of QUIC Connection Migration in the Wild | anchor for uneven support |
| Mobile handover | mQUIC, EnCoR | mobility and application continuity context |
| Middlebox/proxy | When QUIC CM Meets Middleboxes, HAProxy docs | deployment paths can break migration |
| Load balancing | QUIC-LB draft, AWS NLB docs/blog | CID-aware routing requirement |
| Observability | qlog/qvis, qlog schema | need for endpoint evidence |
| Browser/client policy | Android Cronet, Chromium source | client policy is a separate layer |
| Security/manageability | QUIC-Exfil, QUICstep, MIMIQ | operational reluctance and policy sensitivity |

### Gap Statement

> Prior work has studied QUIC connection migration from the perspectives of protocol behavior, Internet-wide support, mobile handover, middleboxes, and multipath extensions. However, implementation primitives, CID-aware load balancing, CDN/proxy termination, browser policy, and application workload continuity have not been connected in a single validation framework.

## 4.4 Implementation Maturity Survey

### Purpose

Determine whether connection migration exists in implementations, and classify how mature that support is.

### Evaluation Axes

| Axis | Question |
| --- | --- |
| Mechanism | Active migration, passive rebinding, preferred address |
| Control API | Can a researcher or application trigger migration? |
| Observability | qlog, PathEvent, NetLog, callbacks |
| Test coverage | Success/failure/edge-case tests |
| Deployment readiness | CID length, CID generation, LB compatibility |
| HTTP/3 usability | Can it be connected to an HTTP/3 workload? |

### Implementation Roles

| Implementation/environment | Role in paper | Current interpretation |
| --- | --- | --- |
| quic-go | active migration baseline | L4 testable maturity |
| quiche | PathEvent/qlog lifecycle evidence | L4 observability evidence |
| picoquic | edge-case maturity baseline | L4 edge-case evidence |
| s2n-quic | AWS/CID provider candidate | L4, AWS L5 candidate |
| ngtcp2 | RFC guardrail baseline | L4 |
| Quinn/Neqo/aioquic | additional evidence | L3-L4 |
| MsQuic/mvfst | production/deployment evidence | source evidence |
| HAProxy | HTTP/3 != CM negative control | L1-L2 |
| Chromium/Cronet | future browser/client target | client-runtime evidence |

### Section Conclusion

> Connection migration is implemented and tested in several stacks. However, API exposure, observability, preferred-address support, and deployment readiness are uneven, and testable transport maturity does not imply deployable HTTP/3 continuity.

## 4.5 Experimental Design

### Overall Experiment Chain

```text
Implementation survey
  -> local implementation tests
  -> EC2 direct-origin positive control
  -> HAProxy HTTP/3 negative control
  -> AWS NLB CID-aware deployment control
  -> HTTP/3 post-migration request workload
  -> HTTP/3 mid-flight upload/download workload
```

### Experiment Purposes

| Experiment | Purpose | Why it matters |
| --- | --- | --- |
| quic-go local direct-origin | minimum active migration reproduction | confirms controllability |
| quiche path-event timeline | migration lifecycle observability | enables event/qlog explanation |
| EC2 direct-origin | public cloud direct-path positive control | isolates transport success |
| HAProxy HTTP/3 | negative control | separates HTTP/3 support from CM support |
| AWS NLB QUIC | CID-aware routing validation | tests LB deployment condition |
| AWS NLB negative controls | failure condition validation | validates CID/Server ID sensitivity |
| AWS NLB `TCP_QUIC :443` | realistic port/protocol repeat | avoids custom high-port limitation |
| HTTP/3 workload | application task extension | connects transport to HTTP/3 |
| mid-flight workload | migration during body transfer | closest controlled task-continuity evidence |

## 4.6 Results

### Result 1. CM primitives exist in implementations

Evidence:

- quic-go local direct-origin PASS.
- quiche path-event timeline PASS.
- picoquic migration edge-case tests PASS.
- s2n-quic migration tests PASS.
- aioquic/ngtcp2/Quinn/Neqo related tests PASS.

Interpretation:

> Connection migration is not merely specified but absent from implementations. Several stacks expose testable transport primitives and observability hooks.

### Result 2. Direct-origin active migration succeeds

EC2 direct-origin:

| Item | Value |
| --- | --- |
| status | PASS |
| implementation | quic-go |
| source tuple change | `211.60.158.133:64273 -> 211.60.158.133:58085` |
| workload | before/after 1MiB stream payload |
| evidence | qlog PATH_CHALLENGE/PATH_RESPONSE, pcap, JSON |

Interpretation:

> Later proxy/LB/CDN failures should not be attributed to the absence of a transport primitive.

### Result 3. HTTP/3 support is not CM support

HAProxy:

| Item | Value |
| --- | --- |
| status | PASS_NEGATIVE_CONTROL |
| baseline HTTP/3 | success |
| active migration | failure |
| PATH_CHALLENGE | 3 |
| PATH_RESPONSE | 0 |
| final state | `validation_state=Failed` |

Interpretation:

> HTTP/3 endpoint availability does not imply connection migration support.

### Result 4. AWS NLB preserves continuity under CID-aware conditions

AWS NLB QUIC data-plane:

| Item | Value |
| --- | --- |
| status | PASS |
| protocol | `QUIC` |
| port | `4242` |
| successful target | target-b |
| source tuple | `211.60.158.133:55957 -> 211.60.158.133:59355` |
| workload | before/after 64KiB stream |

AWS NLB `TCP_QUIC :443` repeat:

| Item | Value |
| --- | --- |
| status | PASS |
| protocol | `TCP_QUIC` |
| port | `443` |
| successful target | target-b |
| source tuple | `211.60.158.133:57897 -> 211.60.158.133:56632` |
| workload | before/after 64KiB stream |

Required CID format:

```text
0x00 + 8-byte Server ID + 7-byte nonce
```

Interpretation:

> Load-balanced QUIC migration can work, but the CID format and registered `QuicServerId` must match exactly.

### Result 5. Incorrect CID conditions fail

Negative controls:

| Condition | Result | Meaning |
| --- | --- | --- |
| malformed CID layout | expected failure | CloudWatch unknown Server ID drops |
| explicit Server ID mismatch | expected failure | target health 2/2, but handshake/application failure |

Role in paper:

- Strengthens the conditional nature of the positive NLB result.
- Prevents the incorrect interpretation that enabling QUIC or HTTP/3 is sufficient.

### Result 6. HTTP/3 post-migration request continuity is preserved

Local:

| Item | Value |
| --- | --- |
| status | PASS |
| workload | POST `/upload` before -> migration -> GET `/download` after |
| source tuple | `127.0.0.1:63819 -> 127.0.0.1:63361` |

AWS NLB:

| Item | Value |
| --- | --- |
| status | PASS |
| protocol | `TCP_QUIC :443` |
| successful target | target-a |
| source tuple | `211.60.158.133:54110 -> 211.60.158.133:50930` |
| workload | before POST `/upload`, after GET `/download` |

Interpretation:

> Under controlled conditions, transport continuity can be lifted to HTTP/3 request continuity.

### Result 7. HTTP/3 mid-flight body transfers are preserved under controlled conditions

Local mid-flight:

| workload | status | socket A | socket B | final addr | evidence |
| --- | --- | --- | --- | --- | --- |
| upload | PASS | `[::]:53663` | `[::]:63569` | `[::]:63569` | server decoded 1MiB upload |
| download | PASS | `[::]:49959` | `[::]:52767` | `[::]:52767` | client decoded 1MiB response |

AWS NLB mid-flight:

| workload | status | target | socket A | socket B | evidence |
| --- | --- | --- | --- | --- | --- |
| upload | PASS | target-a | `[::]:56276` | `[::]:52824` | target decoded 1MiB upload |
| download | PASS | target-b | `[::]:61456` | `[::]:63381` | client decoded 1MiB streaming response |

Important observation:

> In mid-flight cases, `conn.LocalAddr()` immediately after `path.Switch()` may still show socket A. The final address changed to socket B after subsequent packet exchange. Therefore, success should be judged using final address, qlog path validation, and payload integrity together.

## 5. Tables and Figures

### Figure 1. Layered Research Model

```text
QUIC implementation primitive
  -> testable active migration
  -> direct-origin transport continuity
  -> CID-aware deployment continuity
  -> HTTP/3 request continuity
  -> HTTP/3 mid-flight task continuity
  -> browser/mobile real-world continuity
```

### Figure 2. Experimental Architecture

```text
client socket A/B
      |
      | QUIC / HTTP/3
      v
Direct origin / HAProxy / AWS NLB
      |
      v
target A/B or origin
```

### Figure 3. Migration Lifecycle

```text
new path observed
  -> PATH_CHALLENGE
  -> PATH_RESPONSE
  -> path validated
  -> active path switched
```

### Table 1. Implementation Maturity

Columns:

- implementation
- active migration API
- passive rebinding
- observability
- test coverage
- deployment implication
- role in this study

### Table 2. Experiment Summary

Columns:

- experiment
- environment
- protocol
- migration trigger
- result
- key evidence
- interpretation

### Table 3. AWS NLB Positive/Negative Controls

Columns:

- CID condition
- registered Server ID
- result
- target health
- application payload
- interpretation

### Table 4. HTTP/3 Workload Continuity

Columns:

- workload
- local result
- AWS NLB result
- payload size
- final socket change
- integrity check

## 6. Discussion Plan

### 6.1 Why is connection migration not commonly used?

The answer is not simply "because it is not implemented."

Layered reasons:

| Layer | Why it is difficult |
| --- | --- |
| Implementation | APIs, preferred address, observability, and tests differ by stack |
| Client/browser | OS events, default network, cellular cost, and battery policy influence migration |
| CDN/proxy | HTTP/3 may terminate at the edge or proxy |
| Load balancer | backend affinity may be lost after 5-tuple changes |
| CID routing | CID format, Server ID, and routing table must match |
| Observability | QUIC encryption makes pcap-only root cause analysis insufficient |
| Application | upload/download/dashboard tasks can fail independently of transport |
| Security/manageability | migration and preferred address interact with exfiltration, censorship, tracking, and middlebox policy |

### 6.2 What the AWS NLB results mean

What can be claimed:

- CID-aware migration behind a load balancer is possible.
- AWS NLB `TCP_QUIC :443` preserved HTTP/3 request and mid-flight workload continuity in controlled experiments.
- CID format and registered `QuicServerId` are core conditions.

What cannot be claimed:

- It works automatically for all NLB/QUIC servers.
- It works end-to-end through CloudFront/CDN origins.
- It works in Chrome/Android under real handover.

### 6.3 Current scope of web task continuity

Evidence chain already established:

```text
custom transport stream continuity
  -> AWS NLB CID-aware transport continuity
  -> HTTP/3 post-migration request continuity
  -> controlled HTTP/3 mid-flight body continuity
```

Remaining chain:

```text
browser/Cronet policy
  -> real Wi-Fi/LTE handover
  -> real web application fetch/upload/download/dashboard behavior
  -> user-visible continuity
```

## 7. Limitations

### 7.1 Controlled migration vs. real handover

The current experiments use controlled source-port migration or a secondary UDP socket. Real Wi-Fi-to-cellular handover includes interface change, routing table change, carrier NAT, radio delay, and OS default-network selection.

### 7.2 quic-go-centered experiments

quic-go is suitable because its active migration API is explicit, but it does not represent all implementations.

### 7.3 AWS NLB specificity

AWS NLB `TCP_QUIC :443` is a specific CID-aware deployment path. The result does not automatically generalize to other cloud load balancers, CDNs, or reverse proxies.

### 7.4 Browser policy not yet validated

Chrome/Android/Cronet workload experiments are not yet complete. Therefore, the paper must not claim real mobile browser task continuity.

### 7.5 Limited application workloads

Current workloads are deterministic upload/download. Dashboard polling, SSE, WebSocket, WebTransport, service workers, and UI recovery remain future work.

## 8. Follow-up Experiment Plan

### 8.1 CloudFront viewer-edge limited control

Goal:

- Separate CloudFront HTTP/3 connection migration as viewer-edge continuity from origin end-to-end continuity.

Architecture:

```text
client
  -> HTTP/3
  -> CloudFront edge
  -> origin
```

Measurements:

- Whether the client uses HTTP/3 to CloudFront.
- Whether origin logs can observe the client QUIC connection.
- Request/download continuity during network change.

Expected paper role:

> CDN migration support should be interpreted as viewer-edge continuity unless origin end-to-end QUIC continuity is explicitly observed.

### 8.2 Cronet/Android workload

Goal:

- Determine how real client policy differs from controlled quic-go behavior.

Workloads:

- large upload,
- streaming download,
- dashboard polling or SSE-like update.

Conditions:

- HTTP/2 baseline,
- HTTP/3 direct origin,
- HTTP/3 AWS NLB,
- HTTP/3 CloudFront.

Measurements:

- task success/failure,
- retry count,
- stall time,
- recovery time,
- Android network callback,
- Cronet NetLog,
- server qlog.

## 9. Final Conclusion Plan

The paper should conclude:

1. Connection migration is not absent from implementations.
2. Several QUIC stacks already have testable transport maturity.
3. HTTP/3 endpoint support is not the same as connection migration support.
4. CID-aware routing is a core deployment condition.
5. AWS NLB `TCP_QUIC :443` preserved HTTP/3 request and mid-flight body continuity under the correct CID format condition.
6. Browser/mobile handover claims require additional Cronet/Chrome and real handover experiments.

Final one-sentence conclusion:

> QUIC connection migration can work, but HTTP/3 web task continuity is preserved only when implementation maturity, deployment routing, client policy, observability, and application semantics align.
