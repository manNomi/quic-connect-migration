package main

import (
	"crypto/sha256"
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
	"sync"
	"time"

	"github.com/quic-go/quic-go"
	"github.com/quic-go/quic-go/http3"
	h3qlog "github.com/quic-go/quic-go/http3/qlog"

	"quic-cm/quic-go-min-repro/internal/common"
)

type requestRecord struct {
	Label               string `json:"label"`
	Method              string `json:"method"`
	Path                string `json:"path"`
	RemoteAddr          string `json:"remote_addr"`
	RequestBytes        int    `json:"request_bytes"`
	RequestSHA256       string `json:"request_sha256,omitempty"`
	ResponseBytes       int    `json:"response_bytes"`
	ResponseSHA256      string `json:"response_sha256,omitempty"`
	ResponseContentType string `json:"response_content_type,omitempty"`
	HandledAt           string `json:"handled_at"`
	Workload            string `json:"workload"`
	StreamResponse      bool   `json:"stream_response,omitempty"`
	ChunkBytes          int    `json:"chunk_bytes,omitempty"`
	ChunkDelayMillis    int64  `json:"chunk_delay_millis,omitempty"`
	DecodeSuccessful    bool   `json:"decode_successful"`
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
	timeout := flag.Duration("timeout", 30*time.Second, "overall server timeout")
	completionGrace := flag.Duration("completion-grace", 500*time.Millisecond, "grace period after expected requests before server close")
	serverIDHex := flag.String("server-id", "", "optional AWS NLB QUIC Server ID as 16 hex chars")
	expectedRequests := flag.Int("expected-requests", 2, "number of HTTP/3 requests to wait for before exiting")
	flag.Parse()

	result, err := run(*addr, *logPath, *resultPath, *keyLogPath, *qlogDir, *timeout, *completionGrace, *serverIDHex, *expectedRequests)
	if writeErr := common.WriteJSONFile(*resultPath, result); writeErr != nil {
		log.Printf("write result: %v", writeErr)
	}
	if err != nil {
		log.Fatal(err)
	}
}

func run(addr, logPath, resultPath, keyLogPath, qlogDir string, timeout, completionGrace time.Duration, serverIDHex string, expectedRequests int) (serverResult, error) {
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
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
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
			"request_bytes":   record.RequestBytes,
			"response_bytes":  record.ResponseBytes,
			"workload":        record.Workload,
			"stream_response": record.StreamResponse,
			"chunk_bytes":     record.ChunkBytes,
			"chunk_delay_ms":  record.ChunkDelayMillis,
			"count":           count,
		})
		if err := writeWorkloadResponse(w, status, response, record.ResponseContentType, record.StreamResponse, record.ChunkBytes, time.Duration(record.ChunkDelayMillis)*time.Millisecond); err != nil {
			_ = logger.Log("response_write_error", map[string]any{
				"label": record.Label,
				"error": err.Error(),
			})
		}
		if count >= expectedRequests {
			doneOnce.Do(func() { close(done) })
		}
	})

	server := &http3.Server{
		TLSConfig:  tlsConf,
		QUICConfig: quicConf,
		Handler:    handler,
	}
	serveErr := make(chan error, 1)
	go func() {
		serveErr <- server.ServeListener(listener)
	}()

	_ = logger.Log("listening", map[string]any{
		"addr":                listener.Addr().String(),
		"qlog_dir":            qlogDir,
		"result":              resultPath,
		"timeout_ms":          timeout.Milliseconds(),
		"completion_grace_ms": completionGrace.Milliseconds(),
		"connection_id_mode":  result.ConnectionIDMode,
		"aws_server_id":       result.AWSServerID,
		"expected_requests":   expectedRequests,
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
		err := fmt.Errorf("timed out waiting for %d HTTP/3 requests", expectedRequests)
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}

	if completionGrace > 0 {
		time.Sleep(completionGrace)
	}
	_ = server.Close()
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
		HandledAt:  time.Now().UTC().Format(time.RFC3339Nano),
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
	case r.Method == http.MethodGet && r.URL.Path == "/pixel":
		record.Workload = "pixel"
		record.ResponseContentType = "image/svg+xml"
		if label == "" {
			label = "pixel"
		}
		svg := buildPixelSVG(label)
		sum := sha256.Sum256([]byte(svg))
		record.Label = label
		record.ResponseBytes = len(svg)
		record.ResponseSHA256 = hex.EncodeToString(sum[:])
		record.DecodeSuccessful = true
		return record, http.StatusOK, []byte(svg)
	default:
		body, _ := json.Marshal(map[string]string{"error": "not found"})
		return record, http.StatusNotFound, body
	}
}

func writeWorkloadResponse(w http.ResponseWriter, status int, response []byte, contentType string, stream bool, chunkBytes int, chunkDelay time.Duration) error {
	if contentType == "" {
		contentType = "application/octet-stream"
	}
	w.Header().Set("Content-Type", contentType)
	w.Header().Set("Content-Length", strconv.Itoa(len(response)))
	w.WriteHeader(status)
	if !stream || status != http.StatusOK {
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

func buildPixelSVG(label string) string {
	return fmt.Sprintf("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1\" height=\"1\"><title>%s</title><rect width=\"1\" height=\"1\" fill=\"#0a84ff\"/></svg>", html.EscapeString(label))
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
