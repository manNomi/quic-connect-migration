# Final handover trial artifact validator

작성일: 2026-06-24

## 1. 목적

최종 browser/mobile handover 실험을 실행한 뒤, 단일 artifact directory가 `data/experiment-results.csv`에 등록 가능한지와 최종 protocol requirement에 실제로 카운트되는지를 분리해서 검증한다.

이 문서는 실험 결과를 만들지 않는다. 결과 등록 과정에서 positive CM, reconnect negative control, Safari/Android feasibility evidence를 혼동하지 않기 위한 검증 절차다.

## 2. 실행

```bash
python3 tools/validate_final_handover_trial_artifact.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --output /tmp/final-handover-artifact-validation.md
```

최종 protocol에 카운트되는 결과만 허용하려면 다음 옵션을 붙인다.

```bash
python3 tools/validate_final_handover_trial_artifact.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable
```

`--require-final-countable`은 reconnect/multiple-session negative control처럼 CSV에는 기록할 수 있지만 최종 성공 trial로 세면 안 되는 row에서 exit 1을 반환한다.

## 3. 판정 출력

| 항목 | 의미 |
| --- | --- |
| `appendable_to_experiment_results` | CSV field가 완성되어 기록 가능한지 |
| `counts_toward_final_protocol` | `data/final-browser-handover-required-trials.csv`의 requirement에 매칭되는지 |
| `claim_strength` | 논문에서 사용할 수 있는 claim 강도 |
| `matched_final_requirements` | 실제로 카운트되는 requirement id |
| `warnings` | overclaim 방지 경고 |

## 4. Regression

```bash
python3 tools/test_validate_final_handover_trial_artifact.py
```

테스트는 synthetic classifier summary로 다음을 확인한다.

| case | expected |
| --- | --- |
| Chrome `possible_connection_migration` | final Chrome active CM requirement에 카운트 |
| Chrome `reconnect_or_multiple_sessions` | CSV 기록 가능하지만 final CM success로는 미카운트 |
| Safari `possible_connection_migration_server_qlog_only` | P1 feasibility requirement로만 카운트 |

## 5. 등록 순서

1. raw artifact와 classifier summary를 확인한다.
2. `draft_final_handover_result_row.py`로 CSV row 초안을 생성한다.
3. `validate_final_handover_trial_artifact.py`로 append 가능 여부와 final protocol count 여부를 확인한다.
4. row를 `data/experiment-results.csv`에 등록한다.
5. `python3 tools/audit_final_browser_handover_trials.py --require-complete`로 최종 완료 여부를 검증한다.
