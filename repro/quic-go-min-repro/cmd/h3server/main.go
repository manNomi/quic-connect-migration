package main

import (
	"crypto/sha256"
	"crypto/tls"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"html"
	"io"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/quic-go/quic-go"
	"github.com/quic-go/quic-go/http3"
	h3qlog "github.com/quic-go/quic-go/http3/qlog"

	"quic-cm/quic-go-min-repro/internal/common"
)

type requestRecord struct {
	Label               string            `json:"label"`
	Method              string            `json:"method"`
	Path                string            `json:"path"`
	RemoteAddr          string            `json:"remote_addr"`
	RequestBytes        int               `json:"request_bytes"`
	RequestSHA256       string            `json:"request_sha256,omitempty"`
	ResponseBytes       int               `json:"response_bytes"`
	ResponseSHA256      string            `json:"response_sha256,omitempty"`
	ResponseContentType string            `json:"response_content_type,omitempty"`
	ResponseHeaders     map[string]string `json:"response_headers,omitempty"`
	Proto               string            `json:"proto,omitempty"`
	TLSALPN             string            `json:"tls_alpn,omitempty"`
	HandledAt           string            `json:"handled_at"`
	Workload            string            `json:"workload"`
	StreamResponse      bool              `json:"stream_response,omitempty"`
	ChunkBytes          int               `json:"chunk_bytes,omitempty"`
	ChunkDelayMillis    int64             `json:"chunk_delay_millis,omitempty"`
	DecodeSuccessful    bool              `json:"decode_successful"`
}

type serverResult struct {
	Role             string          `json:"role"`
	OK               bool            `json:"ok"`
	StartedAt        string          `json:"started_at"`
	CompletedAt      string          `json:"completed_at"`
	ListenAddr       string          `json:"listen_addr"`
	ConnectionIDMode string          `json:"connection_id_mode"`
	AWSServerID      string          `json:"aws_server_id,omitempty"`
	ExpectedRequests int             `json:"expected_requests"`
	Requests         []requestRecord `json:"requests"`
	Error            string          `json:"error,omitempty"`
}

func main() {
	addr := flag.String("addr", "127.0.0.1:4243", "UDP listen address")
	logPath := flag.String("log", "artifacts/logs/h3server.jsonl", "JSONL log path")
	resultPath := flag.String("result", "artifacts/results/h3server.json", "result JSON path")
	keyLogPath := flag.String("keylog", "", "TLS key log path")
	qlogDir := flag.String("qlog-dir", "artifacts/qlog", "qlog output directory")
	tcpAddr := flag.String("tcp-addr", "", "optional TCP HTTPS listen address for Alt-Svc bootstrap")
	altSvc := flag.String("alt-svc", "", "optional Alt-Svc header value to advertise HTTP/3")
	timeout := flag.Duration("timeout", 30*time.Second, "overall server timeout")
	completionGrace := flag.Duration("completion-grace", 500*time.Millisecond, "grace period after expected requests before server close")
	serverIDHex := flag.String("server-id", "", "optional AWS NLB QUIC Server ID as 16 hex chars")
	expectedRequests := flag.Int("expected-requests", 2, "number of requests to wait for before exiting")
	flag.Parse()

	result, err := run(*addr, *tcpAddr, *altSvc, *logPath, *resultPath, *keyLogPath, *qlogDir, *timeout, *completionGrace, *serverIDHex, *expectedRequests)
	if writeErr := common.WriteJSONFile(*resultPath, result); writeErr != nil {
		log.Printf("write result: %v", writeErr)
	}
	if err != nil {
		log.Fatal(err)
	}
}

func run(addr, tcpAddr, altSvc, logPath, resultPath, keyLogPath, qlogDir string, timeout, completionGrace time.Duration, serverIDHex string, expectedRequests int) (serverResult, error) {
	started := time.Now().UTC()
	result := serverResult{
		Role:             "h3server",
		StartedAt:        started.Format(time.RFC3339Nano),
		ListenAddr:       addr,
		ConnectionIDMode: "default",
		ExpectedRequests: expectedRequests,
	}
	if expectedRequests <= 0 {
		err := fmt.Errorf("expected-requests must be positive")
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}

	serverID, err := common.ParseAWSServerIDHex(serverIDHex)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	if serverIDHex != "" {
		generator := common.NewAWSNLBConnectionIDGenerator(serverID)
		result.ConnectionIDMode = "aws-quic-lb-plaintext"
		result.AWSServerID = generator.ServerIDHex()
	}

	logger, err := common.NewJSONLLogger(logPath, "h3server")
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	defer logger.Close()

	if qlogDir != "" {
		if err := common.EnsureDir(qlogDir); err != nil {
			result.Error = err.Error()
			result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
			return result, err
		}
		if err := os.Setenv("QLOGDIR", qlogDir); err != nil {
			result.Error = err.Error()
			result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
			return result, err
		}
	}

	tlsConf, keyLogCloser, err := common.ServerTLSConfig(keyLogPath)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	if keyLogCloser != nil {
		defer keyLogCloser.Close()
	}

	udpAddr, err := net.ResolveUDPAddr("udp", addr)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	udpConn, err := net.ListenUDP("udp", udpAddr)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	defer udpConn.Close()

	transport := &quic.Transport{Conn: udpConn}
	if serverIDHex != "" {
		transport.ConnectionIDGenerator = common.NewAWSNLBConnectionIDGenerator(serverID)
	}
	defer transport.Close()

	quicConf := &quic.Config{
		Tracer:          h3qlog.DefaultConnectionTracer,
		MaxIdleTimeout:  30 * time.Second,
		KeepAlivePeriod: 5 * time.Second,
	}
	listener, err := transport.ListenEarly(http3.ConfigureTLSConfig(tlsConf), quicConf)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	defer listener.Close()

	done := make(chan struct{})
	var doneOnce sync.Once
	var mu sync.Mutex
	activeHandlers := 0
	maybeCompleteLocked := func() {
		if len(result.Requests) >= expectedRequests && activeHandlers == 0 {
			doneOnce.Do(func() { close(done) })
		}
	}
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		activeHandlers++
		mu.Unlock()
		defer func() {
			mu.Lock()
			activeHandlers--
			maybeCompleteLocked()
			mu.Unlock()
		}()
		if altSvc != "" {
			w.Header().Set("Alt-Svc", altSvc)
		}
		record, status, response := handleWorkloadRequest(r)
		mu.Lock()
		result.Requests = append(result.Requests, record)
		count := len(result.Requests)
		mu.Unlock()
		_ = logger.Log("request_handled", map[string]any{
			"label":           record.Label,
			"method":          record.Method,
			"path":            record.Path,
			"remote_addr":     record.RemoteAddr,
			"proto":           record.Proto,
			"tls_alpn":        record.TLSALPN,
			"request_bytes":   record.RequestBytes,
			"response_bytes":  record.ResponseBytes,
			"workload":        record.Workload,
			"stream_response": record.StreamResponse,
			"chunk_bytes":     record.ChunkBytes,
			"chunk_delay_ms":  record.ChunkDelayMillis,
			"count":           count,
		})
		if err := writeWorkloadResponse(w, status, response, record.ResponseContentType, record.ResponseHeaders, record.StreamResponse, record.ChunkBytes, time.Duration(record.ChunkDelayMillis)*time.Millisecond); err != nil {
			_ = logger.Log("response_write_error", map[string]any{
				"label": record.Label,
				"error": err.Error(),
			})
		}
	})

	h3Server := &http3.Server{
		TLSConfig:  tlsConf,
		QUICConfig: quicConf,
		Handler:    handler,
	}
	serveErr := make(chan error, 2)
	go func() {
		serveErr <- h3Server.ServeListener(listener)
	}()

	var tcpServer *http.Server
	var tcpListener net.Listener
	if tcpAddr != "" {
		tcpTLSConf := tlsConf.Clone()
		tcpTLSConf.NextProtos = []string{"http/1.1"}
		tcpListener, err = tls.Listen("tcp", tcpAddr, tcpTLSConf)
		if err != nil {
			result.Error = err.Error()
			result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
			return result, err
		}
		defer tcpListener.Close()
		tcpServer = &http.Server{Handler: handler}
		go func() {
			serveErr <- tcpServer.Serve(tcpListener)
		}()
	}

	_ = logger.Log("listening", map[string]any{
		"addr":                listener.Addr().String(),
		"qlog_dir":            qlogDir,
		"result":              resultPath,
		"timeout_ms":          timeout.Milliseconds(),
		"completion_grace_ms": completionGrace.Milliseconds(),
		"connection_id_mode":  result.ConnectionIDMode,
		"aws_server_id":       result.AWSServerID,
		"expected_requests":   expectedRequests,
		"tcp_addr":            tcpAddr,
		"alt_svc":             altSvc,
	})

	timer := time.NewTimer(timeout)
	defer timer.Stop()
	select {
	case <-done:
		result.OK = true
	case err := <-serveErr:
		if err != nil && err != http.ErrServerClosed {
			result.Error = err.Error()
			result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
			return result, err
		}
	case <-timer.C:
		err := fmt.Errorf("timed out waiting for %d requests", expectedRequests)
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}

	if completionGrace > 0 {
		time.Sleep(completionGrace)
	}
	_ = h3Server.Close()
	if tcpServer != nil {
		_ = tcpServer.Close()
	}
	if tcpListener != nil {
		_ = tcpListener.Close()
	}
	_ = listener.Close()
	result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
	_ = logger.Log("server_success", map[string]any{
		"request_count": len(result.Requests),
	})
	return result, nil
}

func handleWorkloadRequest(r *http.Request) (requestRecord, int, []byte) {
	record := requestRecord{
		Method:     r.Method,
		Path:       r.URL.Path,
		RemoteAddr: r.RemoteAddr,
		Proto:      r.Proto,
		HandledAt:  time.Now().UTC().Format(time.RFC3339Nano),
	}
	if r.TLS != nil {
		record.TLSALPN = r.TLS.NegotiatedProtocol
	}
	label := r.URL.Query().Get("label")
	if label == "" {
		label = r.Header.Get("X-Experiment-Label")
	}
	record.Label = label

	switch {
	case r.Method == http.MethodPost && r.URL.Path == "/upload":
		record.Workload = "upload"
		raw, err := io.ReadAll(r.Body)
		if err != nil {
			return record, http.StatusInternalServerError, []byte(err.Error())
		}
		record.RequestBytes = len(raw)
		decoded, err := common.DecodeMessage(raw)
		if err != nil {
			return record, http.StatusBadRequest, []byte(err.Error())
		}
		record.Label = decoded.Header.Label
		record.RequestBytes = decoded.Header.PayloadBytes
		record.RequestSHA256 = decoded.Header.SHA256
		record.ResponseBytes = len("ok\n")
		record.DecodeSuccessful = true
		return record, http.StatusOK, []byte("ok\n")
	case r.Method == http.MethodPost && r.URL.Path == "/upload-sink":
		record.Workload = "upload-sink"
		raw, err := io.ReadAll(r.Body)
		if err != nil {
			return record, http.StatusInternalServerError, []byte(err.Error())
		}
		if label == "" {
			label = "upload-sink"
		}
		body, _ := json.Marshal(map[string]any{
			"ok":         true,
			"label":      label,
			"bytes":      len(raw),
			"sha256":     sha256Hex(raw),
			"handled_at": record.HandledAt,
		})
		record.Label = label
		record.RequestBytes = len(raw)
		record.RequestSHA256 = sha256Hex(raw)
		record.ResponseBytes = len(body)
		record.ResponseContentType = "application/json"
		record.DecodeSuccessful = true
		return record, http.StatusOK, body
	case r.Method == http.MethodGet && r.URL.Path == "/download":
		record.Workload = "download"
		record.ResponseContentType = "application/octet-stream"
		size := 65536
		if value := r.URL.Query().Get("bytes"); value != "" {
			parsed, err := strconv.Atoi(value)
			if err != nil || parsed < 0 {
				return record, http.StatusBadRequest, []byte("invalid bytes parameter")
			}
			size = parsed
		}
		if label == "" {
			label = "download"
		}
		record.StreamResponse = r.URL.Query().Get("stream") == "true"
		record.ChunkBytes = queryInt(r, "chunk_bytes", 16384)
		record.ChunkDelayMillis = int64(queryInt(r, "delay_ms", 0))
		msg, header, err := common.BuildMessage(label, size)
		if err != nil {
			return record, http.StatusInternalServerError, []byte(err.Error())
		}
		record.Label = header.Label
		record.ResponseBytes = header.PayloadBytes
		record.ResponseSHA256 = header.SHA256
		record.DecodeSuccessful = true
		return record, http.StatusOK, msg
	case r.Method == http.MethodGet && r.URL.Path == "/browser-sequence":
		record.Workload = "browser-sequence"
		record.ResponseContentType = "text/html; charset=utf-8"
		resources := queryInt(r, "resources", 2)
		if resources > 10 {
			resources = 10
		}
		size := queryInt(r, "bytes", 128)
		if label == "" {
			label = "chrome-sequence"
		}
		html := buildBrowserSequenceHTML(label, resources, size)
		record.ResponseBytes = len(html)
		record.DecodeSuccessful = true
		return record, http.StatusOK, []byte(html)
	case r.Method == http.MethodGet && r.URL.Path == "/browser-poll":
		record.Workload = "browser-poll"
		record.ResponseContentType = "text/html; charset=utf-8"
		count := queryInt(r, "count", 5)
		if count > 100 {
			count = 100
		}
		intervalMillis := queryInt(r, "interval_ms", 500)
		if intervalMillis > 30000 {
			intervalMillis = 30000
		}
		retryAttempts := queryInt(r, "retry_attempts", 0)
		if retryAttempts > 5 {
			retryAttempts = 5
		}
		retryDelayMillis := queryInt(r, "retry_delay_ms", 500)
		if retryDelayMillis > 60000 {
			retryDelayMillis = 60000
		}
		if label == "" {
			label = "chrome-poll"
		}
		html := buildBrowserPollHTML(label, count, intervalMillis, retryAttempts, retryDelayMillis)
		record.ResponseBytes = len(html)
		record.DecodeSuccessful = true
		return record, http.StatusOK, []byte(html)
	case r.Method == http.MethodGet && r.URL.Path == "/poll":
		record.Workload = "poll"
		record.ResponseContentType = "application/json"
		if label == "" {
			label = "poll"
		}
		body, _ := json.Marshal(map[string]any{
			"ok":         true,
			"label":      label,
			"index":      r.URL.Query().Get("i"),
			"handled_at": record.HandledAt,
		})
		record.Label = label
		record.ResponseBytes = len(body)
		record.DecodeSuccessful = true
		return record, http.StatusOK, body
	case r.Method == http.MethodGet && r.URL.Path == "/browser-media-segments":
		record.Workload = "browser-media-segments"
		record.ResponseContentType = "text/html; charset=utf-8"
		count := queryInt(r, "count", 8)
		if count > 200 {
			count = 200
		}
		intervalMillis := queryInt(r, "interval_ms", 1000)
		if intervalMillis > 60000 {
			intervalMillis = 60000
		}
		size := queryInt(r, "bytes", 32768)
		if size > 16*1024*1024 {
			size = 16 * 1024 * 1024
		}
		segmentDurationMillis := queryInt(r, "segment_duration_ms", 0)
		if segmentDurationMillis > 60000 {
			segmentDurationMillis = 60000
		}
		segmentChunks := queryInt(r, "segment_chunks", 1)
		if segmentChunks > 100 {
			segmentChunks = 100
		}
		retryAttempts := queryInt(r, "retry_attempts", 0)
		if retryAttempts > 5 {
			retryAttempts = 5
		}
		retryDelayMillis := queryInt(r, "retry_delay_ms", 500)
		if retryDelayMillis > 60000 {
			retryDelayMillis = 60000
		}
		if label == "" {
			label = "browser-media"
		}
		html := buildBrowserMediaSegmentsHTML(label, count, intervalMillis, size, segmentDurationMillis, segmentChunks, retryAttempts, retryDelayMillis)
		record.ResponseBytes = len(html)
		record.DecodeSuccessful = true
		return record, http.StatusOK, []byte(html)
	case r.Method == http.MethodGet && r.URL.Path == "/media-segment":
		record.Workload = "media-segment"
		record.ResponseContentType = "application/octet-stream"
		size := queryInt(r, "bytes", 32768)
		if size > 16*1024*1024 {
			size = 16 * 1024 * 1024
		}
		durationMillis := queryInt(r, "duration_ms", 0)
		if durationMillis > 60000 {
			durationMillis = 60000
		}
		chunks := queryInt(r, "chunks", 1)
		if chunks > 100 {
			chunks = 100
		}
		if label == "" {
			label = "media-segment"
		}
		msg, header, err := common.BuildMessage(label, size)
		if err != nil {
			return record, http.StatusInternalServerError, []byte(err.Error())
		}
		record.Label = header.Label
		record.ResponseBytes = header.PayloadBytes
		record.ResponseSHA256 = header.SHA256
		record.StreamResponse = durationMillis > 0 || queryBool(r, "stream", false)
		record.ChunkBytes = len(msg) / chunks
		if record.ChunkBytes <= 0 {
			record.ChunkBytes = 1
		}
		if chunks > 0 {
			delayMillis := durationMillis / chunks
			if durationMillis > 0 && delayMillis <= 0 {
				delayMillis = 1
			}
			record.ChunkDelayMillis = int64(delayMillis)
		}
		record.DecodeSuccessful = true
		return record, http.StatusOK, msg
	case r.Method == http.MethodGet && r.URL.Path == "/browser-range-download":
		record.Workload = "browser-range-download"
		record.ResponseContentType = "text/html; charset=utf-8"
		totalBytes := queryInt(r, "bytes", 1048576)
		if totalBytes > 16*1024*1024 {
			totalBytes = 16 * 1024 * 1024
		}
		rangeBytes := queryInt(r, "range_bytes", 131072)
		if rangeBytes > totalBytes {
			rangeBytes = totalBytes
		}
		rangeDurationMillis := queryInt(r, "range_duration_ms", 250)
		if rangeDurationMillis > 60000 {
			rangeDurationMillis = 60000
		}
		rangeChunks := queryInt(r, "range_chunks", 2)
		if rangeChunks > 100 {
			rangeChunks = 100
		}
		retryAttempts := queryInt(r, "retry_attempts", 0)
		if retryAttempts > 5 {
			retryAttempts = 5
		}
		retryDelayMillis := queryInt(r, "retry_delay_ms", 500)
		if retryDelayMillis > 60000 {
			retryDelayMillis = 60000
		}
		if label == "" {
			label = "browser-range-download"
		}
		html := buildBrowserRangeDownloadHTML(label, totalBytes, rangeBytes, rangeDurationMillis, rangeChunks, retryAttempts, retryDelayMillis)
		record.ResponseBytes = len(html)
		record.DecodeSuccessful = true
		return record, http.StatusOK, []byte(html)
	case r.Method == http.MethodGet && r.URL.Path == "/range-download":
		record.Workload = "range-download"
		record.ResponseContentType = "application/octet-stream"
		totalBytes := queryInt(r, "bytes", 1048576)
		if totalBytes > 16*1024*1024 {
			totalBytes = 16 * 1024 * 1024
		}
		durationMillis := queryInt(r, "duration_ms", 250)
		if durationMillis > 60000 {
			durationMillis = 60000
		}
		chunks := queryInt(r, "chunks", 1)
		if chunks > 100 {
			chunks = 100
		}
		if label == "" {
			label = "range-download"
		}
		payload := common.DeterministicPayload(label, totalBytes)
		start, end, partial, err := parseRangeHeader(r.Header.Get("Range"), len(payload))
		if err != nil {
			return record, http.StatusRequestedRangeNotSatisfiable, []byte(err.Error())
		}
		response := payload[start : end+1]
		record.Label = label
		record.ResponseBytes = len(response)
		record.ResponseSHA256 = sha256Hex(response)
		record.StreamResponse = durationMillis > 0 || queryBool(r, "stream", false)
		record.ChunkBytes = len(response) / chunks
		if record.ChunkBytes <= 0 {
			record.ChunkBytes = 1
		}
		if chunks > 0 {
			delayMillis := durationMillis / chunks
			if durationMillis > 0 && delayMillis <= 0 {
				delayMillis = 1
			}
			record.ChunkDelayMillis = int64(delayMillis)
		}
		record.ResponseHeaders = map[string]string{"Accept-Ranges": "bytes"}
		if partial {
			record.ResponseHeaders["Content-Range"] = fmt.Sprintf("bytes %d-%d/%d", start, end, len(payload))
		}
		record.DecodeSuccessful = true
		if partial {
			return record, http.StatusPartialContent, response
		}
		return record, http.StatusOK, response
	case r.Method == http.MethodGet && r.URL.Path == "/browser-slow":
		record.Workload = "browser-slow"
		record.ResponseContentType = "text/html; charset=utf-8"
		durationMillis := queryInt(r, "duration_ms", 6000)
		if durationMillis > 60000 {
			durationMillis = 60000
		}
		chunks := queryInt(r, "chunks", 6)
		if chunks > 100 {
			chunks = 100
		}
		if label == "" {
			label = "chrome-slow"
		}
		html := buildBrowserSlowHTML(label, durationMillis, chunks)
		record.ResponseBytes = len(html)
		record.DecodeSuccessful = true
		return record, http.StatusOK, []byte(html)
	case r.Method == http.MethodGet && r.URL.Path == "/browser-downlink":
		record.Workload = "browser-downlink"
		record.ResponseContentType = "text/html; charset=utf-8"
		durationMillis := queryInt(r, "duration_ms", 15000)
		if durationMillis > 120000 {
			durationMillis = 120000
		}
		chunks := queryInt(r, "chunks", 15)
		if chunks > 200 {
			chunks = 200
		}
		size := queryInt(r, "bytes", 65536)
		if size > 16*1024*1024 {
			size = 16 * 1024 * 1024
		}
		heartbeat := queryBool(r, "heartbeat", false)
		heartbeatDelayMillis := queryInt(r, "heartbeat_delay_ms", durationMillis/2)
		if heartbeatDelayMillis > durationMillis {
			heartbeatDelayMillis = durationMillis
		}
		retryAttempts := queryInt(r, "retry_attempts", 0)
		if retryAttempts > 5 {
			retryAttempts = 5
		}
		retryDelayMillis := queryInt(r, "retry_delay_ms", 500)
		if retryDelayMillis > 60000 {
			retryDelayMillis = 60000
		}
		streamTimeoutMillis := queryInt(r, "stream_timeout_ms", 0)
		if streamTimeoutMillis > 60000 {
			streamTimeoutMillis = 60000
		}
		if label == "" {
			label = "browser-downlink"
		}
		html := buildBrowserDownlinkHTML(label, durationMillis, chunks, size, heartbeat, heartbeatDelayMillis, retryAttempts, retryDelayMillis, streamTimeoutMillis)
		record.ResponseBytes = len(html)
		record.DecodeSuccessful = true
		return record, http.StatusOK, []byte(html)
	case r.Method == http.MethodGet && r.URL.Path == "/browser-upload":
		record.Workload = "browser-upload"
		record.ResponseContentType = "text/html; charset=utf-8"
		durationMillis := queryInt(r, "duration_ms", 6000)
		if durationMillis > 120000 {
			durationMillis = 120000
		}
		chunks := queryInt(r, "chunks", 6)
		if chunks > 200 {
			chunks = 200
		}
		size := queryInt(r, "bytes", 65536)
		if size > 16*1024*1024 {
			size = 16 * 1024 * 1024
		}
		retryAttempts := queryInt(r, "retry_attempts", 0)
		if retryAttempts > 5 {
			retryAttempts = 5
		}
		retryDelayMillis := queryInt(r, "retry_delay_ms", 500)
		if retryDelayMillis > 60000 {
			retryDelayMillis = 60000
		}
		if label == "" {
			label = "browser-upload"
		}
		html := buildBrowserUploadHTML(label, durationMillis, chunks, size, retryAttempts, retryDelayMillis)
		record.ResponseBytes = len(html)
		record.DecodeSuccessful = true
		return record, http.StatusOK, []byte(html)
	case r.Method == http.MethodGet && r.URL.Path == "/downlink-stream":
		record.Workload = "downlink-stream"
		record.ResponseContentType = "application/octet-stream"
		durationMillis := queryInt(r, "duration_ms", 15000)
		if durationMillis > 120000 {
			durationMillis = 120000
		}
		chunks := queryInt(r, "chunks", 15)
		if chunks > 200 {
			chunks = 200
		}
		size := queryInt(r, "bytes", 65536)
		if size > 16*1024*1024 {
			size = 16 * 1024 * 1024
		}
		if label == "" {
			label = "downlink-stream"
		}
		msg, header, err := common.BuildMessage(label, size)
		if err != nil {
			return record, http.StatusInternalServerError, []byte(err.Error())
		}
		delayMillis := durationMillis / chunks
		if delayMillis <= 0 {
			delayMillis = 1
		}
		record.Label = header.Label
		record.ResponseBytes = header.PayloadBytes
		record.ResponseSHA256 = header.SHA256
		record.StreamResponse = true
		record.ChunkBytes = len(msg) / chunks
		if record.ChunkBytes <= 0 {
			record.ChunkBytes = 1
		}
		record.ChunkDelayMillis = int64(delayMillis)
		record.DecodeSuccessful = true
		return record, http.StatusOK, msg
	case r.Method == http.MethodGet && r.URL.Path == "/heartbeat":
		record.Workload = "heartbeat"
		record.ResponseContentType = "application/json"
		if label == "" {
			label = "heartbeat"
		}
		body, _ := json.Marshal(map[string]any{
			"ok":         true,
			"label":      label,
			"handled_at": record.HandledAt,
		})
		record.Label = label
		record.ResponseBytes = len(body)
		record.DecodeSuccessful = true
		return record, http.StatusOK, body
	case r.Method == http.MethodGet && r.URL.Path == "/slow-js":
		record.Workload = "slow-js"
		record.ResponseContentType = "application/javascript"
		durationMillis := queryInt(r, "duration_ms", 6000)
		if durationMillis > 60000 {
			durationMillis = 60000
		}
		chunks := queryInt(r, "chunks", 6)
		if chunks > 100 {
			chunks = 100
		}
		if label == "" {
			label = "slow-js"
		}
		delayMillis := durationMillis / chunks
		if delayMillis <= 0 {
			delayMillis = 1
		}
		body := buildSlowJS(label, chunks)
		record.Label = label
		record.ResponseBytes = len(body)
		record.ResponseSHA256 = sha256Hex([]byte(body))
		record.StreamResponse = true
		record.ChunkBytes = len(body) / chunks
		if record.ChunkBytes <= 0 {
			record.ChunkBytes = 1
		}
		record.ChunkDelayMillis = int64(delayMillis)
		record.DecodeSuccessful = true
		return record, http.StatusOK, []byte(body)
	case r.Method == http.MethodGet && r.URL.Path == "/pixel":
		record.Workload = "pixel"
		record.ResponseContentType = "image/svg+xml"
		if label == "" {
			label = "pixel"
		}
		svg := buildPixelSVG(label)
		record.Label = label
		record.ResponseBytes = len(svg)
		record.ResponseSHA256 = sha256Hex([]byte(svg))
		record.DecodeSuccessful = true
		return record, http.StatusOK, []byte(svg)
	default:
		body, _ := json.Marshal(map[string]string{"error": "not found"})
		return record, http.StatusNotFound, body
	}
}

func writeWorkloadResponse(w http.ResponseWriter, status int, response []byte, contentType string, headers map[string]string, stream bool, chunkBytes int, chunkDelay time.Duration) error {
	if contentType == "" {
		contentType = "application/octet-stream"
	}
	w.Header().Set("Content-Type", contentType)
	w.Header().Set("Content-Length", strconv.Itoa(len(response)))
	for key, value := range headers {
		w.Header().Set(key, value)
	}
	w.WriteHeader(status)
	if !stream || (status != http.StatusOK && status != http.StatusPartialContent) {
		_, err := w.Write(response)
		return err
	}
	if chunkBytes <= 0 {
		chunkBytes = 16384
	}
	flusher, _ := w.(http.Flusher)
	for offset := 0; offset < len(response); {
		end := offset + chunkBytes
		if end > len(response) {
			end = len(response)
		}
		if _, err := w.Write(response[offset:end]); err != nil {
			return err
		}
		if flusher != nil {
			flusher.Flush()
		}
		offset = end
		if chunkDelay > 0 && offset < len(response) {
			time.Sleep(chunkDelay)
		}
	}
	return nil
}

func buildBrowserSequenceHTML(label string, resources, size int) string {
	body := "<!doctype html><html><head><meta charset=\"utf-8\"><title>Chrome H3 sequence</title><link rel=\"icon\" href=\"data:,\"></head><body>"
	body += "<h1>Chrome H3 sequence</h1>"
	body += "<ol>"
	for i := 1; i <= resources; i++ {
		resourceLabel := fmt.Sprintf("%s-%d", label, i)
		body += fmt.Sprintf("<li><img alt=\"%s\" src=\"/pixel?bytes=%d&label=%s\"></li>", html.EscapeString(resourceLabel), size, url.QueryEscape(resourceLabel))
	}
	body += "</ol>"
	body += "<script>document.body.dataset.sequenceReady = 'true';</script>"
	body += "</body></html>"
	return body
}

func buildBrowserPollHTML(label string, count, intervalMillis, retryAttempts, retryDelayMillis int) string {
	escapedLabel := html.EscapeString(label)
	queryLabel := url.QueryEscape(label)
	body := "<!doctype html><html><head><meta charset=\"utf-8\"><title>Chrome H3 poll</title><link rel=\"icon\" href=\"data:,\"></head><body>"
	body += fmt.Sprintf("<h1>Chrome H3 poll</h1><div id=\"status\" data-label=\"%s\">pending</div><ol id=\"events\"></ol>", escapedLabel)
	body += "<script>"
	body += fmt.Sprintf("const count=%d, interval=%d, label=%q,retryAttempts=%d,retryDelayMs=%d;", count, intervalMillis, queryLabel, retryAttempts, retryDelayMillis)
	body += "const sleep=(ms)=>new Promise((resolve)=>setTimeout(resolve,ms));"
	body += "const events=document.getElementById('events');"
	body += "async function fetchPoll(i,attempt){const res=await fetch(`/poll?label=${label}-${i}&i=${i}&attempt=${attempt}&ts=${Date.now()}`,{cache:'no-store'});const json=await res.json();return {status:res.status,label:json.label};}"
	body += "async function pollWithRetry(i){let lastError='';for(let attempt=1;attempt<=retryAttempts+1;attempt++){try{return {attempt,result:await fetchPoll(i,attempt)};}catch(error){lastError=String(error);document.body.dataset.pollLastError=lastError;document.body.dataset.pollLastErrorElapsedMs=String(Math.round(performance.now()-startedAt));if(attempt>retryAttempts){break;}await sleep(retryDelayMs);}}throw new Error(lastError||'poll failed');}"
	body += "const startedAt=performance.now();"
	body += "async function run(){let totalRetries=0;for(let i=1;i<=count;i++){const item=await pollWithRetry(i);totalRetries+=item.attempt-1;document.body.dataset.pollCompletedCount=String(i);document.body.dataset.pollRetriesUsed=String(totalRetries);const li=document.createElement('li');li.textContent=`${item.result.label}:${item.result.status}:attempt:${item.attempt}`;events.appendChild(li);await sleep(interval);}document.getElementById('status').textContent='complete';document.body.dataset.pollElapsedMs=String(Math.round(performance.now()-startedAt));document.body.dataset.pollComplete='true';}"
	body += "run().catch((error)=>{document.getElementById('status').textContent='error';document.body.dataset.pollErrorElapsedMs=String(Math.round(performance.now()-startedAt));document.body.dataset.pollError=String(error);});"
	body += "</script>"
	body += "</body></html>"
	return body
}

func buildBrowserMediaSegmentsHTML(label string, count, intervalMillis, size, segmentDurationMillis, segmentChunks, retryAttempts, retryDelayMillis int) string {
	escapedLabel := html.EscapeString(label)
	queryLabel := url.QueryEscape(label)
	segmentURLPrefix := fmt.Sprintf("/media-segment?bytes=%d&duration_ms=%d&chunks=%d&label=%s", size, segmentDurationMillis, segmentChunks, queryLabel)
	body := "<!doctype html><html><head><meta charset=\"utf-8\"><title>Chrome H3 media segments</title><link rel=\"icon\" href=\"data:,\"></head><body>"
	body += fmt.Sprintf("<h1>Chrome H3 media segments</h1><div id=\"status\" data-label=\"%s\">pending</div><ol id=\"events\"></ol>", escapedLabel)
	body += "<script>"
	body += fmt.Sprintf("const count=%d,interval=%d,segmentUrlPrefix=%q,retryAttempts=%d,retryDelayMs=%d;", count, intervalMillis, segmentURLPrefix, retryAttempts, retryDelayMillis)
	body += "const sleep=(ms)=>new Promise((resolve)=>setTimeout(resolve,ms));"
	body += "const events=document.getElementById('events');"
	body += "const startedAt=performance.now();"
	body += "async function fetchSegment(i,attempt){const res=await fetch(segmentUrlPrefix+'-'+i+'&segment='+i+'&attempt='+attempt+'&ts='+Date.now(),{cache:'no-store'});const buf=await res.arrayBuffer();if(!res.ok){throw new Error('segment status '+res.status);}return {status:res.status,bytes:buf.byteLength};}"
	body += "async function segmentWithRetry(i){let lastError='';for(let attempt=1;attempt<=retryAttempts+1;attempt++){try{return {attempt,result:await fetchSegment(i,attempt)};}catch(error){lastError=String(error);document.body.dataset.mediaLastError=lastError;document.body.dataset.mediaLastErrorElapsedMs=String(Math.round(performance.now()-startedAt));if(attempt>retryAttempts){break;}await sleep(retryDelayMs);}}throw new Error(lastError||'media segment failed');}"
	body += "async function run(){let totalRetries=0,totalBytes=0;for(let i=1;i<=count;i++){const item=await segmentWithRetry(i);totalRetries+=item.attempt-1;totalBytes+=item.result.bytes;document.body.dataset.mediaCompletedCount=String(i);document.body.dataset.mediaRetriesUsed=String(totalRetries);document.body.dataset.mediaBytes=String(totalBytes);const li=document.createElement('li');li.textContent=`segment:${i}:status:${item.result.status}:bytes:${item.result.bytes}:attempt:${item.attempt}`;events.appendChild(li);await sleep(interval);}document.getElementById('status').textContent='complete';document.body.dataset.mediaElapsedMs=String(Math.round(performance.now()-startedAt));document.body.dataset.mediaComplete='true';}"
	body += "run().catch((error)=>{document.getElementById('status').textContent='error';document.body.dataset.mediaErrorElapsedMs=String(Math.round(performance.now()-startedAt));document.body.dataset.mediaError=String(error);});"
	body += "</script>"
	body += "</body></html>"
	return body
}

func buildBrowserRangeDownloadHTML(label string, totalBytes, rangeBytes, rangeDurationMillis, rangeChunks, retryAttempts, retryDelayMillis int) string {
	escapedLabel := html.EscapeString(label)
	queryLabel := url.QueryEscape(label)
	rangeURL := fmt.Sprintf("/range-download?bytes=%d&duration_ms=%d&chunks=%d&label=%s", totalBytes, rangeDurationMillis, rangeChunks, queryLabel)
	body := "<!doctype html><html><head><meta charset=\"utf-8\"><title>Chrome H3 range download</title><link rel=\"icon\" href=\"data:,\"></head><body>"
	body += fmt.Sprintf("<h1>Chrome H3 range download</h1><div id=\"status\" data-label=\"%s\">pending</div><ol id=\"events\"></ol>", escapedLabel)
	body += "<script>"
	body += fmt.Sprintf("const totalBytes=%d,rangeBytes=%d,rangeUrl=%q,retryAttempts=%d,retryDelayMs=%d;", totalBytes, rangeBytes, rangeURL, retryAttempts, retryDelayMillis)
	body += "const sleep=(ms)=>new Promise((resolve)=>setTimeout(resolve,ms));"
	body += "const events=document.getElementById('events');"
	body += "const startedAt=performance.now();"
	body += "async function fetchRange(start,end,attempt){const res=await fetch(rangeUrl+'&start='+start+'&end='+end+'&attempt='+attempt+'&ts='+Date.now(),{cache:'no-store',headers:{Range:`bytes=${start}-${end}`}});const buf=await res.arrayBuffer();if(res.status!==206&&res.status!==200){throw new Error('range status '+res.status);}const expected=end-start+1;if(buf.byteLength!==expected){throw new Error('range length '+buf.byteLength+' expected '+expected);}return {status:res.status,bytes:buf.byteLength};}"
	body += "async function rangeWithRetry(start,end,index){let lastError='';for(let attempt=1;attempt<=retryAttempts+1;attempt++){try{return {attempt,result:await fetchRange(start,end,attempt)};}catch(error){lastError=String(error);document.body.dataset.rangeLastError=lastError;document.body.dataset.rangeLastErrorElapsedMs=String(Math.round(performance.now()-startedAt));if(attempt>retryAttempts){break;}await sleep(retryDelayMs);}}throw new Error(lastError||'range failed');}"
	body += "async function run(){let totalRetries=0,completedBytes=0,completedChunks=0;for(let start=0,index=1;start<totalBytes;start+=rangeBytes,index++){const end=Math.min(totalBytes-1,start+rangeBytes-1);const item=await rangeWithRetry(start,end,index);totalRetries+=item.attempt-1;completedBytes+=item.result.bytes;completedChunks=index;document.body.dataset.rangeCompletedBytes=String(completedBytes);document.body.dataset.rangeCompletedChunks=String(completedChunks);document.body.dataset.rangeRetriesUsed=String(totalRetries);const li=document.createElement('li');li.textContent=`range:${index}:${start}-${end}:status:${item.result.status}:bytes:${item.result.bytes}:attempt:${item.attempt}`;events.appendChild(li);}document.getElementById('status').textContent='complete';document.body.dataset.rangeElapsedMs=String(Math.round(performance.now()-startedAt));document.body.dataset.rangeComplete='true';}"
	body += "run().catch((error)=>{document.getElementById('status').textContent='error';document.body.dataset.rangeErrorElapsedMs=String(Math.round(performance.now()-startedAt));document.body.dataset.rangeError=String(error);});"
	body += "</script>"
	body += "</body></html>"
	return body
}

func buildBrowserSlowHTML(label string, durationMillis, chunks int) string {
	escapedLabel := html.EscapeString(label)
	queryLabel := url.QueryEscape(label)
	body := "<!doctype html><html><head><meta charset=\"utf-8\"><title>Chrome H3 slow</title><link rel=\"icon\" href=\"data:,\"></head><body>"
	body += fmt.Sprintf("<h1>Chrome H3 slow</h1><div id=\"status\" data-label=\"%s\">loading</div>", escapedLabel)
	body += fmt.Sprintf("<script src=\"/slow-js?duration_ms=%d&chunks=%d&label=%s\"></script>", durationMillis, chunks, queryLabel)
	body += "</body></html>"
	return body
}

func buildBrowserDownlinkHTML(label string, durationMillis, chunks, size int, heartbeat bool, heartbeatDelayMillis, retryAttempts, retryDelayMillis, streamTimeoutMillis int) string {
	escapedLabel := html.EscapeString(label)
	queryLabel := url.QueryEscape(label)
	streamURL := fmt.Sprintf("/downlink-stream?duration_ms=%d&chunks=%d&bytes=%d&label=%s-stream", durationMillis, chunks, size, queryLabel)
	heartbeatURL := fmt.Sprintf("/heartbeat?label=%s-heartbeat&ts=", queryLabel)
	body := "<!doctype html><html><head><meta charset=\"utf-8\"><title>Browser H3 downlink</title><link rel=\"icon\" href=\"data:,\"></head><body>"
	body += fmt.Sprintf("<h1>Browser H3 downlink</h1><div id=\"status\" data-label=\"%s\">loading</div><pre id=\"events\"></pre>", escapedLabel)
	body += "<script>"
	body += fmt.Sprintf("const streamUrl=%q, heartbeatUrl=%q, heartbeat=%t, heartbeatDelay=%d,retryAttempts=%d,retryDelayMs=%d,streamTimeoutMs=%d;", streamURL, heartbeatURL, heartbeat, heartbeatDelayMillis, retryAttempts, retryDelayMillis, streamTimeoutMillis)
	body += "const events=document.getElementById('events');"
	body += "const startedAt=performance.now();"
	body += "function note(line){events.textContent+=line+'\\n';}"
	body += "const sleep=(ms)=>new Promise((resolve)=>setTimeout(resolve,ms));"
	body += "async function readWithTimeout(reader,timeoutMs,controller){if(timeoutMs<=0){return await reader.read();}let timeoutId;try{return await Promise.race([reader.read(),new Promise((_,reject)=>{timeoutId=setTimeout(()=>{controller.abort();reject(new Error('stream timeout after '+timeoutMs+'ms'));},timeoutMs);})]);}finally{clearTimeout(timeoutId);}}"
	body += "async function attemptStream(attempt){const targetUrl=streamUrl+'&attempt='+attempt+'&ts='+Date.now();const controller=new AbortController();const res=await fetch(targetUrl,{cache:'no-store',signal:controller.signal});const reader=res.body.getReader();let total=0;document.body.dataset.downlinkAttempt=String(attempt);try{for(;;){const item=await readWithTimeout(reader,streamTimeoutMs,controller);if(item.done)break;total+=item.value.byteLength;document.body.dataset.downlinkBytes=String(total);note('attempt:'+attempt+':chunk:'+total);}return total;}finally{try{reader.releaseLock();}catch(error){}}}"
	body += "async function runStream(){let lastError='';for(let attempt=1;attempt<=retryAttempts+1;attempt++){try{const total=await attemptStream(attempt);document.body.dataset.downlinkBytes=String(total);document.body.dataset.downlinkElapsedMs=String(Math.round(performance.now()-startedAt));document.body.dataset.downlinkRetriesUsed=String(attempt-1);document.body.dataset.downlinkComplete='true';note('downlink:'+total+':attempt:'+attempt);document.getElementById('status').textContent='complete';return;}catch(error){lastError=String(error);document.body.dataset.downlinkLastError=lastError;document.body.dataset.downlinkLastErrorElapsedMs=String(Math.round(performance.now()-startedAt));note('stream-error:'+lastError+':attempt:'+attempt);if(attempt>retryAttempts){break;}await sleep(retryDelayMs);}}throw new Error(lastError||'downlink failed');}"
	body += "if(heartbeat){setTimeout(()=>{fetch(heartbeatUrl+Date.now(),{cache:'no-store'}).then((res)=>{document.body.dataset.heartbeatStatus=String(res.status);note('heartbeat:'+res.status);}).catch((error)=>{document.body.dataset.heartbeatError=String(error);note('heartbeat-error:'+error);});},heartbeatDelay);}"
	body += "runStream().catch((error)=>{document.getElementById('status').textContent='error';document.body.dataset.downlinkErrorElapsedMs=String(Math.round(performance.now()-startedAt));document.body.dataset.downlinkError=String(error);note('stream-error:'+error);});"
	body += "</script>"
	body += "</body></html>"
	return body
}

func buildBrowserUploadHTML(label string, durationMillis, chunks, size, retryAttempts, retryDelayMillis int) string {
	escapedLabel := html.EscapeString(label)
	queryLabel := url.QueryEscape(label)
	uploadURL := fmt.Sprintf("/upload-sink?label=%s-sink", queryLabel)
	body := "<!doctype html><html><head><meta charset=\"utf-8\"><title>Browser H3 upload</title><link rel=\"icon\" href=\"data:,\"></head><body>"
	body += fmt.Sprintf("<h1>Browser H3 upload</h1><div id=\"status\" data-label=\"%s\">loading</div><pre id=\"events\"></pre>", escapedLabel)
	body += "<script>"
	body += fmt.Sprintf("const uploadUrl=%q,totalBytes=%d,chunks=%d,durationMs=%d,retryAttempts=%d,retryDelayMs=%d;", uploadURL, size, chunks, durationMillis, retryAttempts, retryDelayMillis)
	body += "const events=document.getElementById('events');"
	body += "const startedAt=performance.now();"
	body += "function note(line){events.textContent+=line+'\\n';}"
	body += "const sleep=(ms)=>new Promise((resolve)=>setTimeout(resolve,ms));"
	body += "function chunk(index,size){const data=new Uint8Array(size);for(let i=0;i<size;i++){data[i]=(index+i)%251;}return data;}"
	body += "async function attemptUpload(attempt){let sent=0,index=0;const chunkBytes=Math.max(1,Math.ceil(totalBytes/chunks));const delay=Math.max(1,Math.floor(durationMs/chunks));document.body.dataset.uploadAttempt=String(attempt);"
	body += "const stream=new ReadableStream({async pull(controller){if(sent>=totalBytes){controller.close();return;}const next=Math.min(chunkBytes,totalBytes-sent);controller.enqueue(chunk(index,next));sent+=next;index+=1;document.body.dataset.uploadBytes=String(sent);note('attempt:'+attempt+':sent:'+sent);if(sent<totalBytes){await sleep(delay);}}});"
	body += "const targetUrl=uploadUrl+'&attempt='+attempt+'&ts='+Date.now();const res=await fetch(targetUrl,{method:'POST',body:stream,duplex:'half',cache:'no-store',headers:{'content-type':'application/octet-stream'}});const json=await res.json();return {status:res.status,bytes:json.bytes||0};}"
	body += "async function runUpload(){let lastError='';for(let attempt=1;attempt<=retryAttempts+1;attempt++){try{const result=await attemptUpload(attempt);if(result.status!==200||result.bytes!==totalBytes){throw new Error('unexpected upload response '+result.status+':'+result.bytes);}document.body.dataset.uploadStatus=String(result.status);document.body.dataset.uploadResponseBytes=String(result.bytes);document.body.dataset.uploadElapsedMs=String(Math.round(performance.now()-startedAt));document.body.dataset.uploadRetriesUsed=String(attempt-1);document.body.dataset.uploadComplete='true';note('upload:'+result.status+':'+result.bytes+':attempt:'+attempt);document.getElementById('status').textContent='complete';return;}catch(error){lastError=String(error);document.body.dataset.uploadLastError=lastError;document.body.dataset.uploadLastErrorElapsedMs=String(Math.round(performance.now()-startedAt));note('upload-error:'+lastError+':attempt:'+attempt);if(attempt>retryAttempts){break;}await sleep(retryDelayMs);}}throw new Error(lastError||'upload failed');}"
	body += "runUpload().catch((error)=>{document.getElementById('status').textContent='error';document.body.dataset.uploadErrorElapsedMs=String(Math.round(performance.now()-startedAt));document.body.dataset.uploadError=String(error);note('upload-final-error:'+error);});"
	body += "</script>"
	body += "</body></html>"
	return body
}

func buildSlowJS(label string, chunks int) string {
	body := ""
	for i := 1; i <= chunks; i++ {
		body += fmt.Sprintf("// %s chunk %03d\n", label, i)
	}
	body += fmt.Sprintf("document.body.dataset.slowLabel = %q;\n", label)
	body += "document.body.dataset.slowComplete = 'true';\n"
	body += "document.getElementById('status').textContent = 'complete';\n"
	return body
}

func buildPixelSVG(label string) string {
	return fmt.Sprintf("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1\" height=\"1\"><title>%s</title><rect width=\"1\" height=\"1\" fill=\"#0a84ff\"/></svg>", html.EscapeString(label))
}

func sha256Hex(data []byte) string {
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])
}

func queryInt(r *http.Request, key string, fallback int) int {
	value := r.URL.Query().Get(key)
	if value == "" {
		return fallback
	}
	parsed, err := strconv.Atoi(value)
	if err != nil || parsed <= 0 {
		return fallback
	}
	return parsed
}

func queryBool(r *http.Request, key string, fallback bool) bool {
	value := r.URL.Query().Get(key)
	if value == "" {
		return fallback
	}
	parsed, err := strconv.ParseBool(value)
	if err != nil {
		return fallback
	}
	return parsed
}

func parseRangeHeader(header string, size int) (int, int, bool, error) {
	if header == "" {
		return 0, size - 1, false, nil
	}
	if !strings.HasPrefix(header, "bytes=") {
		return 0, 0, false, fmt.Errorf("unsupported range unit")
	}
	rangeSpec := strings.TrimPrefix(header, "bytes=")
	if strings.Contains(rangeSpec, ",") {
		return 0, 0, false, fmt.Errorf("multiple ranges are not supported")
	}
	parts := strings.SplitN(rangeSpec, "-", 2)
	if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
		return 0, 0, false, fmt.Errorf("invalid range")
	}
	start, err := strconv.Atoi(parts[0])
	if err != nil {
		return 0, 0, false, fmt.Errorf("invalid range start")
	}
	end, err := strconv.Atoi(parts[1])
	if err != nil {
		return 0, 0, false, fmt.Errorf("invalid range end")
	}
	if start < 0 || end < start || start >= size {
		return 0, 0, false, fmt.Errorf("range out of bounds")
	}
	if end >= size {
		end = size - 1
	}
	return start, end, true, nil
}
