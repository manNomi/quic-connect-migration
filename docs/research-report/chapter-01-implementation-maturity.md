# Chapter 1. QUIC Connection Migration 구현체 성숙도 조사

작성일: `2026-06-30`

## 1. 이 챕터의 목적

이 챕터의 목적은 단순히 “어떤 QUIC 구현체가 유명한가”를 나열하는 것이 아니다. 교수님 피드백의 첫 번째 논점은 다음이었다.

> Connection Migration이 왜 안 쓰이는지를 논하려면, 먼저 그 기술이 실제 구현체에 구현되어 있는지 확인해야 한다.

따라서 Chapter 1의 핵심 질문은 다음 하나로 시작했다.

> QUIC Connection Migration은 실제 구현체 수준에서 어느 정도 구현되어 있고, 실험자가 검증 가능한가?

이 질문을 먼저 해결해야 이후 연구 질문이 정리된다. 만약 구현체에 CM이 거의 없다면 연구는 “미구현 기술의 도입 가능성”에 가까워진다. 반대로 구현체에는 있는데 브라우저나 배포 경로에서 잘 보이지 않는다면 연구는 “구현체 성숙도와 실제 웹 배포 사이의 gap”을 다루게 된다.

현재까지의 결론은 두 번째에 가깝다.

> QUIC Connection Migration은 주요 구현체에 아예 없는 기술이 아니다. 다만 구현체마다 지원 범위, API 노출 수준, 관찰성, test coverage, deployment readiness가 다르다.

## 2. 조사 대상 선정

조사 대상은 QUIC WG의 구현체 목록을 출발점으로 삼았다.

- `https://github.com/quicwg/base-drafts/wiki/Implementations`
- `https://github.com/quicwg/quicwg.github.io/blob/main/implementations.md`

공식 링크와 scanner trigger 위치는 별도 검증 부록에 정리했다.

- `docs/research-report/chapter-01-reference-and-scanner-evidence.md`
- `docs/research-report/tables/scanner-trigger-summary-20260630.md`

다만 이 목록은 “known QUIC implementations” 목록이지, Connection Migration 지원 여부를 직접 알려주는 표가 아니다. 그래서 목록을 seed로 사용하고, 실제 연구 relevance를 기준으로 18개 구현체/스택을 다시 골랐다.

최종 대상은 다음 범주로 나누었다.

| 범주 | 대상 | 선정 이유 |
| --- | --- | --- |
| 실험 baseline | quic-go, Cloudflare quiche, picoquic, s2n-quic | 직접 빌드/테스트가 가능하고 migration evidence를 얻기 좋음 |
| library/tooling 비교군 | ngtcp2, Quinn, Neqo, aioquic, quicly | RFC primitive, path validation, migration test 비교에 적합 |
| production/server 계열 | MsQuic, lsquic, nginx QUIC, mvfst, XQUIC | 실제 배포 또는 대규모 서비스 relevance가 있음 |
| browser/runtime | Chromium/Cronet | Chrome/Android browser behavior와 직접 연결됨 |
| managed deployment | AWS CloudFront, AWS NLB + s2n-quic | CDN/LB에서 end-to-end CM 해석이 달라질 수 있음 |
| proxy 반례 | HAProxy QUIC | HTTP/3 proxy 지원이 CM 지원과 같지 않다는 반례 |

Apple 구현체는 최종 표에서 제외했다. 이유는 비공개 구현체라 source/test/qlog 기반으로 성숙도를 검수하기 어렵기 때문이다. 논문에서는 Safari 실험을 할 수는 있지만, Apple QUIC 구현체 자체의 내부 성숙도 audit로 다루기는 어렵다.

## 3. 무엇을 확인했는가

각 구현체에서 본 항목은 다음과 같다.

| 확인 항목 | 질문 | 왜 중요한가 |
| --- | --- | --- |
| RFC primitive | `PATH_CHALLENGE`, `PATH_RESPONSE`, CID, transport parameter가 있는가? | RFC 9000 수준의 path validation 기반이 있는지 확인 |
| passive migration | NAT rebinding, peer address change, tuple change를 처리하는가? | 실제 네트워크에서는 NAT rebinding이 흔하게 발생함 |
| active migration API | client가 새 path를 추가/probe/switch할 수 있는가? | 실험자가 migration을 의도적으로 재현할 수 있는지 판단 |
| migration policy | `disable_active_migration`이나 runtime option이 있는가? | 구현체가 CM을 항상 켜는 것이 아니라 정책으로 제어할 수 있음 |
| preferred address | server preferred address가 있는가? | migration 관련 기능이지만 client active migration과 구분 필요 |
| CID/load balancing | CID generator, QUIC-LB, Server ID 근거가 있는가? | LB/CDN 환경에서 tuple이 바뀌어도 같은 backend로 가야 함 |
| observability | qlog, PathEvent, NetLog, tracing이 있는가? | 논문에서는 “됐다”보다 “증거를 남길 수 있는가”가 중요 |
| tests | migration/rebinding/path validation test가 있는가? | 구현체 성숙도와 regression coverage 판단 |
| local reproducibility | 실제 빌드/테스트가 가능한가? | source claim을 실행 근거로 보강 |

중요한 구분은 이것이다.

> `PATH_CHALLENGE` frame이 있다고 해서 active migration이 완성된 것은 아니다.

frame encode/decode만 있는 구현체와, 실제 path state machine, API, qlog, test까지 갖춘 구현체는 성숙도가 다르다.

## 4. 성숙도 Level 기준

Chapter 1에서는 구현체 성숙도를 L0-L5로 나누었다.

| Level | 의미 | 연구에서의 용도 |
| --- | --- | --- |
| L0 | CM 관련 근거 없음 | CM 구현체 후보에서 제외 또는 낮은 우선순위 |
| L1 | RFC primitive 일부 있음 | frame/transport parameter 수준의 근거 |
| L2 | NAT rebinding 또는 peer address change 처리 | passive migration 계층 근거 |
| L3 | active migration API 또는 내부 API 존재 | active migration 실험 후보 |
| L4 | test, qlog, event, failure handling 존재 | 구현체 maturity 근거로 사용 가능 |
| L5 | LB/CDN/cloud/production 배포 근거 존재 | deployment discussion 또는 positive control 후보 |

이 기준에서 가장 중요한 경계는 L4와 L5다.

- L4는 구현체 자체가 충분히 검증 가능하다는 뜻이다.
- L5는 실제 배포 경로까지 어느 정도 연결된다는 뜻이다.

따라서 quic-go가 L4라고 해서 Chrome이나 CDN에서 CM이 자동으로 성공한다고 말하면 안 된다. 구현체 성숙도와 브라우저/배포 성숙도는 다른 층이다.

## 5. 조사 절차

조사는 네 단계로 수행했다.

### 5.1 원본 조사표 작성

원본 표는 `data/implementation-survey.csv`에 만들었다. 이 CSV에는 다음 컬럼이 있다.

| 컬럼 | 의미 |
| --- | --- |
| `priority` | 조사 우선순위 |
| `name` | 구현체 또는 배포 스택 이름 |
| `category` | library/server/client/proxy/managed edge 등 |
| `usage_reason` | 연구에서 이 대상을 보는 이유 |
| `rfc_primitives` | RFC primitive 근거 여부 |
| `passive_migration` | NAT rebinding/passive migration 근거 |
| `active_migration_api` | active migration API 근거 |
| `preferred_address` | preferred address 관련 근거 |
| `observability` | qlog/log/Event/NetLog 등 |
| `tests` | 관련 test 존재 여부 |
| `lb_or_cloud_deployability` | LB/CDN/cloud 연결성 |
| `aws_suitability` | AWS 실험과의 연결 가능성 |
| `current_level` | L0-L5 계열 판정 |
| `evidence_status` | source inspected, partial deferred 등 |
| `next_action` | 다음 조사/실험 액션 |

### 5.2 Evidence scanner로 1차 후보 찾기

다음 도구를 사용했다.

```text
tools/scan_implementation_evidence.py
```

이 도구는 clone된 구현체 repository에서 CM 관련 keyword를 category별로 찾는다.

scanner가 보는 주요 category는 다음이다.

| category | 찾는 evidence |
| --- | --- |
| `path_validation` | `PATH_CHALLENGE`, `PATH_RESPONSE`, path validation |
| `active_migration_api` | `AddPath`, `Probe`, `Switch`, `probe_path`, `migrate_source` |
| `passive_rebinding` | NAT rebinding, peer address, remote address change |
| `disable_migration_policy` | `disable_active_migration`, migration disabled |
| `preferred_address` | preferred address |
| `cid_and_load_balancing` | Connection ID generator, QUIC-LB, Server ID |
| `observability` | qlog, PathEvent, NetLog, tracing |
| `tests` | migration/rebinding/path 관련 test |

scanner는 자동 판정기가 아니다. scanner output은 “읽어야 할 파일 후보”를 찾는 용도다. 최종 판정은 source/test/manual run을 통해 사람이 했다.

scanner의 실제 trigger keyword, 실행 명령, 15개 공개 구현체의 commit hash, 파일/라인 링크는 `tables/scanner-trigger-summary-20260630.md`에 고정했다.

### 5.3 Source/test manual audit

scanner로 찾은 파일을 바탕으로 다음을 수동으로 확인했다.

1. primitive가 실제 state machine에 연결되는가?
2. active migration API가 application에서 호출 가능한가?
3. test-only 또는 internal API는 아닌가?
4. path validation 실패가 구분되는가?
5. qlog/event/log가 남는가?
6. HTTP/3 layer와 연결 가능한가?
7. LB/CDN/proxy 배포 경로에서 continuity를 유지할 수 있는가?

### 5.4 Local test 실행

빌드와 테스트가 가능한 구현체는 실제로 실행했다. 실행까지 한 구현체는 8개다.

| 구현체 | 실행한 검수 | 결과 |
| --- | --- | --- |
| quic-go | custom active migration reproduction | PASS |
| Cloudflare quiche | migration tests + sample client/server migration | PASS |
| picoquic | NAT rebinding/migration/preferred-address 등 13개 test | PASS |
| s2n-quic | connection migration tests | PASS |
| aioquic | path challenge/response unit tests | PASS |
| ngtcp2 | client migration/path validation tests | PASS |
| Quinn | migration/rebind tests | PASS |
| Neqo | migration test suite | PASS |

이 local test 결과는 `docs/results/local-implementation-test-results.md`에 정리되어 있다.

## 6. PASS로 인정한 기준

테스트 명령이 0으로 끝났다고 바로 충분한 evidence로 보지는 않았다. 가능하면 다음 중 여러 증거가 함께 있어야 강한 근거로 보았다.

| 증거 | 예시 |
| --- | --- |
| path validation frame | qlog/log의 `PATH_CHALLENGE`, `PATH_RESPONSE` |
| path switch/rebind | source port 또는 local path 변경 |
| payload continuity | before/after payload가 같은 connection flow에서 전달 |
| HTTP/3 continuity | migration 이후 HTTP/3 request/response 완료 |
| negative behavior | probe 전 switch 실패, migration disabled, failed migration |
| observability | qlog, PathEvent, NetLog, tracing, event log |

이 기준 때문에 Chapter 1은 단순 문서 조사가 아니라, “source evidence + test evidence + observability evidence”를 묶은 maturity audit가 되었다.

## 7. 대표 구현체별 해석

### 7.1 quic-go

quic-go는 가장 중요한 active migration positive control이다. 검증 흐름은 다음과 같다.

```text
client UDP socket A로 QUIC 연결
-> before payload 전송
-> UDP socket B 생성
-> conn.AddPath(transport B)
-> path.Switch() before Probe 실패 확인
-> path.Probe() 성공
-> path.Switch() 성공
-> after payload 전송
-> server가 같은 QUIC connection에서 before/after payload 수신
```

중요 근거:

- `Switch()` before `Probe()`가 `path not yet validated`를 반환했다.
- qlog에서 `path_challenge`, `path_response`가 기록됐다.
- migration 이후 payload가 새 socket 경로로 전송됐다.
- client/server result가 모두 `ok: true`였다.

해석:

> quic-go는 실험자가 active migration을 직접 제어할 수 있어 controlled positive control로 적합하다.

주의:

> quic-go에서 된다는 사실은 Chrome browser handover 성공을 의미하지 않는다.

### 7.2 Cloudflare quiche

quiche는 migration lifecycle을 관찰하기 좋은 구현체다.

확인한 것:

- migration library tests
- sample client/server active migration
- server의 new path detection
- `PATH_CHALLENGE` / `PATH_RESPONSE`
- path validated event
- migration 이후 HTTP/3 request/response

해석:

> quiche는 “CM이 내부적으로 어떤 event sequence로 보이는지” 설명하기 좋은 observability baseline이다.

### 7.3 picoquic

picoquic은 edge-case test가 풍부하다.

확인한 것:

- NAT rebinding
- NAT rebinding with loss
- active migration
- migration failure
- false migration
- preferred address
- migration disabled
- probe API

해석:

> picoquic은 production web stack 대표라기보다 CM edge-case maturity 기준선으로 유용하다.

### 7.4 s2n-quic

s2n-quic은 AWS 연구와 연결성이 높다.

확인한 것:

- IP rebind
- port rebind
- IP+port rebind
- blocked migration
- zero-length CID client migration
- `PathChallenge`, `PathResponse`

해석:

> s2n-quic은 AWS/NLB/CID-aware deployment 연구로 이어질 수 있는 후보군이다.

### 7.5 Chromium/Cronet

Chromium/Cronet은 구현체라기보다 browser runtime policy의 핵심 대상이다.

확인한 것:

- migration 관련 runtime policy knob
- Chrome NetLog 관찰 가능성
- Android Cronet migration option

해석:

> Chromium/Cronet에는 migration 관련 policy와 observability 근거가 있지만, 이것이 Chrome browser에서 실제 Wi-Fi/cellular handover 중 single-session CM이 성공했다는 뜻은 아니다.

## 8. 결과 요약

`data/implementation-survey.csv` 기준으로 요약하면 다음과 같다.

| 항목 | 결과 |
| --- | ---: |
| 총 조사 대상 | 18 |
| local test까지 실행한 구현체 | 8 |
| source inspected | 15 |
| source + local browser baseline | 1 |
| partial/deferred | 2 |
| active migration API `yes` | 8 |
| passive migration `yes` | 14 |
| tests `yes` | 14 |
| high AWS suitability | 5 |

이 숫자의 의미는 다음과 같다.

1. CM은 구현체 수준에서는 꽤 넓게 존재한다.
2. passive migration 근거가 active migration API보다 더 넓게 관찰된다.
3. test와 observability가 있는 구현체가 많아 maturity audit 자체는 가능하다.
4. 그러나 production/browser claim은 별도 evidence chain이 필요하다.

## 9. Chapter 1의 결론

Chapter 1의 결론은 다음이다.

> QUIC Connection Migration은 구현체 수준에서 실재하는 기능이다. 주요 구현체 다수는 path validation, NAT rebinding, active/passive migration, qlog/event/test 중 일부 이상을 제공한다. 하지만 구현체 maturity는 browser/runtime/deployment maturity와 다르므로, 다음 단계에서는 왜 이 기능이 실제 웹 브라우저와 배포 환경에서 잘 보이지 않는지 분석해야 한다.

이 결론 때문에 Chapter 2의 질문은 다음으로 바뀌었다.

> 구현체에는 CM primitive와 test가 있는데, 왜 실제 웹에서는 user-visible continuity로 잘 드러나지 않는가?

## 10. 보고 시 강조할 문장

교수님께 설명할 때는 이렇게 말하면 된다.

> 챕터 1에서는 QUIC WG 구현체 목록을 출발점으로 18개 구현체/스택을 선정했고, path validation, NAT rebinding, active migration API, migration policy, preferred address, CID/LB, qlog/event, test 여부를 CSV로 정리했습니다. 이후 scanner로 1차 evidence 후보를 찾고, source/test를 수동 검수했으며, 8개 구현체는 local test까지 실행했습니다. 결론적으로 CM은 구현체 수준에서는 존재하지만, 실제 브라우저나 CDN/LB에서 end-to-end CM으로 보이는지는 별도 문제라서 Chapter 2에서 deployment/runtime friction을 분석하게 되었습니다.

## 11. 연결 문서

| 문서 | 역할 |
| --- | --- |
| `tables/implementation-survey-readable.md` | CSV를 보고용 표로 정리 |
| `../results/chapter1-implementation-maturity-methodology-20260630.md` | Chapter 1 상세 방법론 원본 |
| `../results/local-implementation-test-results.md` | local test 결과 원본 |
| `../results/quic-go-minimum-reproduction-results.md` | quic-go positive control |
| `../results/quiche-path-event-timeline-20260623.md` | quiche migration lifecycle |
| `../results/chaptered-research-synthesis-20260629.md` | 전체 챕터 흐름 |
