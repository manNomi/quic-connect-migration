# CDN Edge Connection Migration Boundary Audit

Generated: `2026-06-30`

This public-safe audit narrows the CDN part of the deployment-path claim. It separates viewer-edge HTTP/3 continuity from end-to-end origin QUIC Connection Migration.

## Summary

| field | value |
| --- | --- |
| scope | `managed_cdn_edge_connection_migration_boundary` |
| implementations | `['AWS CloudFront', 'Cloudflare managed edge']` |
| evidence items | `6` |
| CloudFront viewer-edge HTTP/3 CM | `supported_by_official_docs` |
| CloudFront origin end-to-end QUIC CM | `not_established_by_official_docs` |
| Cloudflare viewer-edge HTTP/3 | `supported_by_official_docs` |
| Cloudflare origin HTTP/3 | `not_supported_in_inspected_official_doc` |
| live edge trial completed | `no` |
| interpretation | Managed CDN HTTP/3 support is a deployment-layer boundary. It can support viewer-to-edge continuity while still terminating or translating the origin leg. |

## Conclusion

| claim axis | result |
| --- | --- |
| safe CDN claim | `viewer_edge_http3_continuity_or_capability` |
| unsafe CDN claim | `origin_end_to_end_quic_connection_migration_without_separate_origin_evidence` |
| paper use | Use this audit to prevent CloudFront/Cloudflare HTTP/3 support from being misreported as end-to-end browser-origin Connection Migration. |

## Evidence Table

| id | source | lines | topic | observation | implication |
| --- | --- | --- | --- | --- | --- |
| `cloudfront-viewer-supported-http-versions` | [AWS CloudFront Developer Guide](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesGeneral.html) | `147-152` | `Supported HTTP versions` | CloudFront documentation scopes supported HTTP versions to viewers communicating with CloudFront and states that CloudFront supports HTTP/3 connection migration. | This supports a viewer-to-edge migration claim, not an origin end-to-end QUIC Connection Migration claim. |
| `cloudfront-api-httpversion-viewer-scope` | [AWS CloudFront API Reference](https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_DistributionConfig.html) | `154-162` | `DistributionConfig.HttpVersion` | The HttpVersion field controls the HTTP versions that viewers use to communicate with CloudFront and includes http3/http2and3 values. | Configuration evidence is viewer-facing; it does not prove the origin leg is QUIC or migration-preserving. |
| `cloudfront-origin-fetch-boundary` | [AWS News Blog](https://aws.amazon.com/blogs/aws/new-http-3-support-for-amazon-cloudfront/) | `56-59` | `Viewer HTTP/3 versus origin fetch` | The CloudFront HTTP/3 launch post describes client-side migration benefits, then separates viewer HTTP/3 requests to edge locations from origin fetches continuing over HTTP/1.1. | CloudFront HTTP/3 should be reported as edge-level continuity unless a separate experiment proves origin end-to-end QUIC semantics. |
| `cloudfront-no-origin-change-enable` | [AWS News Blog](https://aws.amazon.com/blogs/aws/new-http-3-support-for-amazon-cloudfront/) | `59-64` | `No origin changes for HTTP/3 enablement` | The launch post says HTTP/3 can be enabled for CloudFront distributions without origin changes. | A no-origin-change enablement model is strong evidence that the managed edge terminates or translates the protocol boundary. |
| `cloudflare-user-edge-scope` | [Cloudflare Speed Docs](https://developers.cloudflare.com/speed/optimization/protocol/http3/) | `118-129` | `HTTP/3 setting scope` | Cloudflare's HTTP/3 page states that the setting is for the connection between the user and Cloudflare and that HTTP/3 connection to the origin is not yet supported. | Cloudflare managed-edge HTTP/3 evidence must not be written as origin end-to-end Connection Migration evidence. |
| `cloudflare-dashboard-api-toggle` | [Cloudflare Speed Docs](https://developers.cloudflare.com/speed/optimization/protocol/http3/) | `143-157` | `HTTP/3 dashboard/API toggle` | Cloudflare exposes HTTP/3 as a zone setting through dashboard or API toggles. | A CDN setting can make viewer-edge H3 visible while leaving origin transport semantics outside the application's direct control. |

## Reporting Boundary

- Safe claim: CloudFront official docs support viewer-to-CloudFront HTTP/3 Connection Migration, and Cloudflare official docs scope HTTP/3 to the user-to-Cloudflare leg.
- Unsafe claim: A CloudFront or Cloudflare HTTP/3 toggle proves end-to-end origin QUIC Connection Migration, origin qlog path validation, or application-origin single-session continuity.
- Next non-iPhone gate: For CloudFront, run a viewer-edge continuity experiment and label it edge-level; for origin end-to-end CM, keep using direct-origin or CID-aware load-balancer paths with server qlog and backend routing evidence.

## Paper Interpretation

1. CDN HTTP/3 support is relevant because it is common in real web deployment, but it is not the same as direct browser-origin QUIC.
2. CloudFront is useful as a managed viewer-edge continuity case; it should not replace direct-origin or CID-aware load-balancer experiments.
3. Cloudflare is useful as a termination-boundary example because the inspected official doc explicitly separates user-to-Cloudflare HTTP/3 from origin HTTP/3.
4. This strengthens the paper framing: CM may be implemented, yet deployment layers can hide, terminate, or translate the semantics that an application researcher wants to measure.
