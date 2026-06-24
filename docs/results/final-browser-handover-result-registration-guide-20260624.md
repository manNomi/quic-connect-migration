# Final browser handover result registration guide

작성일: 2026-06-24

## 1. 목적

최종 browser/mobile handover 본 실험을 실행한 뒤, 결과를 `data/experiment-results.csv`에 어떤 형식으로 등록해야 `tools/audit_final_browser_handover_trials.py`가 정확히 세는지 정리한다.

이 문서는 실험 결과를 만들지 않는다. 실험 후 기록 오류를 줄이기 위한 등록 규칙이다.

## 2. 공통 규칙

CSV row는 다음 조건을 지켜야 한다.

| 필드 | 규칙 |
| --- | --- |
| `trial_id` | `controlled-public`, browser, workload, phase token을 포함 |
| `deployment_tier` | `controlled public` 문구 포함 |
| `migration_trigger` | active run은 `active`, `path`, `change` 포함; no-change baseline은 `no network change` 포함 |
| `application_task` | workload token 포함. heartbeat run은 `heartbeat` 포함 |
| `notes` | classifier 결과를 `classification <value>` 또는 동등하게 검색 가능한 문자열로 포함 |
| `status` | Chrome active CM 성공은 `PASS`; Safari/Android server-qlog-only evidence는 `PASS_FEASIBILITY` |

## 3. 권장 trial_id

| requirement | 권장 trial_id pattern |
| --- | --- |
| Chrome public H3 baseline | `controlled-public-chrome-h3-baseline-001` |
| Chrome downlink no-heartbeat active CM | `controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| Chrome downlink heartbeat active CM | `controlled-public-chrome-downlink-heartbeat-network-change-001` |
| Chrome downlink no-heartbeat no-change baseline | `controlled-public-chrome-downlink-noheartbeat-nochange-001` |
| Chrome downlink heartbeat no-change baseline | `controlled-public-chrome-downlink-heartbeat-nochange-001` |
| Safari feasibility | `controlled-public-safari-downlink-network-change-001` |
| Android Chrome feasibility | `controlled-public-android-chrome-downlink-network-change-001` |

반복 실험은 `001`, `002`, `003`처럼 suffix만 증가시킨다.

## 4. Chrome active CM row 예시

```csv
controlled-public-chrome-downlink-noheartbeat-network-change-001,2026-06-24,PASS,Chrome 149 + controlled public quic-go H3,controlled public browser active network-change,HTTP/3 over QUIC,"active path change during downlink streaming; NETWORK_CHANGE_CMD executed",true,true,"GET /browser-downlink then streaming GET /downlink-stream",true,false,none,repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001,"classification possible_connection_migration; client_path_change=client_active_path_changed; server remote tuple changed; qlog path validation=true; target QUIC session evidence did not indicate reconnect_or_multiple_sessions"
```

이 row는 `chrome-downlink-noheartbeat-active-cm` 요구사항에 1회로 계산된다.

## 5. Chrome no-change baseline row 예시

```csv
controlled-public-chrome-downlink-noheartbeat-nochange-001,2026-06-24,PASS,Chrome 149 + controlled public quic-go H3,controlled public browser no-change baseline,HTTP/3 over QUIC,"no network change; controlled public downlink streaming without heartbeat",false,false,"GET /browser-downlink then streaming GET /downlink-stream",true,false,none,repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-nochange-001,"classification no_path_change_baseline; server remote addr count 1; application H3 baseline confirmed"
```

이 row는 `chrome-downlink-noheartbeat-nochange-baseline` 요구사항에 1회로 계산된다.

## 6. Safari/Android feasibility row 예시

Safari:

```csv
controlled-public-safari-downlink-network-change-001,2026-06-24,PASS_FEASIBILITY,Safari + controlled public quic-go H3,controlled public browser active network-change,HTTP/3 over QUIC,"active path change during Safari downlink workload",true,true,"GET /browser-downlink then streaming GET /downlink-stream",true,false,server-qlog-only,repro/quic-go-min-repro/artifacts/controlled-public-safari-downlink-network-change-001,"classification possible_connection_migration_server_qlog_only; Safari navigation_ok=true; server remote tuple changed; qlog path validation=true; browser-internal QUIC log unavailable"
```

Android Chrome:

```csv
controlled-public-android-chrome-downlink-network-change-001,2026-06-24,PASS_FEASIBILITY,Android Chrome + controlled public quic-go H3,controlled public mobile browser active network-change,HTTP/3 over QUIC,"active path change during Android Chrome downlink workload",true,true,"GET /browser-downlink then streaming GET /downlink-stream",true,false,server-qlog-only,repro/quic-go-min-repro/artifacts/controlled-public-android-chrome-downlink-network-change-001,"classification possible_connection_migration_server_qlog_only; Android Chrome navigation_ok=true; server remote tuple changed; qlog path validation=true; browser-internal QUIC log unavailable"
```

둘 중 하나가 있으면 `p1-safari-or-android-feasibility` 요구사항에 1회로 계산된다.

## 7. 등록 후 검증

실험을 시작하기 전 현재 CSV 기준 다음 실행 항목을 확인한다.

```bash
python3 tools/select_next_final_handover_trial.py \
  --output docs/results/final-handover-next-trial-20260624.md
```

실제 artifact가 있는 경우 CSV row 초안은 다음 도구로 먼저 생성한다.

```bash
python3 tools/draft_final_handover_result_row.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --format markdown \
  --output /tmp/final-handover-row.md
```

이 도구는 classifier summary를 읽어 positive CM, reconnect/multiple-session negative control, Safari/Android `PASS_FEASIBILITY`, no-change baseline row의 status/notes를 구분한다. 단, 최종 등록 전에는 raw artifact와 summary를 직접 확인한다.

CSV에 붙이기 전에 단일 artifact validation을 실행한다.

```bash
python3 tools/validate_final_handover_trial_artifact.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --output /tmp/final-handover-artifact-validation.md
```

최종 protocol에 카운트되는 성공 trial만 허용하려면 `--require-final-countable`을 붙인다. 이 옵션은 reconnect/multiple-session negative control처럼 기록은 가능하지만 final CM success로 세면 안 되는 row에서 exit 1을 반환한다.

CSV에 붙일 때는 먼저 dry-run으로 확인한다.

```bash
python3 tools/append_final_handover_result_row.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable \
  --output /tmp/final-handover-append-dry-run.md
```

dry-run 결과에서 `duplicate trial_id=no`, `counts toward final protocol=yes`를 확인한 뒤에만 `--apply`를 붙인다.

```bash
python3 tools/append_final_handover_result_row.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable \
  --apply
```

row를 추가한 뒤 다음을 실행한다.

```bash
python3 tools/audit_final_browser_handover_trials.py \
  --output docs/results/final-browser-handover-trial-audit-20260624.md

python3 tools/build_paper_tables.py --output docs/results/paper-tables-20260624.md
python3 tools/audit_research_bundle.py --output docs/results/research-bundle-audit-20260624.md
python3 tools/validate_publication_bundle.py
```

최종 완료 전에는 다음도 확인한다.

```bash
python3 tools/audit_final_browser_handover_trials.py --require-complete
```

이 명령이 exit 0이 될 때까지 논문 Results에서 browser/mobile handover 본 실험 완료를 주장하지 않는다.
