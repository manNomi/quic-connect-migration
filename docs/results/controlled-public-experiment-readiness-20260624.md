# Controlled public experiment readiness

작성일: 2026-06-24

## 1. 목적

controlled public Chrome HTTP/3 network-change 하네스를 실제로 실행하기 전에, 현재 로컬/실험 환경이 충분한지 자동 점검하는 readiness gate를 추가했다.

이 단계는 connection migration 결과가 아니다. 실제 실험을 실행해도 되는 상태인지 판단하는 preflight다.

## 2. 추가한 도구

파일:

- `tools/check_controlled_public_experiment_readiness.py`

이 도구는 다음 조건을 함께 확인한다.

| 항목 | 의미 |
| --- | --- |
| controlled public origin readiness | public URL의 DNS/TLS/HTTPS/Alt-Svc 상태 |
| application H3 baseline summary | `controlled-public-h3-baseline-summary.json`이 `status=PASS`인지 |
| active secondary path | non-loopback active IPv4 interface가 2개 이상인지 |
| network-change command | `NETWORK_CHANGE_CMD`를 제공했는지 |
| Chrome/harness readiness | Chrome binary와 network-change wrapper 존재 여부 |

## 3. 실행

```bash
python3 tools/check_controlled_public_experiment_readiness.py \
  --format json \
  --output data/controlled-public-experiment-readiness-20260624.json

python3 tools/check_controlled_public_experiment_readiness.py \
  --format markdown
```

## 4. 현재 결과

| check | value |
| --- | --- |
| controlled public origin ready | `false` |
| application H3 baseline ready | `false` |
| network-change harness ready | `true` |
| Chrome found | `true` |
| active IPv4 interfaces | `en0(192.168.0.212)` |
| secondary path ready | `false` |
| NETWORK_CHANGE_CMD present | `false` |
| can run application H3 baseline | `false` |
| can run network-change | `false` |

현재 blockers:

1. public origin URL is not provided
2. controlled public application H3 baseline summary is not PASS
3. active secondary network path is not ready
4. `NETWORK_CHANGE_CMD` is not provided

## 5. 해석

현재 상태에서 real interface-change 실험을 실행하면 connection migration 실험이 아니라 단순 연결 단절 또는 no-op control이 될 가능성이 높다.

따라서 다음 순서가 필요하다.

1. controlled public origin URL 준비
2. WebPKI certificate와 UDP/TCP 443 설정
3. application H3 baseline `status=PASS` 확보
4. active secondary path 준비
5. 실제 active path를 바꾸는 `NETWORK_CHANGE_CMD` 확정
6. 그 후 `run-controlled-public-h3-network-change.sh` 실행

## 6. 논문상 의미

이 readiness gate는 실험 실패를 연구 결과로 오해하지 않기 위한 안전장치다. browser CM 연구에서는 “network change를 넣었다”는 사실만으로 충분하지 않고, 실제 active path 변화가 있었는지와 application H3 precondition이 성립했는지를 먼저 증명해야 한다.
