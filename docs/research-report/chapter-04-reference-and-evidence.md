# Chapter 4 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 4 “배포 경로 검수”의 실제 구현 코드, run script, 결과 문서, 공식 cloud/proxy/CDN reference link를 정리한다. 공개 안전성을 위해 공인 IP, NLB hostname, EC2 instance ID, AWS account ID, SSH target은 포함하지 않는다.

## 1. 현재 repo의 구현/실행 근거

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| AWS NLB CID generator | [repro/quic-go-min-repro/internal/common/aws_nlb_cid.go](../../repro/quic-go-min-repro/internal/common/aws_nlb_cid.go) | `0x00 + 8-byte Server ID + 7-byte nonce` CID 생성 |
| CID unit test | [repro/quic-go-min-repro/internal/common/aws_nlb_cid_test.go](../../repro/quic-go-min-repro/internal/common/aws_nlb_cid_test.go) | CID length, config byte, Server ID placement, nonce uniqueness 검증 |
| NLB data-plane harness | [harness/scripts/run-aws-nlb-quic-data-plane.sh](../../harness/scripts/run-aws-nlb-quic-data-plane.sh) | temporary NLB/target/EC2 생성, package deploy, positive/negative run, cleanup |
| package script | [harness/scripts/package-quic-go-ec2.sh](../../harness/scripts/package-quic-go-ec2.sh) | EC2 target에 올릴 repro package 생성 |
| EC2 bootstrap | [repro/quic-go-min-repro/scripts/ec2-bootstrap-go.sh](../../repro/quic-go-min-repro/scripts/ec2-bootstrap-go.sh) | EC2 target에서 Go runtime 준비 |
| transport server | [repro/quic-go-min-repro/cmd/server/main.go](../../repro/quic-go-min-repro/cmd/server/main.go) | AWS NLB CID generator를 quic-go transport에 연결 |
| H3 server | [repro/quic-go-min-repro/cmd/h3server/main.go](../../repro/quic-go-min-repro/cmd/h3server/main.go) | HTTP/3 upload/download workload |
| H3 client | [repro/quic-go-min-repro/cmd/h3client/main.go](../../repro/quic-go-min-repro/cmd/h3client/main.go) | HTTP/3 before/after 또는 mid-flight workload와 path switch |
| deployment trigger map | [tables/chapter-04-scanner-trigger-map-20260630.md](tables/chapter-04-scanner-trigger-map-20260630.md) | CID generator, NLB harness, H3 workload, false-positive guard line anchor |

## 2. 공식 reference links

| source | 링크 | Chapter 4에서의 역할 |
| --- | --- | --- |
| AWS NLB QUIC announcement | [Introducing QUIC Protocol Support for Network Load Balancer](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/) | NLB QUIC/TCP_QUIC support와 Server ID 기반 routing 근거 |
| AWS NLB docs | [What is a Network Load Balancer?](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html) | NLB 동작과 protocol support 공식 문서 |
| AWS target registration | [Register targets for your Network Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/target-group-register-targets.html) | target registration과 QUIC Server ID 관련 운용 근거 |
| AWS Load Balancer Controller QUIC example | [AWS Load Balancer Controller QUIC guide](https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/use_cases/quic/) | QUIC-LB plaintext CID 예시와 Kubernetes deployment reference |
| QUIC-LB draft | [draft-ietf-quic-load-balancers](https://datatracker.ietf.org/doc/html/draft-ietf-quic-load-balancers) | routable QUIC Connection ID 개념 기준 |
| HAProxy docs | [HAProxy configuration manual](https://docs.haproxy.org/3.2/configuration.html) | HTTP/3 over QUIC proxy와 migration support boundary 확인 |
| HAProxy source | [haproxy/haproxy](https://github.com/haproxy/haproxy) | proxy implementation source reference |
| CloudFront HTTP/3 announcement | [New HTTP/3 support for Amazon CloudFront](https://aws.amazon.com/blogs/aws/new-http-3-support-for-amazon-cloudfront/) | viewer-edge HTTP/3 support 근거 |
| CloudFront supported HTTP versions | [CloudFront distribution supported HTTP versions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html#DownloadDistValuesSupportedHTTPVersions) | managed CDN HTTP version configuration 근거 |
| CloudFront API note | [CloudFront UpdateDistribution API](https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_UpdateDistribution.html) | CloudFront HTTP/3 connection migration note 확인 |
| Cloudflare HTTP/3 docs | [Cloudflare HTTP/3 docs](https://developers.cloudflare.com/speed/optimization/protocol/http3/) | user-to-CDN edge H3와 origin 구간 구분 근거 |

## 3. 결과 문서 링크

| 결과 문서 | 의미 |
| --- | --- |
| [docs/results/aws-nlb-quic-data-plane-results-20260624.md](../results/aws-nlb-quic-data-plane-results-20260624.md) | NLB `QUIC` data-plane positive control |
| [docs/results/aws-nlb-quic-negative-control-results-20260624.md](../results/aws-nlb-quic-negative-control-results-20260624.md) | malformed CID / Server ID mismatch negative controls |
| [docs/results/aws-nlb-tcp-quic-443-results-20260624.md](../results/aws-nlb-tcp-quic-443-results-20260624.md) | `TCP_QUIC :443` repeat positive control |
| [docs/results/aws-nlb-http3-workload-results-20260624.md](../results/aws-nlb-http3-workload-results-20260624.md) | HTTP/3 POST-before / migration / GET-after workload |
| [docs/results/haproxy-http3-negative-control-results-20260623.md](../results/haproxy-http3-negative-control-results-20260623.md) | HTTP/3 proxy support != active CM support negative control |
| [docs/results/cm-operational-friction-matrix-20260624.md](../results/cm-operational-friction-matrix-20260624.md) | Chapter 2 friction matrix와 deployment interpretation 연결 |

## 4. Evidence Chain

AWS NLB positive control:

| evidence | 의미 |
| --- | --- |
| backend generated NLB-routable CID | LB가 Server ID를 읽어 target routing 가능 |
| active source-port migration | client path/tuple 변경 |
| qlog path validation | `PATH_CHALLENGE` / `PATH_RESPONSE` 확인 |
| same target before/after payload | migrated path가 같은 logical backend로 유지 |
| HTTP/3 before/after request continuity | transport positive control을 H3 request layer로 확장 |

AWS NLB negative control:

| evidence | 의미 |
| --- | --- |
| malformed CID layout | QUIC support만으로 충분하지 않음 |
| registered Server ID mismatch | target health와 routable CID correctness는 별개 |
| failed application payload or no response | deployment contract 위반 시 continuity 실패 |

HAProxy negative control:

| evidence | 의미 |
| --- | --- |
| ordinary H3 request PASS | endpoint/proxy가 HTTP/3 자체는 지원 |
| no-migration quiche request PASS | client/proxy basic interop은 됨 |
| migration attempt path validation FAIL | HTTP/3 support가 active CM support를 의미하지 않음 |
| client qlog `PATH_RESPONSE=0` | path validation failure 근거 |

## 5. Claim Boundary

쓸 수 있는 주장:

> AWS NLB QUIC/TCP_QUIC can be a deployable positive control for CID-aware Connection Migration when the backend emits the expected routable CID format.

쓸 수 없는 주장:

| 주장 | 이유 |
| --- | --- |
| 모든 AWS HTTP/3 배포에서 CM이 된다 | NLB passthrough와 CloudFront edge termination은 다르다. |
| CloudFront/Cloudflare HTTP/3 support는 origin end-to-end CM이다 | viewer-edge QUIC termination 가능성이 있다. |
| HAProxy가 모든 미래 버전에서 CM을 지원하지 않는다 | tested version/build에 대한 negative control이다. |
| NLB target health는 CM readiness다 | CID layout/Server ID mismatch negative control과 충돌한다. |

## 6. 검수 체크리스트

| 항목 | 판정 | 근거 |
| --- | --- | --- |
| 구현 코드 링크가 있는가? | PASS | CID generator, CID test, NLB harness link |
| 공식 cloud/proxy/CDN 링크가 있는가? | PASS | AWS, QUIC-LB, HAProxy, CloudFront, Cloudflare link |
| positive/negative control을 분리했는가? | PASS | NLB positive, malformed/mismatch negative, HAProxy negative 구분 |
| 민감정보를 새 문서에 복사하지 않았는가? | PASS | IP/hostname/account/instance/SSH target 미기재 |
| claim boundary가 안전한가? | PASS | browser/CDN origin-end-to-end claim 배제 |
