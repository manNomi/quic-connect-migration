# Firefox Desktop Runtime Trial Packet

Generated: `2026-07-01`

This public-safe packet turns the Firefox/Neqo boundary audit into an executable research gate. It is not a Firefox Connection Migration result; it defines the evidence required before Firefox can be used as a runtime row.

## Summary

| field | value |
| --- | --- |
| scope | `firefox_desktop_runtime_trial_packet` |
| source boundary doc | `docs/results/firefox-neqo-browser-boundary-audit-20260701.md` |
| Neqo local Firefox recipe | [Neqo README](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/README.md#L154) |
| Firefox binary ready | `no` |
| geckodriver ready | `no` |
| packet capture ready | `yes` |
| non-iPhone desktop path ready | `no` |
| Firefox runtime rows executed | `no` |

## Local Tooling

| tool | found | executable | version |
| --- | --- | --- | --- |
| firefox | no | no | - |
| geckodriver | no | no | - |
| tcpdump | yes | yes | tcpdump version 4.99.1 -- Apple version 148 |
| route | yes | yes | route to: default |

## Firefox Profile Preferences

```js
user_pref("network.http.http3.enabled", true);
user_pref("network.http.http3.alt-svc-mapping-for-testing", "localhost;h3=\":12345\"");
user_pref("network.http.http3.disable_when_third_party_roots_found", false);
```

## Trial Plan

| rank | trial id | phase | target | prerequisite | required artifacts | acceptance gate | safe interpretation | do not claim |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `firefox-local-neqo-h3-baseline` | `local-baseline` | Firefox -> local neqo-server | Firefox binary, local Neqo checkout, temporary Firefox profile with HTTP/3 testing preferences. | neqo-server qlog directory<br>Firefox profile preferences used for the run<br>browser navigation result or WebDriver/manual timestamp<br>server access/log evidence for HTTP/3 request | baseline_only: Firefox reaches the local H3 target and server qlog confirms HTTP/3. | Firefox can be connected to the local Neqo H3 test target. | Connection Migration, public-origin behavior, or browser handover. |
| 2 | `firefox-controlled-public-h3-baseline` | `public-baseline` | Firefox -> controlled public H3 origin | Firefox binary, controlled public origin with WebPKI TLS and Alt-Svc h3, packet/server qlog capture enabled. | public origin readiness with Alt-Svc h3<br>server qlog or H3 access evidence<br>Firefox version/profile metadata<br>packet capture if browser-internal logging is unavailable | baseline_only: public H3 request completes and server-side H3 evidence is present. | Firefox public H3 baseline is usable for a later active path-change row. | Network-change migration or same-session continuity. |
| 3 | `firefox-controlled-public-range-active-001` | `active-network-change` | Firefox -> controlled public byte-range workload | Firefox public baseline PASS, non-iPhone desktop path-change command, before/after route snapshots, server qlog, and packet capture. | before/after route snapshots<br>server qlog PATH_CHALLENGE/PATH_RESPONSE or equivalent path validation evidence<br>server remote tuple/path evidence<br>workload completion state<br>Firefox logging/profile/profiler artifact if available | feasibility_or_strong_with_extra_browser_logs: task completion + client path change + server path validation; strong browser claim additionally needs Firefox/Necko/Neqo same-connection attribution. | Firefox range workload survived or failed under a controlled active path-change attempt. | Chrome-equivalent NetLog proof or Firefox single-session CM without same-connection browser/runtime attribution. |
| 4 | `firefox-controlled-public-upload-active-001` | `active-network-change` | Firefox -> controlled public upload workload | Same as range active row, but with upload endpoint and client-sending workload evidence. | before/after route snapshots<br>server qlog path validation evidence<br>upload completion and received byte count<br>server tuple/path evidence<br>Firefox logging/profile/profiler artifact if available | same as range active row, with upload byte-count continuity. | Firefox upload continuity can be compared with Chrome upload local/public evidence. | Application upload success as pure QUIC CM unless the same-session chain is proven. |

## Command Templates

### firefox-local-neqo-h3-baseline

```bash
NEQO_CHECKOUT=/private/tmp/quic-cm-scan-repos/neqo
cd "$NEQO_CHECKOUT"
QLOGDIR=/tmp/firefox-neqo-qlog cargo run --bin neqo-server -- 'localhost:12345'
FIREFOX_PROFILE=/tmp/firefox-cm-profile
mkdir -p "$FIREFOX_PROFILE"
# write the documented HTTP/3 test prefs to $FIREFOX_PROFILE/user.js, then launch Firefox to https://localhost:12345/
```

### firefox-controlled-public-h3-baseline

```bash
PUBLIC_ORIGIN_BASE=${PUBLIC_ORIGIN_BASE:?set controlled H3 origin}
FIREFOX_BIN=${FIREFOX_BIN:-/Applications/Firefox.app/Contents/MacOS/firefox}
FIREFOX_PROFILE=/tmp/firefox-public-h3-profile
"$FIREFOX_BIN" --new-instance --profile "$FIREFOX_PROFILE" "$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=firefox-public-baseline"
```

### firefox-controlled-public-range-active-001

```bash
PUBLIC_ORIGIN_BASE=${PUBLIC_ORIGIN_BASE:?set controlled H3 origin}
NETWORK_CHANGE_CMD=${NETWORK_CHANGE_CMD:?set non-iPhone desktop path-change command}
python3 tools/capture_network_path_snapshot.py --label firefox-before --url "$PUBLIC_ORIGIN_BASE" --output /tmp/firefox-before.json
# launch Firefox to /browser-range-download and trigger NETWORK_CHANGE_CMD after first range completes
$NETWORK_CHANGE_CMD
python3 tools/capture_network_path_snapshot.py --label firefox-after --url "$PUBLIC_ORIGIN_BASE" --output /tmp/firefox-after.json
```

### firefox-controlled-public-upload-active-001

```bash
PUBLIC_ORIGIN_BASE=${PUBLIC_ORIGIN_BASE:?set controlled H3 origin}
NETWORK_CHANGE_CMD=${NETWORK_CHANGE_CMD:?set non-iPhone desktop path-change command}
# launch Firefox to /browser-upload, trigger NETWORK_CHANGE_CMD mid-upload, then classify server/qlog/workload artifacts
```

## Claim Boundary

- Safe claim: This packet makes Firefox runtime evidence reproducible and fail-closed; it does not add a Firefox runtime result until a trial row with artifacts exists.
- Unsafe claim: Neqo transport tests, this packet, or a Firefox H3 baseline prove Firefox single-session Connection Migration across an active path change.
- Next non-iPhone gate: Install Firefox/geckodriver or run a manual Firefox profile, open a non-iPhone desktop path-change gate, then start with local Neqo H3 baseline before any active public row.

## Current Blockers

- Firefox binary is not installed or not executable on the current host
- geckodriver is not installed, so automation would be manual or require another driver
- no active non-iPhone desktop path-change gate is open
