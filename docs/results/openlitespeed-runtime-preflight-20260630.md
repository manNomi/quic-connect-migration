# OpenLiteSpeed Runtime Preflight

작성일: `2026-06-30`

## 1. 목적

이 문서는 OpenLiteSpeed production-like HTTP/3 Connection Migration runtime demo를 현재 로컬 환경에서 바로 실행할 수 있는지 확인한 preflight 결과다.

이 preflight는 다음을 하지 않는다.

| 하지 않는 일 | 이유 |
| --- | --- |
| OpenLiteSpeed build | 현재 디스크 여유가 낮고 source submodule이 준비되지 않음 |
| `lshttpd` 실행 | local OpenLiteSpeed binary가 없음 |
| Connection Migration 성공 판정 | runtime HTTP/3 server와 active migration을 실행하지 않았음 |

## 2. 실행 명령

```bash
harness/scripts/openlitespeed-runtime-preflight.sh
```

최신 실행 artifact:

```text
harness/results/openlitespeed-runtime-preflight-20260630T120037Z
```

## 3. 최신 결과 요약

```text
run_id=openlitespeed-runtime-preflight-20260630T120037Z
system_name=Darwin
system_machine=arm64
disk_free_gib=19.58
min_disk_gib=30
openlitespeed_commit=f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379
lsquic_commit_pointer=f8ebaf838d2f4db836bda1182ee35b05d5191cee
local_lsquic_commit=f8ebaf838d2f4db836bda1182ee35b05d5191cee
source_ready=yes
source_feature_ready=yes
lsquic_pointer_ready=yes
local_lsquic_match=yes
submodule_ready=no
binary_ready=no
quiche_ready=yes
build_tools_ready=yes
linux_recommended_ready=no
dev_shm_ready=no
disk_ready=no
lseng_http_server_count=1
quic_enable_count=2
scid_callback_count=3
cid_pid_count=46
runtime_ready=no
next_action=free-disk-or-use-linux-ec2-before-openlitespeed-build
openlitespeed_runtime_preflight=blocked
```

## 4. 판정표

| Gate | 결과 | 해석 |
| --- | --- | --- |
| OpenLiteSpeed source clone | PASS | source audit와 runtime follow-up 설계 가능 |
| Source feature files | PASS | CMake/config/src/quic 핵심 파일 존재 |
| `LSQUICCOMMIT` present | PASS | OpenLiteSpeed가 가리키는 LSQUIC commit 확인 |
| local LSQUIC matches pointer | PASS | 현재 검수한 LSQUIC commit과 OpenLiteSpeed pointer 일치 |
| quiche client ready | PASS | active migration client candidate 존재 |
| build tools ready | PASS | `cmake`, `make`, compiler 존재 |
| OpenLiteSpeed submodule ready | FAIL | shallow clone에 `src/liblsquic` 없음 |
| OpenLiteSpeed binary ready | FAIL | local `lshttpd`/`openlitespeed` 없음 |
| Linux recommended runtime | FAIL | 현재 환경은 `Darwin arm64` |
| `/dev/shm` ready | FAIL | OpenLiteSpeed default `quicShmDir /dev/shm` 경로가 macOS에 없음 |
| disk ready | FAIL | 19.58GiB < 30GiB |
| runtime ready | FAIL | 위 gate가 닫혀 runtime demo 보류 |

## 5. 해석

현재 로컬 환경은 OpenLiteSpeed runtime demo를 바로 실행하기에는 준비되지 않았다. 하지만 이것은 OpenLiteSpeed가 CM을 지원하지 않는다는 결과가 아니다.

안전한 해석:

> OpenLiteSpeed is still a valid production-like follow-up target because the source-level LSQUIC/HTTP/3 integration gates are present, but the current local runtime environment is not ready for a publishable migration demo.

한국어 표현:

> OpenLiteSpeed는 LSQUIC 기반 production-like 후속 실험 대상으로는 타당하지만, 현재 macOS 로컬 환경에서는 submodule/binary/Linux shared-memory/disk gate가 닫혀 있어 runtime Connection Migration 검증을 진행하지 않는다.

## 6. 다음 조치

| 우선순위 | 조치 | 이유 |
| ---: | --- | --- |
| 1 | Linux VM 또는 EC2에서 OpenLiteSpeed source/submodule 준비 | `/dev/shm`, UDP packet info, `sendmmsg` 경로가 production 조건에 가까움 |
| 2 | local artifact cleanup 후 최소 30GiB 이상 확보 | build/log/qlog 여유 확보 |
| 3 | `lshttpd -v`와 LSQUIC commit을 artifact로 고정 | runtime 결과의 구현 버전 추적 |
| 4 | quiche no-migration baseline 실행 | ordinary H3 success와 CM success를 분리 |
| 5 | quiche active migration 실행 | `PATH_CHALLENGE`/`PATH_RESPONSE`, final path state, 1MiB response completion 확인 |

## 7. Claim boundary

쓸 수 있는 주장:

> The OpenLiteSpeed runtime preflight identified concrete gates required before a production-like CM demo: OpenLiteSpeed binary/submodule readiness, Linux-style shared-memory support, sufficient disk, and quiche active-migration client availability.

쓰면 안 되는 주장:

| 금지 claim | 이유 |
| --- | --- |
| OpenLiteSpeed에서 CM이 실패했다 | runtime migration을 실행하지 않았음 |
| OpenLiteSpeed에서 CM이 성공했다 | runtime migration을 실행하지 않았음 |
| macOS preflight 결과가 Linux production behavior를 대표한다 | 현재 결과는 local readiness gate일 뿐임 |
