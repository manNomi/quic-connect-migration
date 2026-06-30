# Chapter 11. Streaming And Media Workload

작성일: `2026-06-30`

## 1. 이 챕터의 목적

사용자가 처음 제안한 것처럼 Connection Migration은 streaming service에서 특히 중요해 보인다. 다만 streaming은 upload/download보다 해석이 더 어렵다. media playback은 segment fetch, retry, buffer depth, startup delay, rebuffer event, replacement session이 함께 결과를 만든다.

이 챕터의 핵심 질문은 다음이다.

> media workload에서 관찰되는 playback continuity는 transport-level QUIC Connection Migration과 어떻게 분리해서 평가해야 하는가?

현재 Chapter 11의 근거는 local Chrome forced-H3 NAT rebinding controls다. public Wi-Fi to iPhone USB media handover row는 아직 main evidence가 아니다.

## 2. Harness Update

media workload는 두 종류로 추가됐다.

| workload | endpoint | 의미 |
| --- | --- | --- |
| media segment fetch | `GET /browser-media-segments`, `GET /media-segment` | VOD/live/music의 segment request pattern을 단순화 |
| buffered playback | `GET /browser-buffered-media`, `GET /media-segment` | bounded buffer와 playback clock을 둔 player-like model |

수집하는 application fields:

| field group | examples |
| --- | --- |
| segment completion | `mediaCompletedCount`, `mediaComplete`, `mediaBytes`, `mediaRetriesUsed` |
| segment failure | `mediaLastError`, `mediaError`, `mediaErrorElapsedMs` |
| buffer/QoE | `bufferedMediaStartupElapsedMs`, `bufferedMediaRebufferEvents`, `bufferedMediaPlayedCount`, `bufferedMediaComplete` |
| protocol/session | Chrome target QUIC session count, qlog path challenge/response, server request/tuple count |

이 workload는 codec/decoder test가 아니다. network and application recovery model이다.

## 3. Local Smoke 결과

짧은 media segment smoke는 application level에서 성공했지만, no-change 조건에서도 Chrome target QUIC session이 둘로 나뉘었다.

| field | value |
| --- | --- |
| workload | media segment smoke |
| expected requests | 4 |
| server result | 4/4 requests |
| browser application result | `mediaComplete=true`, `mediaCompletedCount=3`, `mediaRetriesUsed=0` |
| protocol result | page and segment fetches used HTTP/3 |
| local classifier | `PASS`, `multiple_quic_sessions_without_network_change` |

이 결과는 media completion을 single-session CM으로 해석하면 안 된다는 첫 경고다.

## 4. Video-Like Segment Replication

| profile | drop window | retry | PASS/runs | media complete | median elapsed ms | Chrome sessions | classification | duplicate segments |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| video-like segments | 3000ms | 0 | 3/3 | 3/3 | 5476 | 2-2 | `nat_rebinding_multiple_quic_sessions` | 0 |
| video-like segments | 6000ms | 0 | 3/3 | 3/3 | 8895 | 2-3 | `nat_rebinding_multiple_quic_sessions` | 2 |

해석:

1. segment-style media workload는 retry 없이도 local disruption을 버텼다.
2. 그러나 모든 row는 multiple target QUIC sessions로 분류됐다.
3. 6000ms row에서는 duplicate segment request도 발생했다.

따라서 video-like completion은 "사용자 관점 segment task continuity"이지 "single-session browser CM success"가 아니다.

## 4.1 Fresh Chrome Desktop Local Media Refresh

2026-06-30에 iPhone 없이 local Chrome forced-H3 media control을 짧게 재실행했다. 조건은 6개 media segment, retry 0, proxy switch after 1s, A-side server return path 3000ms drop 설정이었다.

| field | value |
| --- | --- |
| run | `chrome-desktop-noniphone-media-drop3000-retry0-20260630` |
| status | `PASS` |
| classification | `nat_rebinding_possible_session_continuity` |
| media/application complete | `true` |
| elapsed | `1895ms` |
| server remote tuples | `2` |
| Chrome target QUIC sessions | `1` |
| server qlog PATH_CHALLENGE/PATH_RESPONSE | `1/1` |
| Chrome NetLog target PATH_CHALLENGE/PATH_RESPONSE | `1/1` |
| proxy client packets A/B | `63/24` |

이 row는 앞의 video-like replication과 달리 single target session으로 분류됐다. 따라서 local control 수준에서는 "possible session continuity" 후보로 쓸 수 있다. 그러나 public origin, real interface handover, mobile network transition을 거치지 않았으므로 streaming handover success claim으로 확장하지 않는다.

## 5. Music-Like Segment Control

| profile | drop window | retry | PASS/runs | media complete | median elapsed ms | Chrome sessions | classification |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| music-like segments | 6000ms | 0 | 0/3 | 0/3 | - | 2-2 | `browser_h3_request_failed` |
| music-like segments | 6000ms | 1 | 3/3 | 3/3 | 14076 | 3-3 | `nat_rebinding_multiple_quic_sessions` |
| music-like fresh refresh | 6000ms | 0 | 0/1 | 0/1 | - | 2 | `browser_h3_request_failed` |
| music-like fresh refresh | 6000ms | 1 | 1/1 | 1/1 | 16786 | 3 | `nat_rebinding_multiple_quic_sessions` |

이 결과는 중요한 반례다. 작은 segment나 music-like workload가 자동으로 tolerant한 것은 아니다. retry=0에서는 3/3 실패했고, retry=1에서 3/3 복구됐다. 그러나 복구 mechanism은 여전히 multiple Chrome QUIC sessions였다.

2026-07-01 fresh refresh에서도 같은 방향이 재현됐다. retry=0 row는 첫 segment 이후 DOM task가 실패했고, retry=1 row는 8/8 segment completion으로 회복됐지만 Chrome target QUIC session은 3개였다. 따라서 음악형 streaming completion은 application retry/reconnect 회복으로 해석해야 하며, single-session browser CM 성공으로 쓰면 안 된다.

## 6. Buffered Playback Control

| drop window | retry | startup/max buffer | PASS/runs | playback complete | median startup ms | median elapsed ms | rebuffer events | Chrome sessions | classification |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 3000ms | 0 | 1/1 | 3/3 | 3/3 | 67 | 22128 | 14-14 | 2-2 | `nat_rebinding_multiple_quic_sessions` |
| 3000ms | 0 | 4/6 | 3/3 | 3/3 | 15191 | 23215 | 0-0 | 2-2 | `nat_rebinding_multiple_quic_sessions` |
| 3000ms | 2 | 1/1 | 3/3 | 3/3 | 66 | 12100 | 3-14 | 2-2 | `nat_rebinding_multiple_quic_sessions` |
| 3000ms | 2 | 4/6 | 3/3 | 3/3 | 15177 | 23189 | 0-0 | 2-2 | `nat_rebinding_multiple_quic_sessions` |

buffered playback은 completion만 보면 모두 PASS다. 그러나 QoE는 전혀 다르다.

| buffer policy | 사용자 경험 tradeoff |
| --- | --- |
| low startup buffer | fast startup, many rebuffer events |
| high startup buffer | long startup delay, zero rebuffer events |
| retry enabled | some low-buffer rows reduce elapsed/rebuffer, but sessions remain multiple |

따라서 streaming 연구에서는 "재생 완료" 하나만으로는 부족하다.

## 7. Streaming Claim Boundary

현재 evidence로 쓸 수 있는 주장:

> Local media workload controls show that streaming-style task continuity is shaped by segment granularity, retry, buffering, startup delay, rebuffering, duplicate segment fetches, and Chrome session churn.

아직 쓸 수 없는 주장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| streaming에서 Chrome CM이 성공했다 | current media rows are local proxy controls and multiple-session rows. |
| media completion is transport continuity | completion can be produced by segment retry, duplicate fetch, buffering, or replacement sessions. |
| music-like traffic is always safer | no-retry music-like profile failed 3/3 under 6000ms local loss. |
| buffered playback has no user impact | high buffer removed rebuffering by adding around 15s startup delay. |

## 8. 논문에서의 위치

Chapter 11은 논문의 "왜 workload taxonomy가 필요한가"를 가장 잘 보여준다.

| workload | main metric | hidden cost |
| --- | --- | --- |
| upload | complete, received bytes, retry count | duplicate upload, replacement session, latency |
| full downlink | complete/error, bytes before error | no resume semantics |
| byte-range | complete, completed bytes, retry count | range retry, tuple/session churn |
| media segment | completed segments, elapsed time | duplicate segment, session churn |
| buffered media | playback complete, startup delay, rebuffer events | QoE tradeoff, buffer policy |

## 9. 다음 연구 필요

media는 local controls만으로는 부족하다. 다음 단계는 controlled public origin에서 page-ready media handover를 실행하고, 다음 지표를 같이 수집해야 한다.

1. `mediaComplete` 또는 `bufferedMediaComplete`
2. startup delay
3. rebuffer events
4. retry count
5. duplicate segment requests
6. target Chrome QUIC session count
7. qlog path validation
8. client path change evidence

## 10. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| media completion과 CM success를 분리했는가? | PASS |
| segment retry와 buffering을 별도 mechanism으로 구분했는가? | PASS |
| startup/rebuffer QoE metric을 포함했는가? | PASS |
| local proxy control과 public handover를 구분했는가? | PASS |
| raw public URL/IP를 새 문서에 복사하지 않았는가? | PASS |
| scanner/classifier trigger를 line-level로 문서화했는가? | PASS, `chapter-11-reference-and-evidence.md`와 trigger map 참조 |
