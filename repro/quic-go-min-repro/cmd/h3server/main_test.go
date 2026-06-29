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

func TestBuildBrowserPollHTMLIncludesRetryControls(t *testing.T) {
	html := buildBrowserPollHTML("poll retry", 6, 1000, 2, 750)

	wantSubstrings := []string{
		"retryAttempts=2",
		"retryDelayMs=750",
		"pollWithRetry",
		"attempt=${attempt}",
		"pollRetriesUsed",
		"pollCompletedCount",
		"pollComplete",
		"pollErrorElapsedMs",
	}
	for _, want := range wantSubstrings {
		if !strings.Contains(html, want) {
			t.Fatalf("browser poll HTML missing %q in:\n%s", want, html)
		}
	}
}

func TestBuildBrowserMediaSegmentsHTMLIncludesSegmentRetryControls(t *testing.T) {
	html := buildBrowserMediaSegmentsHTML("media retry", 6, 1000, 32768, 250, 2, 2, 750)

	wantSubstrings := []string{
		"media-segment",
		"retryAttempts=2",
		"retryDelayMs=750",
		"segmentWithRetry",
		"mediaCompletedCount",
		"mediaRetriesUsed",
		"mediaBytes",
		"mediaComplete",
		"mediaErrorElapsedMs",
	}
	for _, want := range wantSubstrings {
		if !strings.Contains(html, want) {
			t.Fatalf("browser media HTML missing %q in:\n%s", want, html)
		}
	}
}

func TestBuildBrowserBufferedMediaHTMLIncludesBufferControls(t *testing.T) {
	html := buildBrowserBufferedMediaHTML("buffered media", 8, 32768, 100, 2, 1000, 2, 4, 1, 750)

	wantSubstrings := []string{
		"Chrome H3 buffered media",
		"media-segment",
		"startupBuffer=2",
		"maxBuffer=4",
		"playbackInterval=1000",
		"retryAttempts=1",
		"fetchLoop",
		"playbackLoop",
		"bufferedMediaBufferDepth",
		"bufferedMediaRebufferEvents",
		"bufferedMediaComplete",
		"mediaComplete",
	}
	for _, want := range wantSubstrings {
		if !strings.Contains(html, want) {
			t.Fatalf("browser buffered media HTML missing %q in:\n%s", want, html)
		}
	}
}

func TestBuildBrowserRangeDownloadHTMLIncludesRangeRetryControls(t *testing.T) {
	html := buildBrowserRangeDownloadHTML("range retry", 1048576, 131072, 250, 2, 1, 750)

	wantSubstrings := []string{
		"range-download",
		"Range:`bytes=${start}-${end}`",
		"retryAttempts=1",
		"retryDelayMs=750",
		"rangeWithRetry",
		"rangeCompletedBytes",
		"rangeCompletedChunks",
		"rangeRetriesUsed",
		"rangeComplete",
		"rangeErrorElapsedMs",
	}
	for _, want := range wantSubstrings {
		if !strings.Contains(html, want) {
			t.Fatalf("browser range HTML missing %q in:\n%s", want, html)
		}
	}
}

func TestParseRangeHeader(t *testing.T) {
	start, end, partial, err := parseRangeHeader("bytes=10-19", 100)
	if err != nil {
		t.Fatalf("parse range: %v", err)
	}
	if start != 10 || end != 19 || !partial {
		t.Fatalf("unexpected range parse: start=%d end=%d partial=%v", start, end, partial)
	}

	start, end, partial, err = parseRangeHeader("", 100)
	if err != nil {
		t.Fatalf("parse empty range: %v", err)
	}
	if start != 0 || end != 99 || partial {
		t.Fatalf("unexpected empty range parse: start=%d end=%d partial=%v", start, end, partial)
	}

	start, end, partial, err = parseRangeHeader("bytes=90-120", 100)
	if err != nil {
		t.Fatalf("parse clipped range: %v", err)
	}
	if start != 90 || end != 99 || !partial {
		t.Fatalf("unexpected clipped range parse: start=%d end=%d partial=%v", start, end, partial)
	}
}
