# Artifact Cleanup Dry-run Plan

Generated: `2026-06-24`

## Summary

| metric | value |
| --- | --- |
| target free GiB | `5.0` |
| current free | `14.2 GiB` |
| free space needed | `0 B` |
| selected candidates | `0/76` |
| reclaimable from selected | `0 B` |
| projected free after selected cleanup | `14.2 GiB` |
| target met by selected cleanup | `yes` |
| remaining external cleanup gap | `0 B` |

## Selected Candidates

| path | size | files | directories |
| --- | ---: | ---: | ---: |
| - | - | - | - |

## Note

Dry-run only. Review docs/results and data/experiment-results.csv before deleting any raw artifact directory.

This tool does not delete files. It only identifies how much local ignored artifact cleanup can contribute before running large NetLog/qlog/pcap experiments.
