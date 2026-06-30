# Chapter 1 Reference And Scanner Evidence

작성일: `2026-06-30`

이 문서는 Chapter 1 구현체 성숙도 조사에서 사용한 실제 참고 링크와 scanner trigger 맥락을 한 곳에 모은 검증 부록이다. 목적은 “QUIC Connection Migration이 구현체에 어느 정도 구현되어 있다”는 주장을 환각 없이 추적 가능하게 만드는 것이다.

## 1. 기준 문서

| 구분 | 링크 | 사용한 이유 |
| --- | --- | --- |
| QUIC RFC | [RFC 9000: QUIC: A UDP-Based Multiplexed and Secure Transport](https://datatracker.ietf.org/doc/html/rfc9000) | Connection ID, path validation, connection migration, `disable_active_migration`, preferred address의 기준 문서 |
| HTTP/3 RFC | [RFC 9114: HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114) | HTTP/3가 QUIC 위에서 동작한다는 전제와 웹 실험 해석 기준 |
| QUIC WG 구현체 목록 | [quicwg/base-drafts wiki: Implementations](https://github.com/quicwg/base-drafts/wiki/Implementations) | 조사 대상 seed 목록 |
| QUIC WG 구현체 원본 목록 | [quicwg.github.io implementations.md](https://github.com/quicwg/quicwg.github.io/blob/main/implementations.md) | wiki와 함께 구현체 후보를 교차 확인 |
| 핵심 참고 논문 | [ACM DOI: 10.1145/3727063.3727066](https://dl.acm.org/doi/10.1145/3727063.3727066) | 최신 관련 연구 기준점. 로컬 PDF: `/Users/manwook-han/Desktop/lab/3727063.3727066.pdf` |
| curl 이슈 | [curl/curl#7695](https://github.com/curl/curl/issues/7695) | HTTP/3 지원과 Connection Migration 지원이 동일하지 않다는 반례성 근거 |

## 2. 구현체별 공식 링크

| 우선순위 | 대상 | 공식/source 링크 | Chapter 1에서 본 관점 |
| ---: | --- | --- | --- |
| 1 | quic-go | [GitHub](https://github.com/quic-go/quic-go), [Connection Migration 문서](https://quic-go.net/docs/quic/connection-migration/) | active migration positive control |
| 2 | Cloudflare quiche | [GitHub](https://github.com/cloudflare/quiche), [docs.rs quiche](https://docs.rs/quiche/latest/quiche/) | path event와 HTTP/3 실험 baseline |
| 3 | AWS s2n-quic | [GitHub](https://github.com/aws/s2n-quic), [공식 문서](https://aws.github.io/s2n-quic/) | AWS/NLB 후보와 library maturity |
| 4 | ngtcp2 | [GitHub](https://github.com/ngtcp2/ngtcp2), [공식 사이트](https://nghttp2.org/ngtcp2/) | C library/tooling 비교군 |
| 5 | LiteSpeed lsquic | [GitHub](https://github.com/litespeedtech/lsquic), [LiteSpeed LSQUIC official page](https://www.litespeedtech.com/open-source/quic-http3-library) | 서버 구현체와 preferred address/migration 근거 |
| 6 | MsQuic | [GitHub](https://github.com/microsoft/msquic), [공식 문서](https://microsoft.github.io/msquic/) | Microsoft ecosystem과 deployment 문서 |
| 7 | Quinn | [GitHub](https://github.com/quinn-rs/quinn), [docs.rs quinn](https://docs.rs/quinn/latest/quinn/) | Rust implementation 비교군 |
| 8 | Neqo | [GitHub](https://github.com/mozilla/neqo) | Mozilla implementation 비교군 |
| 9 | XQUIC | [GitHub](https://github.com/alibaba/xquic) | Alibaba implementation, NAT rebinding/migration evidence |
| 10 | Chromium/Cronet | [Chromium source](https://chromium.googlesource.com/chromium/src/), [Android Cronet ConnectionMigrationOptions](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions) | Chrome/Android browser runtime 정책 확인 |
| 11 | AWS CloudFront | [CloudFront HTTP/3 announcement](https://aws.amazon.com/blogs/aws/new-http-3-support-for-amazon-cloudfront/), [CloudFront supported HTTP versions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html#DownloadDistValuesSupportedHTTPVersions) | viewer-edge HTTP/3. end-to-end CM과 구분 필요 |
| 12 | AWS NLB + s2n-quic | [NLB QUIC announcement](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/), [NLB listener docs](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-listeners.html) | passthrough QUIC와 CID routing 실험 후보 |
| 13 | mvfst | [GitHub](https://github.com/facebook/mvfst) | 대규모 production-oriented QUIC stack |
| 14 | picoquic | [GitHub](https://github.com/private-octopus/picoquic) | edge-case test가 풍부한 연구/interop 구현체 |
| 15 | nginx QUIC | [GitHub mirror](https://github.com/nginx/nginx), [NGINX HTTP/3 docs](https://nginx.org/en/docs/http/ngx_http_v3_module.html) | server-side passive migration/web server 근거 |
| 16 | quicly | [GitHub](https://github.com/h2o/quicly) | H2O 계열 C implementation 비교군 |
| 17 | aioquic | [GitHub](https://github.com/aiortc/aioquic), [공식 문서](https://aioquic.readthedocs.io/) | Python readable reference, path validation test |
| 18 | HAProxy QUIC | [GitHub](https://github.com/haproxy/haproxy), [HAProxy HTTP/3 docs](https://www.haproxy.com/documentation/haproxy-configuration-tutorials/protocol-support/http/) | proxy 반례. HTTP/3 proxy 지원과 CM 지원을 분리 |

Apple/Safari는 실험 대상 browser로는 볼 수 있지만, Apple QUIC implementation은 비공개라 source/test/qlog 기반 구현체 성숙도 audit 대상에서는 제외했다.

## 3. Scanner Trigger 위치

scanner 결과는 별도 표로 분리했다.

- scanner 결과 표: [tables/scanner-trigger-summary-20260630.md](tables/scanner-trigger-summary-20260630.md)
- 외부 링크 검수 표: [tables/chapter-01-external-link-check-20260630.md](tables/chapter-01-external-link-check-20260630.md)
- scanner source: [tools/scan_implementation_evidence.py](../../tools/scan_implementation_evidence.py)

이번 재실행에서는 다음 15개 공개 repository를 shallow clone하고 같은 scanner를 돌렸다.

| 포함됨 | repository |
| --- | --- |
| yes | quic-go, quiche, s2n-quic, picoquic, ngtcp2, Quinn, Neqo, aioquic |
| yes | lsquic, MsQuic, XQUIC, HAProxy, mvfst, nginx, quicly |
| no | Chromium/Cronet, AWS CloudFront, AWS NLB |

Chromium/Cronet은 전체 source clone 비용이 크고 browser runtime 정책 확인이 핵심이라 공식 source/docs 링크로 별도 추적한다. AWS CloudFront와 AWS NLB는 managed service라 repository scanner 대상이 아니다.

## 4. Scanner가 실제로 본 패턴

`tools/scan_implementation_evidence.py`의 category별 trigger는 다음이다.

| category | trigger keyword/pattern | 해석 |
| --- | --- | --- |
| `path_validation` | `PATH_CHALLENGE`, `PATH_RESPONSE`, `path validation`, `path_validat`, `ErrPathNotValidated` | RFC 9000 path validation primitive 후보 |
| `active_migration_api` | `AddPath`, `Probe(`, `Switch(`, `path.Probe`, `path.Switch`, `migrate_source`, `perform_migration`, `active migration`, `probe_path` | active migration API 또는 internal path switching 후보 |
| `passive_rebinding` | `NAT rebinding`, `rebinding`, `peer address`, `remote address`, `address change`, `tuple change` | NAT rebinding/tuple change handling 후보 |
| `disable_migration_policy` | `disable_active_migration`, `DisableActiveMigration`, `disable migration`, `migration disabled` | migration 정책/비활성화 transport parameter 후보 |
| `preferred_address` | `preferred address`, `preferred_address`, `PreferredAddress` | server preferred address 관련 후보 |
| `cid_and_load_balancing` | `ConnectionIDGenerator`, `connection id generator`, `QuicServerId`, `Server ID`, `QUIC-LB`, `load balanc`, `Connection ID` | CID와 load balancing 배포 근거 후보 |
| `observability` | `qlog`, `PathEvent`, `NetLog`, `tracing`, `event::`, `path event` | qlog/log/event/tracing 근거 후보 |
| `tests` | `migration.*test`, `test.*migration`, `path.*test`, `rebinding.*test` | test coverage 후보 |

주의할 점은 scanner가 conformance test가 아니라 keyword first-pass라는 것이다. 예를 들어 `Switch(` 같은 trigger는 QUIC migration과 무관한 일반 switch 함수에도 걸릴 수 있다. 그래서 scanner 결과는 “성숙도 판정”이 아니라 “수동 검토를 시작할 파일/라인 후보”로만 사용했다.

## 5. 재현 명령

아래는 scanner 결과를 다시 만들기 위한 최소 절차다. commit은 매 실행 시점의 `main` 또는 default branch에 따라 달라질 수 있으므로, 논문 최종본에서는 `tables/scanner-trigger-summary-20260630.md`의 commit hash를 함께 고정해서 인용해야 한다.

```bash
mkdir -p /tmp/quic-cm-scan-repos
git clone --depth 1 https://github.com/quic-go/quic-go.git /tmp/quic-cm-scan-repos/quic-go
git clone --depth 1 https://github.com/cloudflare/quiche.git /tmp/quic-cm-scan-repos/quiche
git clone --depth 1 https://github.com/aws/s2n-quic.git /tmp/quic-cm-scan-repos/s2n-quic
git clone --depth 1 https://github.com/private-octopus/picoquic.git /tmp/quic-cm-scan-repos/picoquic
git clone --depth 1 https://github.com/ngtcp2/ngtcp2.git /tmp/quic-cm-scan-repos/ngtcp2
git clone --depth 1 https://github.com/quinn-rs/quinn.git /tmp/quic-cm-scan-repos/quinn
git clone --depth 1 https://github.com/mozilla/neqo.git /tmp/quic-cm-scan-repos/neqo
git clone --depth 1 https://github.com/aiortc/aioquic.git /tmp/quic-cm-scan-repos/aioquic
git clone --depth 1 https://github.com/litespeedtech/lsquic.git /tmp/quic-cm-scan-repos/lsquic
git clone --depth 1 https://github.com/microsoft/msquic.git /tmp/quic-cm-scan-repos/msquic
git clone --depth 1 https://github.com/alibaba/xquic.git /tmp/quic-cm-scan-repos/xquic
git clone --depth 1 https://github.com/haproxy/haproxy.git /tmp/quic-cm-scan-repos/haproxy
git clone --depth 1 https://github.com/facebook/mvfst.git /tmp/quic-cm-scan-repos/mvfst
git clone --depth 1 https://github.com/nginx/nginx.git /tmp/quic-cm-scan-repos/nginx
git clone --depth 1 https://github.com/h2o/quicly.git /tmp/quic-cm-scan-repos/quicly
```

```bash
python3 tools/scan_implementation_evidence.py \
  /tmp/quic-cm-scan-repos/quic-go \
  /tmp/quic-cm-scan-repos/quiche \
  /tmp/quic-cm-scan-repos/s2n-quic \
  /tmp/quic-cm-scan-repos/picoquic \
  /tmp/quic-cm-scan-repos/ngtcp2 \
  /tmp/quic-cm-scan-repos/quinn \
  /tmp/quic-cm-scan-repos/neqo \
  /tmp/quic-cm-scan-repos/aioquic \
  /tmp/quic-cm-scan-repos/lsquic \
  /tmp/quic-cm-scan-repos/msquic \
  /tmp/quic-cm-scan-repos/xquic \
  /tmp/quic-cm-scan-repos/haproxy \
  /tmp/quic-cm-scan-repos/mvfst \
  /tmp/quic-cm-scan-repos/nginx \
  /tmp/quic-cm-scan-repos/quicly \
  --format csv --max-examples 3
```

## 6. 검증 순서

검토자 또는 제3자가 hallucination 여부를 점검하려면 다음 순서로 보면 된다.

1. RFC 9000에서 connection migration/path validation/transport parameter 개념을 확인한다.
2. `data/implementation-survey.csv`에서 내가 어떤 구현체를 어떤 level로 분류했는지 본다.
3. [tables/scanner-trigger-summary-20260630.md](tables/scanner-trigger-summary-20260630.md)에서 해당 구현체의 category별 trigger 위치를 연다.
4. 원본 source/test 링크를 직접 읽어 scanner hit가 실제 CM evidence인지, 단순 keyword false positive인지 구분한다.
5. `docs/results/local-implementation-test-results.md`에서 실제 빌드/테스트까지 수행한 8개 구현체 결과를 확인한다.
6. Chromium/Cronet, AWS CloudFront/NLB는 구현체 source scanner가 아니라 runtime/managed service 문서와 실제 실험 결과로 따로 판단한다.

## 7. 현재 문서의 한계

- scanner trigger 표는 각 category당 최대 3개 example link만 남긴다. 전체 match line을 모두 복사하지 않은 이유는 외부 source code를 대량 복제하지 않기 위해서다.
- match count는 연구 결론이 아니다. 특히 `cid_and_load_balancing`, `observability`, `tests`는 generic keyword가 많아 false positive가 생길 수 있다.
- active migration maturity는 “API 존재 여부”, “probe/switch state machine”, “qlog/event”, “test”, “HTTP/3 continuity”를 함께 봐야 한다.
- browser-level Chrome/Safari 결과는 library scanner 결과와 별도로 해석해야 한다.
