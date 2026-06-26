package main

import (
	"strings"
	"testing"
)

func TestBuildBrowserDownlinkHTMLIncludesStreamTimeoutRetryControls(t *testing.T) {
	html := buildBrowserDownlinkHTML("timeout retry", 8000, 8, 32768, false, 4000, 1, 500, 1500)

	wantSubstrings := []string{
		"retryAttempts=1",
		"retryDelayMs=500",
		"streamTimeoutMs=1500",
		"AbortController",
		"readWithTimeout(reader,streamTimeoutMs,controller)",
		"stream timeout after ",
		"signal:controller.signal",
		"downlinkRetriesUsed",
	}
	for _, want := range wantSubstrings {
		if !strings.Contains(html, want) {
			t.Fatalf("browser downlink HTML missing %q in:\n%s", want, html)
		}
	}
}
