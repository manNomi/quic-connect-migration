# Controlled public application H3 evidence gate

작성일: 2026-06-24

## 1. 목적

public third-party endpoint 실험에서 `dns_alpn_h3` discovery job과 application HTTP/3 evidence를 분리해야 한다는 점이 확인됐다. 따라서 Chrome/Cronet handover 실험으로 넘어가기 전, 연구자가 제어하는 public WebPKI origin에서 application HTTP/3 no-change baseline을 먼저 증명하는 gate가 필요하다.

이 단계는 handover 실험이 아니다. 다음 handover 실험의 전제 조건을 검증하는 evidence gate다.

## 2. 추가한 도구

파일:

- `tools/classify_controlled_public_h3_baseline.py`

입력 artifact:

| 입력 | 경로 |
| --- | --- |
| server result | `results/server.json` |
| server metadata | `results/server-public-origin-metadata.json` |
| server qlog | `qlog/*` |
| public readiness | `results/public-origin-readiness.json` |
| Chrome public summary | `results/chrome-public-h3-summary.json` |

## 3. 판정 기준

application H3 baseline은 다음을 함께 봐야 한다.

| evidence | 기준 |
| --- | --- |
| server request log | expected request count 이상 도달 |
| server qlog | `chosen_alpn > 0` and `http3_frame > 0` |
| Chrome NetLog | application `using_quic` job이 있으면 강한 browser-side evidence |
| readiness | DNS/TLS/HTTPS와 `Alt-Svc: h3`가 정상 |

Chrome NetLog가 discovery 수준에 머물러도, controlled server의 request log와 qlog가 application H3를 직접 증명하면 baseline은 통과로 분류한다. 반대로 `dns_alpn_h3` discovery만 있고 server qlog가 application H3를 보이지 않으면 통과시키지 않는다.

## 4. Wrapper 연결

`repro/quic-go-min-repro/scripts/run-controlled-public-h3-browser-baseline.sh`는 같은 artifact directory에 `results/server.json`이 있거나 `CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR`가 지정되면 combined classifier를 자동 실행한다.

결과 파일:

```text
results/controlled-public-h3-baseline-summary.json
```

## 5. Local regression check

public domain/certificate가 아직 없는 상태에서도 classifier 자체는 기존 local artifact로 회귀 검수했다.

| artifact | status | classification | 의미 |
| --- | --- | --- | --- |
| `chrome-h3-sequence-vtime-pass` | `PASS_FEASIBILITY` | `controlled_public_server_qlog_h3_confirmed_browser_summary_missing` | server request 3개, qlog `chosen_alpn=1`, `http3_frame=11`; public browser summary는 없는 local forced-H3 회귀 검수 |
| `chrome-h3-alt-svc-html-local-20260624` | `PASS_NEGATIVE_CONTROL` | `controlled_public_application_h3_not_confirmed` | server request 4개 모두 `HTTP/1.1`, qlog `chosen_alpn=0`, `http3_frame=1`; H3 candidate만으로는 application H3가 아님 |

이 결과는 classifier가 application H3 evidence와 H1-only Alt-Svc candidate를 구분한다는 sanity check다.

## 6. 다음 실행 조건

실제 controlled public baseline을 실행하려면 다음이 필요하다.

1. public DNS hostname
2. WebPKI certificate/key
3. UDP 443과 TCP 443 inbound 허용
4. 같은 artifact directory에서 server wrapper와 browser wrapper 실행
5. `controlled-public-h3-baseline-summary.json`의 `status=PASS`

이 gate가 통과한 뒤에만 active interface/network change 실험으로 넘어간다.
