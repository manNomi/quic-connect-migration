# Chapter 1 External Link Check

작성일: `2026-06-30`

이 표는 `chapter-01-reference-and-scanner-evidence.md`와 `chapter-01-implementation-maturity.md`에 포함된 외부 URL을 `curl -L -I`로 확인한 결과다. `403`은 링크 부재가 아니라 publisher가 HEAD/curl 접근을 제한한 경우로 보고, 논문 최종본에서는 브라우저 수동 확인 또는 DOI/arXiv mirror를 함께 남긴다.

| URL | status | note | effective URL |
| --- | ---: | --- | --- |
| [datatracker.ietf.org](https://datatracker.ietf.org/doc/html/rfc9000) | `200` | OK | [datatracker.ietf.org](https://datatracker.ietf.org/doc/html/rfc9000) |
| [datatracker.ietf.org](https://datatracker.ietf.org/doc/html/rfc9114) | `200` | OK | [datatracker.ietf.org](https://datatracker.ietf.org/doc/html/rfc9114) |
| [github.com](https://github.com/quicwg/base-drafts/wiki/Implementations) | `200` | OK | [github.com](https://github.com/quicwg/base-drafts/wiki/Implementations) |
| [github.com](https://github.com/quicwg/quicwg.github.io/blob/main/implementations.md) | `200` | OK | [github.com](https://github.com/quicwg/quicwg.github.io/blob/main/implementations.md) |
| [dl.acm.org](https://dl.acm.org/doi/10.1145/3727063.3727066) | `403` | publisher blocks HEAD/curl; manual DOI check needed | [dl.acm.org](https://dl.acm.org/doi/10.1145/3727063.3727066) |
| [github.com](https://github.com/curl/curl/issues/7695) | `200` | OK | [github.com](https://github.com/curl/curl/issues/7695) |
| [github.com](https://github.com/quic-go/quic-go) | `200` | OK | [github.com](https://github.com/quic-go/quic-go) |
| [quic-go.net](https://quic-go.net/docs/quic/connection-migration/) | `200` | OK | [quic-go.net](https://quic-go.net/docs/quic/connection-migration/) |
| [github.com](https://github.com/cloudflare/quiche) | `200` | OK | [github.com](https://github.com/cloudflare/quiche) |
| [docs.rs](https://docs.rs/quiche/latest/quiche/) | `200` | OK | [docs.rs](https://docs.rs/quiche/latest/quiche/) |
| [github.com](https://github.com/aws/s2n-quic) | `200` | OK | [github.com](https://github.com/aws/s2n-quic) |
| [aws.github.io](https://aws.github.io/s2n-quic/) | `200` | OK | [aws.github.io](https://aws.github.io/s2n-quic/) |
| [github.com](https://github.com/ngtcp2/ngtcp2) | `200` | OK | [github.com](https://github.com/ngtcp2/ngtcp2) |
| [nghttp2.org](https://nghttp2.org/ngtcp2/) | `200` | OK | [nghttp2.org](https://nghttp2.org/ngtcp2/) |
| [github.com](https://github.com/litespeedtech/lsquic) | `200` | OK | [github.com](https://github.com/litespeedtech/lsquic) |
| [litespeedtech.com](https://www.litespeedtech.com/open-source/quic-http3-library) | `200` | OK | [litespeedtech.com](https://www.litespeedtech.com/open-source/quic-http3-library) |
| [github.com](https://github.com/microsoft/msquic) | `200` | OK | [github.com](https://github.com/microsoft/msquic) |
| [microsoft.github.io](https://microsoft.github.io/msquic/) | `200` | OK | [microsoft.github.io](https://microsoft.github.io/msquic/) |
| [github.com](https://github.com/quinn-rs/quinn) | `200` | OK | [github.com](https://github.com/quinn-rs/quinn) |
| [docs.rs](https://docs.rs/quinn/latest/quinn/) | `200` | OK | [docs.rs](https://docs.rs/quinn/latest/quinn/) |
| [github.com](https://github.com/mozilla/neqo) | `200` | OK | [github.com](https://github.com/mozilla/neqo) |
| [github.com](https://github.com/alibaba/xquic) | `200` | OK | [github.com](https://github.com/alibaba/xquic) |
| [chromium.googlesource.com](https://chromium.googlesource.com/chromium/src/) | `200` | OK | [chromium.googlesource.com](https://chromium.googlesource.com/chromium/src/) |
| [developer.android.com](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions) | `200` | OK | [developer.android.com](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions) |
| [aws.amazon.com](https://aws.amazon.com/blogs/aws/new-http-3-support-for-amazon-cloudfront/) | `200` | OK | [aws.amazon.com](https://aws.amazon.com/blogs/aws/new-http-3-support-for-amazon-cloudfront/) |
| [docs.aws.amazon.com](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html#DownloadDistValuesSupportedHTTPVersions) | `200` | OK | [docs.aws.amazon.com](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html#DownloadDistValuesSupportedHTTPVersions) |
| [aws.amazon.com](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/) | `200` | OK | [aws.amazon.com](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/) |
| [docs.aws.amazon.com](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-listeners.html) | `200` | OK | [docs.aws.amazon.com](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-listeners.html) |
| [github.com](https://github.com/facebook/mvfst) | `200` | OK | [github.com](https://github.com/facebook/mvfst) |
| [github.com](https://github.com/private-octopus/picoquic) | `200` | OK | [github.com](https://github.com/private-octopus/picoquic) |
| [github.com](https://github.com/nginx/nginx) | `200` | OK | [github.com](https://github.com/nginx/nginx) |
| [nginx.org](https://nginx.org/en/docs/http/ngx_http_v3_module.html) | `200` | OK | [nginx.org](https://nginx.org/en/docs/http/ngx_http_v3_module.html) |
| [github.com](https://github.com/h2o/quicly) | `200` | OK | [github.com](https://github.com/h2o/quicly) |
| [github.com](https://github.com/aiortc/aioquic) | `200` | OK | [github.com](https://github.com/aiortc/aioquic) |
| [aioquic.readthedocs.io](https://aioquic.readthedocs.io/) | `200` | redirect OK | [aioquic.readthedocs.io](https://aioquic.readthedocs.io/en/latest/) |
| [github.com](https://github.com/haproxy/haproxy) | `200` | OK | [github.com](https://github.com/haproxy/haproxy) |
| [haproxy.com](https://www.haproxy.com/documentation/haproxy-configuration-tutorials/protocol-support/http/) | `200` | OK | [haproxy.com](https://www.haproxy.com/documentation/haproxy-configuration-tutorials/protocol-support/http/) |
| [github.com](https://github.com/quic-go/quic-go.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/quic-go/quic-go) |
| [github.com](https://github.com/cloudflare/quiche.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/cloudflare/quiche) |
| [github.com](https://github.com/aws/s2n-quic.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/aws/s2n-quic) |
| [github.com](https://github.com/private-octopus/picoquic.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/private-octopus/picoquic) |
| [github.com](https://github.com/ngtcp2/ngtcp2.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/ngtcp2/ngtcp2) |
| [github.com](https://github.com/quinn-rs/quinn.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/quinn-rs/quinn) |
| [github.com](https://github.com/mozilla/neqo.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/mozilla/neqo) |
| [github.com](https://github.com/aiortc/aioquic.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/aiortc/aioquic) |
| [github.com](https://github.com/litespeedtech/lsquic.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/litespeedtech/lsquic) |
| [github.com](https://github.com/microsoft/msquic.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/microsoft/msquic) |
| [github.com](https://github.com/alibaba/xquic.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/alibaba/xquic) |
| [github.com](https://github.com/haproxy/haproxy.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/haproxy/haproxy) |
| [github.com](https://github.com/facebook/mvfst.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/facebook/mvfst) |
| [github.com](https://github.com/nginx/nginx.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/nginx/nginx) |
| [github.com](https://github.com/h2o/quicly.git) | `200` | clone URL redirects to repo page under HEAD check | [github.com](https://github.com/h2o/quicly) |

## 검수 요약

| 항목 | 값 |
| --- | ---: |
| checked URLs | `52` |
| OK or redirect OK | `51` |
| publisher/API blocked or method-limited | `1` |
| not found | `0` |
