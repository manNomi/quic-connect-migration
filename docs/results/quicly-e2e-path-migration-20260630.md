# quicly e2e Path Migration Check

작성일: `2026-06-30`

## 1. 목적

이 문서는 quicly의 기존 `PARTIAL` 판정을 더 정밀하게 나누기 위한 focused e2e 결과다.

기존 fresh rerun에서는 `test.t` build와 migration-related unit evidence는 확보했지만, `t/e2e.t`는 Perl dependency 부족으로 실행 전 실패했다. 이번 보강에서는 local CPAN install로 `Net::EmptyPort` dependency를 채운 뒤 full `t/e2e.t`를 실행하고, 그중 Connection Migration과 직접 관련된 `path-migration` subtest만 별도 판정한다.

핵심 경계:

> 이 결과는 quicly full e2e PASS가 아니다. `path-migration` subtest는 PASS였지만, full `t/e2e.t`는 unrelated `slow-start` subtest 실패 때문에 exit 1이었다.

## 2. 추가한 runner

```bash
harness/scripts/run-quicly-e2e-path-migration-check.sh
```

runner가 하는 일:

| 단계 | 설명 |
| --- | --- |
| 1 | quicly source, `cli`, `udpfw`, `t/e2e.t` 존재 확인 |
| 2 | `Net::EmptyPort` Perl dependency 확인 |
| 3 | `prove -v t/e2e.t` 실행 |
| 4 | full e2e exit와 별개로 `path-migration` subtest 결과 추출 |
| 5 | `CID seq 1 is used for 1st path probe` check와 unrelated `slow-start` failure를 분리 기록 |

## 3. 실행 환경

| 항목 | 값 |
| --- | --- |
| quicly source | `/private/tmp/quic-cm-scan-repos/quicly` |
| quicly commit | `ed83c7c7d545a01650651c9523466f561ec5d4bb` |
| build dir | `/private/tmp/quic-cm-scan-repos/quicly/build-local` |
| binaries | `cli`, `udpfw`, `test.t` |
| Perl dependency | local CPAN install under `/private/tmp/quic-cm-perl5` |
| artifact root | `harness/results/quicly-e2e-path-migration-local-20260630` |

재현 명령:

```bash
RUN_ID=quicly-e2e-path-migration-local-20260630 \
  harness/scripts/run-quicly-e2e-path-migration-check.sh
```

`Net::EmptyPort`가 없으면 다음처럼 local install 후 재실행한다.

```bash
mkdir -p /private/tmp/quic-cm-perl5
PERL_MM_USE_DEFAULT=1 \
PERL_MM_OPT='INSTALL_BASE=/private/tmp/quic-cm-perl5' \
PERL_MB_OPT='--install_base /private/tmp/quic-cm-perl5' \
  cpan -T -i Net::EmptyPort
```

## 4. 최신 실행 결과

```text
run_id=quicly-e2e-path-migration-local-20260630
ready=yes
blocked_reason=none
net_empty_port_ready=yes
prove_exit=1
path_subtest_seen=yes
path_subtest_ok=yes
cid_seq_check_ok=yes
slow_start_failed=yes
result_fail=yes
validation=ok_path_migration
```

## 5. 핵심 evidence

`results/path-migration-excerpt.txt`에서 추출한 public-safe TAP excerpt:

```text
# Subtest: path-migration
    # Subtest: without-cid
        ok 1
        # Subtest: CID seq 1 is used for 1st path probe
            1..0 # SKIP zero-length CID
        ok 2 # skip zero-length CID
        ok 3 - packets-lost-but-cc-in-slow-start
        1..3
    ok 1 - without-cid
    # Subtest: with-cid
        ok 1
        # Subtest: CID seq 1 is used for 1st path probe
            ok 1
            1..1
        ok 2 - CID seq 1 is used for 1st path probe
        ok 3 - packets-lost-but-cc-in-slow-start
        1..3
    ok 2 - with-cid
    1..2
ok 17 - path-migration
```

Full e2e boundary:

```text
Failed 1/26 subtests
Failed test: 18
Result: FAIL
```

`Failed test: 18`은 `slow-start`다. 따라서 이 실행을 "quicly e2e 전체 PASS"로 쓰면 안 된다.

## 6. 해석

안전하게 쓸 수 있는 주장:

> quicly's full `t/e2e.t` did not pass on the current macOS host because an unrelated `slow-start` subtest failed. However, after satisfying the Perl dependency, the `path-migration` e2e subtest itself passed in both zero-length CID and CID-enabled modes, including the check that CID sequence 1 is used for the first path probe.

한국어 표현:

> quicly는 전체 e2e를 PASS로 주장할 수는 없지만, Connection Migration과 직접 관련된 `path-migration` e2e subtest는 통과했다. 특히 CID-enabled case에서 첫 path probe가 CID sequence 1을 사용한다는 검사도 통과했다. 따라서 quicly를 단순 source/primitive partial로만 남기기보다, focused e2e path-migration evidence가 있는 비교군으로 분류할 수 있다.

피해야 할 주장:

| 금지 claim | 이유 |
| --- | --- |
| quicly full e2e PASS | `prove_exit=1`, `Result: FAIL` |
| quicly 전체 production readiness 입증 | 현재는 local e2e subtest evidence |
| `slow-start` 실패가 migration 실패다 | 실패한 subtest는 path-migration 이후의 unrelated congestion-control timing 영역 |

## 7. 논문에서의 위치

이 결과는 Chapter 1 구현체 성숙도 표에서 quicly를 다음처럼 보강한다.

| 이전 분류 | 보강 후 분류 |
| --- | --- |
| fresh build/unit partial evidence | focused e2e path-migration evidence, full e2e caveat 유지 |

즉, quicly는 quic-go/quiche처럼 application continuity positive control은 아니지만, path promotion과 e2e path migration test가 실제로 통과한 구현체로 설명할 수 있다.
