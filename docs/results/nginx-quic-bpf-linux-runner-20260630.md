# nginx quic_bpf Linux Runner

작성일: `2026-06-30`

## 1. 목적

이 문서는 nginx QUIC의 Linux `quic_bpf` deployment 검증을 위해 전용 runner를 추가한 결과다.

핵심 경계:

> 이 문서는 Linux `quic_bpf` 성공 결과가 아니다. 현재 단계에서는 Linux 전용 runner와 fail-closed local blocked artifact를 확보했다. 현재 host는 Darwin arm64이므로 runner는 active migration workload를 실행하지 않고 `validation=blocked`로 닫혔다.

## 2. 추가한 코드

| 파일 | 역할 |
| --- | --- |
| [harness/scripts/run-nginx-quic-bpf-linux-demo.sh](../../harness/scripts/run-nginx-quic-bpf-linux-demo.sh) | Linux/root/`/sys/fs/bpf`/nginx source gate가 열릴 때만 `quic_bpf on;` active migration demo를 실행하는 wrapper |
| [harness/scripts/run-nginx-quic-active-migration-demo.sh](../../harness/scripts/run-nginx-quic-active-migration-demo.sh) | `NGINX_QUIC_BPF=1`일 때 `quic_bpf on;`과 `listen ... reuseport`를 config에 추가하도록 확장 |

## 3. Runner가 하는 일

Linux 조건이 맞으면 runner는 다음 순서로 실행된다.

| 단계 | 내용 |
| --- | --- |
| 1 | nginx source, `quic_bpf` source, migration source file 확인 |
| 2 | Linux host, root 권한, writable `/sys/fs/bpf` 확인 |
| 3 | 기존 nginx active migration demo runner 존재 확인 |
| 4 | `NGINX_QUIC_BPF=1`로 active migration demo 실행 |
| 5 | nginx config에 `quic_bpf on;`, `listen ... quic reuseport` 적용 |
| 6 | quiche client `--enable-active-migration --perform-migration`로 1MiB HTTP/3 workload 실행 |
| 7 | response completion, server path seq:1 creation/validation, PATH_CHALLENGE/PATH_RESPONSE evidence 확인 |

## 4. 현재 로컬 실행

Command:

```bash
RUN_ID=nginx-quic-bpf-linux-demo-local-blocked-20260630 \
  harness/scripts/run-nginx-quic-bpf-linux-demo.sh
```

Result:

```text
run_id=nginx-quic-bpf-linux-demo-local-blocked-20260630
system_name=Darwin
system_machine=arm64
source_ready=yes
source_has_quic_bpf=yes
source_has_migration_file=yes
active_demo_runner_ready=yes
linux_ready=no
root_ready=no
sys_fs_bpf_ready=no
nginx_bin_ready=yes
nginx_v3_module_ready=yes
validation=blocked
blocked_reason=linux_required
```

해석:

> source와 local nginx binary, active migration demo runner는 준비됐지만 현재 host가 Linux가 아니므로 `quic_bpf` deployment 검증은 실행하지 않았다.

## 5. Claim Boundary

쓸 수 있는 주장:

> The repository now contains a fail-closed Linux runner for nginx `quic_bpf` deployment testing. On the current macOS host, the runner records `linux_required` before executing the workload.

한국어 표현:

> nginx `quic_bpf` Linux 검증 runner를 추가했다. 현재 macOS 로컬에서는 source와 기존 runtime demo runner readiness만 확인하고, Linux가 아니므로 workload 실행 전에 `validation=blocked`로 닫힌다.

피해야 할 주장:

| 금지 claim | 이유 |
| --- | --- |
| nginx `quic_bpf` deployment에서 Connection Migration이 성공했다 | Linux runner는 현재 host에서 실행되지 않음 |
| macOS blocked 결과가 nginx migration 실패다 | host prerequisite mismatch일 뿐 runtime failure가 아님 |
| local nginx active migration demo와 Linux `quic_bpf` deployment가 같은 claim이다 | loopback server runtime과 Linux/eBPF packet routing은 별도 축 |

## 6. 다음 단계

| 우선순위 | 작업 | 성공 근거 |
| ---: | --- | --- |
| 1 | Linux VM/EC2에서 runner 실행 | `linux_ready=yes`, `root_ready=yes`, `sys_fs_bpf_ready=yes` |
| 2 | `quic_bpf on;` config test와 nginx start 통과 | active demo artifact 생성 |
| 3 | quiche active migration workload 완료 | `client_response_bytes=1048576`, `validation=ok` |
| 4 | server path validation evidence 확인 | `server_path_seq1_created_count>=1`, `server_path_seq1_validated_count>=1` |

이 결과가 나오기 전까지 nginx에 대해서는 local server runtime positive control과 Linux `quic_bpf` deployment readiness를 분리한다.
