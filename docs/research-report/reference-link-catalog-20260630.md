# Reference Link Catalog

작성일: `2026-06-30`

이 문서는 연구 보고용 폴더의 외부 참고자료를 한 곳에 모은 검증 인덱스다. 목적은 검토자 또는 제3자가 "이 주장은 실제 문서/논문/소스 링크에 기대고 있는가"를 빠르게 확인하게 만드는 것이다.

원칙:

1. 이 카탈로그는 claim을 새로 만들지 않는다.
2. 각 링크가 무엇을 지지하는지와 무엇을 지지하지 않는지는 챕터별 부록에서 확인한다.
3. 구현체 source line trigger는 코드 복사가 아니라 원본 GitHub line anchor로 추적한다.
4. 외부 링크 상태는 각 챕터의 `external-link-check` 표에 남긴다. ACM DOI처럼 `curl -L -I`에서 `403`이 나는 링크는 publisher 접근 정책으로 분리하고, 가능한 경우 arXiv mirror를 함께 둔다.

## 1. Standards And Protocol References

| reference | link | 사용 챕터 | 사용 맥락 |
| --- | --- | --- | --- |
| QUIC transport | [RFC 9000](https://datatracker.ietf.org/doc/html/rfc9000) | Chapter 1-12 | Connection ID, path validation, NAT rebinding, active migration, `disable_active_migration` 기준 |
| HTTP/3 | [RFC 9114](https://datatracker.ietf.org/doc/html/rfc9114) | Chapter 1, 2, 5-12 | application HTTP/3 baseline과 browser workload 해석 |
| HTTP semantics | [RFC 9110](https://datatracker.ietf.org/doc/html/rfc9110), [Range Requests](https://datatracker.ietf.org/doc/html/rfc9110#name-range-requests) | Chapter 9, 10 | byte-range resume와 upload/request semantics |
| QUIC applicability | [RFC 9308](https://datatracker.ietf.org/doc/html/rfc9308) | Chapter 2, 12 | deployment caveat, UDP/NAT/manageability friction |
| QUIC manageability | [RFC 9312](https://datatracker.ietf.org/doc/html/rfc9312) | Chapter 2, 12 | middlebox/monitoring/operational caution |
| QUIC-LB | [draft-ietf-quic-load-balancers](https://datatracker.ietf.org/doc/html/draft-ietf-quic-load-balancers) | Chapter 2, 4 | CID-aware routing and load-balancer boundary |
| Multipath QUIC | [draft-ietf-quic-multipath](https://datatracker.ietf.org/doc/draft-ietf-quic-multipath/) | Chapter 12 | future path-management scope. 현재 browser single-path CM 성공 근거로 쓰지 않음 |
| qlog schema | [qlog main schema](https://quicwg.org/qlog/draft-ietf-quic-qlog-main-schema.html) | Chapter 2, 5-11 | qlog path/application evidence 해석 |

## 2. QUIC Implementation And Source References

| target | link | 사용 챕터 | 검증 방식 |
| --- | --- | --- | --- |
| QUIC WG implementation seed | [base-drafts wiki implementations](https://github.com/quicwg/base-drafts/wiki/Implementations), [quicwg.github.io implementations.md](https://github.com/quicwg/quicwg.github.io/blob/main/implementations.md) | Chapter 1 | 조사 대상 seed |
| quic-go | [GitHub](https://github.com/quic-go/quic-go), [Connection Migration docs](https://quic-go.net/docs/quic/connection-migration/), [HTTP/3 server docs](https://quic-go.net/docs/http3/server/), [qlog docs](https://quic-go.net/docs/quic/qlog/) | Chapter 1, 3, 6-12 | source scanner, local positive control, H3 server/qlog |
| Cloudflare quiche | [GitHub](https://github.com/cloudflare/quiche), [docs.rs](https://docs.rs/quiche/latest/quiche/), [Connection API](https://docs.rs/quiche/latest/quiche/struct.Connection.html) | Chapter 1-3 | source scanner and implementation comparison |
| AWS s2n-quic | [GitHub](https://github.com/aws/s2n-quic), [official docs](https://aws.github.io/s2n-quic/) | Chapter 1, 3, 4 | source scanner and AWS deployment candidate |
| ngtcp2 | [GitHub](https://github.com/ngtcp2/ngtcp2), [official site](https://nghttp2.org/ngtcp2/) | Chapter 1, 3 | source scanner and C library comparison |
| LiteSpeed lsquic | [GitHub](https://github.com/litespeedtech/lsquic), [official LSQUIC page](https://www.litespeedtech.com/open-source/quic-http3-library) | Chapter 1 | source scanner and server-side QUIC comparison |
| MsQuic | [GitHub](https://github.com/microsoft/msquic), [docs](https://microsoft.github.io/msquic/), [deployment docs](https://microsoft.github.io/msquic/msquicdocs/docs/Deployment.html) | Chapter 1-3 | source scanner and production stack comparison |
| Quinn | [GitHub](https://github.com/quinn-rs/quinn), [docs.rs](https://docs.rs/quinn/latest/quinn/) | Chapter 1, 3 | source scanner and Rust implementation comparison |
| Neqo | [GitHub](https://github.com/mozilla/neqo) | Chapter 1, 3 | source scanner and Mozilla-adjacent stack |
| XQUIC | [GitHub](https://github.com/alibaba/xquic) | Chapter 1 | source scanner and implementation comparison |
| mvfst | [GitHub](https://github.com/facebook/mvfst) | Chapter 1 | source scanner and production-oriented stack |
| picoquic | [GitHub](https://github.com/private-octopus/picoquic) | Chapter 1, 3 | source scanner and edge-case comparison |
| nginx QUIC | [GitHub mirror](https://github.com/nginx/nginx), [NGINX HTTP/3 module](https://nginx.org/en/docs/http/ngx_http_v3_module.html) | Chapter 1 | source scanner and web server comparison |
| quicly | [GitHub](https://github.com/h2o/quicly) | Chapter 1 | source scanner and C implementation comparison |
| aioquic | [GitHub](https://github.com/aiortc/aioquic), [docs](https://aioquic.readthedocs.io/) | Chapter 1, 3 | source scanner and Python reference |
| HAProxy QUIC | [GitHub](https://github.com/haproxy/haproxy), [HTTP/3 docs](https://www.haproxy.com/documentation/haproxy-configuration-tutorials/protocol-support/http/), [configuration manual](https://docs.haproxy.org/3.2/configuration.html) | Chapter 1, 2, 4 | proxy negative control and source scanner |
| curl issue | [curl/curl#7695](https://github.com/curl/curl/issues/7695) | Chapter 1 | HTTP/3 support and CM support are not equivalent |

Line-level implementation scanner results are in:

- [tables/scanner-trigger-summary-20260630.md](tables/scanner-trigger-summary-20260630.md)

## 3. Browser, Runtime, And Web Platform References

| reference | link | 사용 챕터 | 사용 맥락 |
| --- | --- | --- | --- |
| Chromium NetLog guide | [Providing Network Details for bug reports](https://www.chromium.org/for-testers/providing-network-details/) | Chapter 5-11 | Chrome NetLog capture method |
| Chromium NetLog events | [net_log_event_type_list.h](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h) | Chapter 2, 5-11 | QUIC/session/network event interpretation |
| Chromium QUIC context | [quic_context.h](https://chromium.googlesource.com/chromium/src/+/master/net/quic/quic_context.h) | Chapter 1, 2, 5, 12 | Chromium QUIC runtime/policy source |
| Chromium QUIC client session | [quic_chromium_client_session.h](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/net/quic/quic_chromium_client_session.h) | Chapter 2, 5 | browser session/policy source evidence |
| Cronet config source | [url_request_context_config.cc](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/cronet/url_request_context_config.cc) | Chapter 5 | Cronet policy and Chrome browser distinction |
| Android Cronet CM options | [ConnectionMigrationOptions](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions), [Android platform builder](https://developer.android.com/reference/android/net/http/ConnectionMigrationOptions.Builder) | Chapter 1, 2, 5, 12 | runtime policy knobs. Browser success proof로 쓰지 않음 |
| Safari WebDriver | [WebKit Safari WebDriver](https://webkit.org/blog/6900/webdriver-support-in-safari-10/), [Selenium Safari docs](https://www.selenium.dev/documentation/webdriver/browsers/safari/), [W3C WebDriver](https://www.w3.org/TR/webdriver2/) | Chapter 5 | automation feasibility, not QUIC session evidence |
| Chrome DevTools Protocol | [Page domain](https://chromedevtools.github.io/devtools-protocol/tot/Page/), [Runtime domain](https://chromedevtools.github.io/devtools-protocol/tot/Runtime/) | Chapter 8-11 | navigation and DOM dataset collection |
| Fetch and Streams | [Fetch Standard](https://fetch.spec.whatwg.org/), [Streams Standard](https://streams.spec.whatwg.org/) | Chapter 8-11 | browser fetch/upload/download/media workload semantics |

## 4. Deployment, Cloud, CDN, And Certificate References

| reference | link | 사용 챕터 | 사용 맥락 |
| --- | --- | --- | --- |
| AWS NLB QUIC support | [AWS NLB QUIC announcement](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/) | Chapter 2, 4, 12 | CID-aware managed deployment axis |
| AWS NLB docs | [NLB introduction](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html), [listener docs](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-listeners.html), [target registration](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/target-group-register-targets.html) | Chapter 1, 2, 4 | QUIC/NLB deployment and target routing |
| AWS Load Balancer Controller | [QUIC use case guide](https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/use_cases/quic/) | Chapter 4 | QUIC-LB plaintext CID deployment example |
| AWS CloudFront HTTP/3 | [CloudFront HTTP/3 announcement](https://aws.amazon.com/blogs/aws/new-http-3-support-for-amazon-cloudfront/), [supported HTTP versions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html#DownloadDistValuesSupportedHTTPVersions), [UpdateDistribution API](https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_UpdateDistribution.html) | Chapter 1, 2, 4 | CDN edge H3 and origin/end-to-end CM boundary |
| Cloudflare HTTP/3 | [Cloudflare HTTP/3 docs](https://developers.cloudflare.com/speed/optimization/protocol/http3/) | Chapter 1, 2, 4 | CDN edge support boundary |
| AWS security groups | [VPC security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) | Chapter 7 | public origin TCP/UDP 443 access precondition |
| Let's Encrypt | [Getting Started](https://letsencrypt.org/getting-started/) | Chapter 7 | WebPKI public-origin certificate preparation |

## 5. Paper And Measurement References

| source_id | link | 사용 챕터 | 사용 맥락 |
| --- | --- | --- | --- |
| `ccr2025-wild-cm` | [ACM DOI](https://dl.acm.org/doi/10.1145/3727063.3727066), [arXiv mirror](https://arxiv.org/abs/2410.06066) | Chapter 1, 2, 12 | primary related work and support unevenness anchor |
| `qlog-qvis` | [ACM DOI](https://doi.org/10.1145/3404868.3406663) | Chapter 2 | qlog/qvis observability motivation |
| `quicstep-2026` | [PoPETs page](https://petsymposium.org/popets/2026/popets-2026-0014.php) | Chapter 2, 12 | CM support measurement and security/privacy sensitivity |
| `mimiq` | [USENIX FOCI 2020](https://www.usenix.org/conference/foci20/presentation/govil) | Chapter 2 | migration/privacy/security discussion |
| `quic-exfil-2025` | [arXiv](https://arxiv.org/abs/2505.05292) | Chapter 2, 12 | preferred-address misuse and operational caution |
| `qasm-2026` | [arXiv](https://arxiv.org/abs/2602.03354) | Chapter 2, 12 | QUIC-aware middlebox/manageability friction |
| `secure-middlebox-quic` | [arXiv](https://arxiv.org/abs/2307.08543) | Chapter 2 | middlebox-assisted QUIC background |
| `encor-2026` | [arXiv HTML](https://arxiv.org/html/2605.22524v2) | Chapter 2, 12 | mobile handover/application continuity motivation |
| `swiftshift-2026` | [ACM DOI](https://dl.acm.org/doi/10.1145/3798065.3798080) | Chapter 2, 11, 12 | media/QoE migration motivation |
| `video-over-quic` | [arXiv](https://arxiv.org/abs/2505.21769) | Chapter 2, 11 | video streaming over QUIC context |
| `pcm-quic` | [Wiley DOI](https://onlinelibrary.wiley.com/doi/10.1002/nem.70022) | Chapter 2 | performance/QoE related work |
| `measuring-http3` | [arXiv](https://arxiv.org/abs/2102.12358) | Chapter 2 | HTTP/3 adoption is not CM adoption |
| `quic-hunter` | [project page](https://zirngibl.github.io/publication/2024-03-11-QUIC-Hunter-Finding-QUIC-Deployments-and-Identifying-Server-Libraries-Across-the-Internet) | Chapter 2 | Internet-scale QUIC measurement context |

## 6. Link Check Evidence

Catalog-level quick check:

```text
2026-06-30: 81 URLs checked with curl -L -I
ok_or_redirect=77
blocked_or_method_limited=4
warning=0
```

| chapter | link-check table | note |
| --- | --- | --- |
| Chapter 2 | [tables/chapter-02-external-link-check-20260630.md](tables/chapter-02-external-link-check-20260630.md) | friction/reference links |
| Chapter 3 | [tables/chapter-03-external-link-check-20260630.md](tables/chapter-03-external-link-check-20260630.md) | implementation positive-control links |
| Chapter 4 | [tables/chapter-04-external-link-check-20260630.md](tables/chapter-04-external-link-check-20260630.md) | AWS/HAProxy/CDN links |
| Chapter 5 | [tables/chapter-05-external-link-check-20260630.md](tables/chapter-05-external-link-check-20260630.md) | browser/runtime links |
| Chapter 6 | [tables/chapter-06-external-link-check-20260630.md](tables/chapter-06-external-link-check-20260630.md) | local Chrome/NAT rebinding links |
| Chapter 7 | [tables/chapter-07-external-link-check-20260630.md](tables/chapter-07-external-link-check-20260630.md) | public origin/baseline links |
| Chapter 8 | [tables/chapter-08-external-link-check-20260630.md](tables/chapter-08-external-link-check-20260630.md) | downlink handover links |
| Chapter 9 | [tables/chapter-09-external-link-check-20260630.md](tables/chapter-09-external-link-check-20260630.md) | byte-range/retry links |
| Chapter 10 | [tables/chapter-10-external-link-check-20260630.md](tables/chapter-10-external-link-check-20260630.md) | upload links |
| Chapter 11 | [tables/chapter-11-external-link-check-20260630.md](tables/chapter-11-external-link-check-20260630.md) | streaming/media links |
| Chapter 12 | [tables/chapter-12-external-link-check-20260630.md](tables/chapter-12-external-link-check-20260630.md) | literature positioning links |

## 7. Claim Boundary For References

| link type | 이 링크로 말할 수 있는 것 | 이 링크만으로 말하면 안 되는 것 |
| --- | --- | --- |
| RFC | QUIC/HTTP/3의 표준 primitive와 terminology | Chrome/Safari가 우리 handover scenario에서 single-session CM 성공했다 |
| implementation docs/source | 특정 stack에 primitive/test/API/hook이 존재한다 | browser web workload continuity가 자동으로 보장된다 |
| browser runtime docs | Chrome/Cronet/Safari automation or policy가 존재한다 | runtime이 실제 live web session을 migration했다 |
| cloud/CDN docs | HTTP/3, QUIC-aware routing, edge support가 존재한다 | origin까지 end-to-end CM이 보장된다 |
| papers | research gap, related work, threat model, QoE metric을 정당화한다 | 우리 실험에서 관찰되지 않은 결과를 대신 증명한다 |
