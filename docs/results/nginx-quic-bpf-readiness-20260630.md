# nginx QUIC quic_bpf Readiness

작성일: `2026-06-30`

## 1. 목적

이 문서는 nginx QUIC local runtime demo와 Linux `quic_bpf` production-routing 검증을 분리하기 위한 readiness 결과다.

핵심 경계:

> 이 문서는 nginx `quic_bpf` deployment 성공 결과가 아니다. 현재 단계의 결론은 "nginx source/runtime demo는 준비되어 있지만, 현재 macOS host에서는 Linux/eBPF 기반 `quic_bpf` 검증을 실행할 수 없다"이다.

## 2. 추가한 runner

```bash
harness/scripts/check-nginx-quic-bpf-readiness.sh
```

runner가 확인하는 항목:

| 항목 | 의미 |
| --- | --- |
| nginx source | `quic_bpf` directive/source와 migration file 존재 여부 |
| nginx binary | `--with-http_v3_module` build 여부 |
| runtime demo script | 기존 local nginx active-migration demo runner 존재 여부 |
| Linux host | `quic_bpf` 검증이 Linux/eBPF deployment claim인지 분리 |
| host capability | root/capability와 `/sys/fs/bpf` readiness |

2026-06-30 추가 runner:

```bash
harness/scripts/run-nginx-quic-bpf-linux-demo.sh
```

이 runner는 Linux/root/`/sys/fs/bpf` gate가 열릴 때만 기존 nginx active migration demo를 `NGINX_QUIC_BPF=1`로 실행한다. 이때 nginx config에는 `quic_bpf on;`과 `listen ... quic reuseport`가 추가된다. 현재 macOS local run은 `nginx-quic-bpf-linux-demo-local-blocked-20260630`에서 `validation=blocked`, `blocked_reason=linux_required`로 닫혔다.

## 3. 최신 로컬 실행

Command:

```bash
RUN_ID=nginx-quic-bpf-readiness-local-20260630 \
  harness/scripts/check-nginx-quic-bpf-readiness.sh
```

Result:

```text
run_id=nginx-quic-bpf-readiness-local-20260630
system_name=Darwin
system_machine=arm64
nginx_dir=/private/tmp/quic-cm-scan-repos/nginx
nginx_bin=/private/tmp/quic-cm-scan-repos/nginx/build-quic-runtime/nginx
source_ready=yes
source_has_quic_bpf=yes
source_has_migration_file=yes
runtime_demo_script_ready=yes
linux_ready=no
root_ready=no
sys_fs_bpf_ready=no
nginx_bin_ready=yes
nginx_v3_module_ready=yes
nginx_version_exit=0
can_run_linux_quic_bpf_now=no
blocked_reason=linux_required
```

## 4. 해석

확인된 것:

1. nginx source에는 `quic_bpf` 관련 source/docs 근거가 있다.
2. `ngx_event_quic_migration.c` migration file이 존재한다.
3. 기존 local runtime demo runner는 존재한다.
4. local nginx binary는 `--with-http_v3_module`로 build되어 있다.
5. 현재 host는 Darwin arm64라 Linux/eBPF `quic_bpf` 검증은 실행할 수 없다.

따라서 nginx에 대한 claim은 두 단계로 분리한다.

| claim | 현재 상태 |
| --- | --- |
| local HTTP/3 server가 quiche active source-port migration을 처리 | 완료, `nginx-quic-active-migration-runtime-20260630.md` |
| Linux `quic_bpf` packet-routing deployment에서도 migration support 확인 | 미실행, Linux host 필요 |

## 5. 논문 claim boundary

쓸 수 있는 주장:

> nginx source and local runtime evidence support server-side QUIC path validation and active-client-migration handling on loopback. A Linux `quic_bpf` deployment claim remains separate and unexecuted on the current macOS host.

한국어 표현:

> nginx QUIC은 local HTTP/3 runtime demo에서 quiche active migration을 처리했지만, 이는 Linux `quic_bpf` 기반 production packet-routing 검증과는 별개다. 현재 macOS host에서는 `quic_bpf` readiness가 `linux_required`로 닫히므로 production deployment claim을 추가하지 않는다.

피해야 할 주장:

| 금지 claim | 이유 |
| --- | --- |
| nginx production deployment에서 CM이 검증됐다 | local loopback runtime demo와 Linux/eBPF deployment는 다름 |
| `quic_bpf`가 현재 host에서 검증됐다 | 현재 host는 Darwin arm64 |
| `quic_bpf` blocked가 nginx migration 실패다 | prerequisite host mismatch일 뿐 runtime failure가 아님 |

## 6. 다음 단계

| 우선순위 | 작업 | 필요한 evidence |
| ---: | --- | --- |
| 1 | Linux VM/EC2에서 runner 재실행 | `linux_ready=yes` |
| 2 | root 또는 적절한 capability 확보 | `root_ready=yes` 또는 equivalent capability note |
| 3 | `/sys/fs/bpf` mount/writable 확인 | `sys_fs_bpf_ready=yes` |
| 4 | nginx `quic_bpf on;` config test와 runtime demo 확장 | config test, access log, path validation, response completion |
| 5 | local runtime result와 Linux `quic_bpf` result 분리 보고 | claim boundary 유지 |

추가 문서:

- [nginx-quic-bpf-linux-runner-20260630.md](nginx-quic-bpf-linux-runner-20260630.md)
