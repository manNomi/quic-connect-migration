# Artifact Cleanup Dry-run Plan

Generated: `2026-06-25`

## Summary

| metric | value |
| --- | --- |
| target free GiB | `7.0` |
| candidate policy | `review-unreferenced` |
| current free | `9.2 GiB` |
| free space needed | `0 B` |
| selected candidates | `0/15` |
| reclaimable from selected | `0 B` |
| projected free after selected cleanup | `9.2 GiB` |
| target met by selected cleanup | `yes` |
| remaining external cleanup gap | `0 B` |

## Selected Candidates

| path | size | files | directories | recommendation |
| --- | ---: | ---: | ---: | --- |
| - | - | - | - | - |

## Note

Dry-run only. Review docs/results and data/experiment-results.csv before deleting any raw artifact directory.

`candidate_policy=review-unreferenced` excludes artifact directories referenced by tracked CSVs or planned final trial ids.

This tool does not delete files. It only identifies how much local ignored artifact cleanup can contribute before running large NetLog/qlog/pcap experiments.
