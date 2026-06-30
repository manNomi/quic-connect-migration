# Chapter 4 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 4 “배포 경로 검수”의 실제 구현 코드, run script, 결과 문서, 공식 cloud/proxy/CDN reference link를 정리한다. 공개 안전성을 위해 공인 IP, NLB hostname, EC2 instance ID, AWS account ID, SSH target은 포함하지 않는다.

## 1. 현재 repo의 구현/실행 근거

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| AWS NLB CID generator | [repro/quic-go-min-repro/internal/common/aws_nlb_cid.go](../../repro/quic-go-min-repro/internal/common/aws_nlb_cid.go) | `0x00 + 8-byte Server ID + 7-byte nonce` CID 생성 |
| CID unit test | [repro/quic-go-min-repro/internal/common/aws_nlb_cid_test.go](../../repro/quic-go-min-repro/internal/common/aws_nlb_cid_test.go) | CID length, config byte, Server ID placement, nonce uniqueness 검증 |
| NLB data-plane harness | [harness/scripts/run-aws-nlb-quic-data-plane.sh](../../harness/scripts/run-aws-nlb-quic-data-plane.sh) | temporary NLB/target/EC2 생성, package deploy, positive/negative run, cleanup |
| s2n NLB live readiness gate | [harness/scripts/check-s2n-nlb-live-readiness.sh](../../harness/scripts/check-s2n-nlb-live-readiness.sh) | AWS identity, local s2n CID provider proof, live runner readiness를 public-safe로 분리 |
| s2n NLB live runner | [harness/scripts/run-aws-s2n-nlb-live-data-plane.sh](../../harness/scripts/run-aws-s2n-nlb-live-data-plane.sh) | AWS identity가 유효할 때만 EC2 target A/B, NLB, QUIC target registration, s2n echo client를 실행; 현재 invalid token이면 resource 생성 전 blocked |
| s2n NLB live server/client | [experiments/s2n-quic-nlb-cid-provider/src/bin](../../experiments/s2n-quic-nlb-cid-provider/src/bin) | `nlb_live_server`, `nlb_live_client`, `generate_localhost_cert`로 live runner binary 구성 |
| package script | [harness/scripts/package-quic-go-ec2.sh](../../harness/scripts/package-quic-go-ec2.sh) | EC2 target에 올릴 repro package 생성 |
| EC2 bootstrap | [repro/quic-go-min-repro/scripts/ec2-bootstrap-go.sh](../../repro/quic-go-min-repro/scripts/ec2-bootstrap-go.sh) | EC2 target에서 Go runtime 준비 |
| transport server | [repro/quic-go-min-repro/cmd/server/main.go](../../repro/quic-go-min-repro/cmd/server/main.go) | AWS NLB CID generator를 quic-go transport에 연결 |
| H3 server | [repro/quic-go-min-repro/cmd/h3server/main.go](../../repro/quic-go-min-repro/cmd/h3server/main.go) | HTTP/3 upload/download workload |
| H3 client | [repro/quic-go-min-repro/cmd/h3client/main.go](../../repro/quic-go-min-repro/cmd/h3client/main.go) | HTTP/3 before/after 또는 mid-flight workload와 path switch |
| HAProxy negative-control runner | [harness/scripts/run-haproxy-http3-negative-control.sh](../../harness/scripts/run-haproxy-http3-negative-control.sh) | HAProxy ordinary H3 baseline과 active migration failure를 재현 |
| nginx quic_bpf readiness gate | [harness/scripts/check-nginx-quic-bpf-readiness.sh](../../harness/scripts/check-nginx-quic-bpf-readiness.sh) | local nginx runtime demo와 Linux/eBPF production-routing claim을 분리 |
| OpenLiteSpeed runtime preflight | [harness/scripts/openlitespeed-runtime-preflight.sh](../../harness/scripts/openlitespeed-runtime-preflight.sh) | OpenLiteSpeed production-like runtime demo를 실행하기 전 local gate 확인 |
| OpenLiteSpeed active migration runner | [harness/scripts/run-openlitespeed-active-migration-demo.sh](../../harness/scripts/run-openlitespeed-active-migration-demo.sh) | Linux/EC2에서 OpenLiteSpeed minimal server root, quiche active migration, server/client path evidence 검증 |
| Artifact storage report | [tools/report_artifact_storage.py](../../tools/report_artifact_storage.py) | ignored raw artifact roots와 현재 free space를 삭제 없이 측정 |
| Artifact cleanup safety audit | [tools/audit_artifact_cleanup_safety.py](../../tools/audit_artifact_cleanup_safety.py) | CSV-referenced/planned artifact를 보호하고 review-unreferenced 후보만 분리 |
| Artifact cleanup dry-run planner | [tools/plan_artifact_cleanup.py](../../tools/plan_artifact_cleanup.py) | 실제 삭제 없이 OpenLiteSpeed build 전 확보 가능한 free space를 계산 |
| deployment trigger map | [tables/chapter-04-scanner-trigger-map-20260630.md](tables/chapter-04-scanner-trigger-map-20260630.md) | CID generator, NLB harness, H3 workload, false-positive guard line anchor |
| OpenLiteSpeed feasibility audit | [docs/results/openlitespeed-quic-cm-source-feasibility-20260630.md](../results/openlitespeed-quic-cm-source-feasibility-20260630.md) | LSQUIC example demo를 production-like server 실험으로 확장하기 위한 source-level 사전 검수 |

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
| OpenLiteSpeed source | [litespeedtech/openlitespeed](https://github.com/litespeedtech/openlitespeed) | LSQUIC 기반 production-like HTTP/3 server follow-up target |
| OpenLiteSpeed docs | [OpenLiteSpeed documentation](https://openlitespeed.org/kb/) | 설치/운영 경로 공식 문서 entry point |
| LiteSpeed QUIC/HTTP3 setup reference | [LiteSpeed QUIC/HTTP3 guide](https://docs.litespeedtech.com/lsws/cp/cpanel/quic-http3/) | HTTP/3/QUIC가 HTTPS/UDP/listener 설정과 연결된다는 운영 참고 |
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
| [docs/results/s2n-quic-nlb-cid-provider-rerun-20260630.md](../results/s2n-quic-nlb-cid-provider-rerun-20260630.md) | s2n-quic custom CID provider 복원/rerun, AWS NLB deployment prerequisite |
| [docs/results/s2n-nlb-live-readiness-20260630.md](../results/s2n-nlb-live-readiness-20260630.md) | live AWS NLB+s2n 전제 조건 gate; local proof PASS, dedicated s2n runner ready, AWS identity invalid |
| [docs/results/aws-s2n-nlb-live-runner-20260630.md](../results/aws-s2n-nlb-live-runner-20260630.md) | dedicated AWS NLB+s2n live runner, local binary smoke, current fail-closed blocked artifact |
| [docs/results/aws-nlb-http3-workload-results-20260624.md](../results/aws-nlb-http3-workload-results-20260624.md) | HTTP/3 POST-before / migration / GET-after workload |
| [docs/results/haproxy-http3-negative-control-results-20260623.md](../results/haproxy-http3-negative-control-results-20260623.md) | HTTP/3 proxy support != active CM support negative control |
| [docs/results/haproxy-http3-negative-control-rerun-20260630.md](../results/haproxy-http3-negative-control-rerun-20260630.md) | HAProxy HTTP/3 negative-control fresh rerun with reproducible runner |
| [docs/results/nginx-haproxy-quic-cm-boundary-20260630.md](../results/nginx-haproxy-quic-cm-boundary-20260630.md) | nginx server passive migration source evidence와 HAProxy proxy negative-control boundary |
| [docs/results/nginx-quic-bpf-readiness-20260630.md](../results/nginx-quic-bpf-readiness-20260630.md) | nginx local runtime demo와 Linux `quic_bpf` production-routing 검증을 분리하는 readiness gate |
| [docs/results/openlitespeed-quic-cm-source-feasibility-20260630.md](../results/openlitespeed-quic-cm-source-feasibility-20260630.md) | OpenLiteSpeed source-level production-like follow-up feasibility; runtime CM proof는 아직 아님 |
| [docs/results/openlitespeed-runtime-preflight-20260630.md](../results/openlitespeed-runtime-preflight-20260630.md) | OpenLiteSpeed runtime demo readiness gate; latest local result `runtime_ready=no` |
| [docs/results/openlitespeed-active-migration-runner-20260630.md](../results/openlitespeed-active-migration-runner-20260630.md) | OpenLiteSpeed Linux/EC2 runtime runner와 현재 macOS local `missing-openlitespeed-binary` blocked result |
| [docs/results/artifact-storage-report-20260630-openlitespeed-preflight.md](../results/artifact-storage-report-20260630-openlitespeed-preflight.md) | OpenLiteSpeed runtime 전 local artifact roots total `35.3GiB`, current free `20.57GiB` |
| [docs/results/artifact-cleanup-safety-audit-20260630-openlitespeed-preflight.md](../results/artifact-cleanup-safety-audit-20260630-openlitespeed-preflight.md) | review-unreferenced cleanup candidates `92`, reclaimable `7.1GiB`, protected referenced/planned artifact `25.8GiB` |
| [docs/results/artifact-cleanup-dry-run-20260630-openlitespeed-preflight.md](../results/artifact-cleanup-dry-run-20260630-openlitespeed-preflight.md) | deletion-free cleanup dry-run; projected free `27.7GiB`, still `2.3GiB` short of 30GiB target |
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

s2n NLB live readiness:

| evidence | 의미 |
| --- | --- |
| local s2n CID provider proof `PASS` | s2n endpoint에 AWS NLB-compatible CID provider를 주입할 수 있음 |
| local echo `echo_matches=yes` | provider가 설치된 local s2n endpoint가 application echo workload를 완료 |
| dedicated live runner ready | s2n target A/B를 EC2에 배포하고 NLB `QuicServerId` registration 후 echo를 실행할 code path가 준비됨 |
| local live binary smoke PASS | 새 `nlb_live_server`/`nlb_live_client`가 같은 certificate/CID-provider 전제로 echo를 완료 |
| AWS identity `invalid_client_token` | current host에서 live AWS resource 생성/삭제를 실행하면 안 됨 |
| live AWS run `validation=blocked` | runner는 resource 생성 전에 fail-closed로 중단됨 |

HAProxy negative control:

| evidence | 의미 |
| --- | --- |
| ordinary H3 request PASS | endpoint/proxy가 HTTP/3 자체는 지원 |
| no-migration quiche request PASS | client/proxy basic interop은 됨 |
| migration attempt path validation FAIL | HTTP/3 support가 active CM support를 의미하지 않음 |
| client qlog `path_challenge=3`, `path_response=0` | path validation failure 근거 |

OpenLiteSpeed local runtime readiness:

| evidence | 의미 |
| --- | --- |
| source feasibility PASS | OpenLiteSpeed가 LSQUIC HTTP/3 server engine, QUIC config, CID/SHM routing hook을 갖는 production-like follow-up target임 |
| runtime preflight `runtime_ready=no` | 현재 macOS local host는 submodule/binary/Linux-style `/dev/shm`/disk gate가 닫혀 있음 |
| artifact storage total `35.3GiB` | OpenLiteSpeed build 전 raw artifact storage pressure가 실험 진행 조건에 영향을 줌 |
| cleanup dry-run projected free `27.7GiB` | 안전 후보만 삭제해도 30GiB local build target에는 부족하므로 Linux/EC2 또는 archive 정책이 필요 |
| active migration runner added | Linux/EC2에서 config test, ordinary HTTP/3 completion, active migration path evidence를 하나의 packet으로 검증 가능 |
| local runner result `blocked` | 현재 macOS local host에는 OpenLiteSpeed binary가 없어 runtime success/failure claim을 만들지 않음 |

nginx/HAProxy boundary:

| evidence | 의미 |
| --- | --- |
| nginx `ngx_event_quic_migration.c` | server-side passive migration, NAT rebinding, path validation source flow 존재 |
| nginx `quic_bpf` official docs | packet routing과 migration support가 서버 배포 조건과 연결됨 |
| HAProxy official docs | HTTP/3 support가 있어도 HAProxy current docs는 connection migration 미지원 boundary를 명시 |
| HAProxy source handler/counter | 관련 코드 primitive는 있으므로 "구현 코드가 전혀 없음"이 아니라 "지원 claim을 제한해야 함"으로 해석 |
| nginx `quic_bpf` readiness `linux_required` | local runtime success와 Linux/eBPF production packet-routing claim을 분리 |

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
