package main

import (
	"bytes"
	"context"
	"crypto/tls"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"time"

	"github.com/quic-go/quic-go"
	"github.com/quic-go/quic-go/http3"
	h3qlog "github.com/quic-go/quic-go/http3/qlog"

	"quic-cm/quic-go-min-repro/internal/common"
)

type h3TaskResult struct {
	Label                   string `json:"label"`
	Method                  string `json:"method"`
	Path                    string `json:"path"`
	RequestBytes            int    `json:"request_bytes"`
	RequestSHA256           string `json:"request_sha256,omitempty"`
	ResponseBytes           int    `json:"response_bytes"`
	ResponseSHA256          string `json:"response_sha256,omitempty"`
	StatusCode              int    `json:"status_code"`
	MigrationTriggered      bool   `json:"migration_triggered,omitempty"`
	MigrationAtBytes        int    `json:"migration_at_bytes,omitempty"`
	MigrationStartedAt      string `json:"migration_started_at,omitempty"`
	MigrationCompletedAt    string `json:"migration_completed_at,omitempty"`
	MigrationLocalAddrAfter string `json:"migration_local_addr_after,omitempty"`
	StartedAt               string `json:"started_at"`
	CompletedAt             string `json:"completed_at"`
}

type clientResult struct {
	Role                           string         `json:"role"`
	OK                             bool           `json:"ok"`
	Mode                           string         `json:"mode"`
	StartedAt                      string         `json:"started_at"`
	CompletedAt                    string         `json:"completed_at"`
	ServerAddr                     string         `json:"server_addr"`
	Authority                      string         `json:"authority"`
	SocketALocalAddr               string         `json:"socket_a_local_addr"`
	SocketBLocalAddr               string         `json:"socket_b_local_addr"`
	ConnectionLocalAddrAfterDial   string         `json:"connection_local_addr_after_dial"`
	ConnectionLocalAddrAfterProbe  string         `json:"connection_local_addr_after_probe"`
	ConnectionLocalAddrAfterSwitch string         `json:"connection_local_addr_after_switch"`
	ConnectionLocalAddrAfterAfter  string         `json:"connection_local_addr_after_after_request"`
	BindAddr                       string         `json:"bind_addr"`
	MigrationAtBytes               int            `json:"migration_at_bytes,omitempty"`
	ChunkBytes                     int            `json:"chunk_bytes,omitempty"`
	ChunkDelayMillis               int64          `json:"chunk_delay_millis,omitempty"`
	SwitchBeforeProbeError         string         `json:"switch_before_probe_error"`
	SwitchBeforeProbeMatched       bool           `json:"switch_before_probe_matched"`
	ProbeDurationMillis            int64          `json:"probe_duration_millis"`
	LocalAddrChangedToSocketB      bool           `json:"local_addr_changed_to_socket_b"`
	Tasks                          []h3TaskResult `json:"tasks"`
	Error                          string         `json:"error,omitempty"`
}

type migrationPath struct {
	udp  *net.UDPConn
	tr   *quic.Transport
	path *quic.Path
}

type migrationEvent struct {
	Triggered      bool
	AtBytes        int
	StartedAt      string
	CompletedAt    string
	LocalAddrAfter string
}

type throttledTriggerReader struct {
	data       []byte
	offset     int
	chunkBytes int
	chunkDelay time.Duration
	triggerAt  int
	triggered  bool
	trigger    func(bytesSeen int) error
}

func main() {
	server := flag.String("server", "127.0.0.1:4243", "server UDP address")
	bindAddr := flag.String("bind", "0.0.0.0:0", "local UDP bind address for both client paths")
	authority := flag.String("authority", "quic-cm-repro.local", "HTTP/3 request authority")
	payloadBytes := flag.Int("payload-bytes", 65536, "payload size per upload/download task")
	probeTimeout := flag.Duration("probe-timeout", 3*time.Second, "path probe timeout")
	logPath := flag.String("log", "artifacts/logs/h3client.jsonl", "JSONL log path")
	resultPath := flag.String("result", "artifacts/results/h3client.json", "result JSON path")
	keyLogPath := flag.String("keylog", "", "TLS key log path")
	qlogDir := flag.String("qlog-dir", "artifacts/qlog", "qlog output directory")
	mode := flag.String("mode", "upload-download", "experiment mode: upload-download, midflight-upload, midflight-download")
	timeout := flag.Duration("timeout", 30*time.Second, "overall client timeout")
	postSendWait := flag.Duration("post-send-wait", 0, "optional wait after final request before closing connection")
	migrationAtBytes := flag.Int("migration-at-bytes", 0, "byte threshold for mid-flight migration; 0 means approximately halfway")
	chunkBytes := flag.Int("chunk-bytes", 16384, "maximum body chunk size for mid-flight workloads")
	chunkDelay := flag.Duration("chunk-delay", 2*time.Millisecond, "delay after each body chunk for mid-flight workloads")
	flag.Parse()

	result, err := run(
		*server,
		*bindAddr,
		*authority,
		*payloadBytes,
		*probeTimeout,
		*logPath,
		*resultPath,
		*keyLogPath,
		*qlogDir,
		*mode,
		*timeout,
		*postSendWait,
		*migrationAtBytes,
		*chunkBytes,
		*chunkDelay,
	)
	if writeErr := common.WriteJSONFile(*resultPath, result); writeErr != nil {
		log.Printf("write result: %v", writeErr)
	}
	if err != nil {
		log.Fatal(err)
	}
}

func run(server, bindAddr, authority string, payloadBytes int, probeTimeout time.Duration, logPath, resultPath, keyLogPath, qlogDir, mode string, timeout, postSendWait time.Duration, migrationAtBytes, chunkBytes int, chunkDelay time.Duration) (clientResult, error) {
	started := time.Now().UTC()
	result := clientResult{
		Role:             "h3client",
		Mode:             mode,
		StartedAt:        started.Format(time.RFC3339Nano),
		ServerAddr:       server,
		Authority:        authority,
		BindAddr:         bindAddr,
		MigrationAtBytes: migrationAtBytes,
		ChunkBytes:       chunkBytes,
		ChunkDelayMillis: chunkDelay.Milliseconds(),
	}
	if !isSupportedMode(mode) {
		err := fmt.Errorf("unsupported mode %q", mode)
		return failResult(result, err)
	}
	if payloadBytes <= 0 {
		err := fmt.Errorf("payload-bytes must be positive")
		return failResult(result, err)
	}
	if chunkBytes <= 0 {
		err := fmt.Errorf("chunk-bytes must be positive")
		return failResult(result, err)
	}

	logger, err := common.NewJSONLLogger(logPath, "h3client")
	if err != nil {
		return failResult(result, err)
	}
	defer logger.Close()

	if qlogDir != "" {
		if err := common.EnsureDir(qlogDir); err != nil {
			return failResult(result, err)
		}
		if err := os.Setenv("QLOGDIR", qlogDir); err != nil {
			return failResult(result, err)
		}
	}

	tlsConf, keyLogCloser, err := clientH3TLSConfig(keyLogPath)
	if err != nil {
		return failResult(result, err)
	}
	if keyLogCloser != nil {
		defer keyLogCloser.Close()
	}

	serverAddr, err := net.ResolveUDPAddr("udp", server)
	if err != nil {
		return failResult(result, err)
	}

	udpA, err := listenLocalUDP(bindAddr)
	if err != nil {
		return failResult(result, err)
	}
	trA := &quic.Transport{Conn: udpA}
	defer trA.Close()
	result.SocketALocalAddr = udpA.LocalAddr().String()

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	quicConf := &quic.Config{
		Tracer:          h3qlog.DefaultConnectionTracer,
		MaxIdleTimeout:  30 * time.Second,
		KeepAlivePeriod: 5 * time.Second,
	}
	_ = logger.Log("dial_start", map[string]any{
		"server_addr":         server,
		"authority":           authority,
		"socket_a_local_addr": result.SocketALocalAddr,
		"payload_bytes":       payloadBytes,
		"qlog_dir":            qlogDir,
		"result":              resultPath,
		"mode":                mode,
	})
	conn, err := trA.Dial(ctx, serverAddr, tlsConf, quicConf)
	if err != nil {
		return failResult(result, err)
	}
	defer conn.CloseWithError(0, "h3 client done")
	result.ConnectionLocalAddrAfterDial = conn.LocalAddr().String()
	_ = logger.Log("dial_success", map[string]any{
		"connection_local_addr":  result.ConnectionLocalAddrAfterDial,
		"connection_remote_addr": conn.RemoteAddr().String(),
	})

	h3Transport := &http3.Transport{}
	h3Conn := h3Transport.NewClientConn(conn)
	defer h3Conn.CloseWithError(0, "h3 client done")

	switch mode {
	case "upload-download":
		err = runUploadDownloadMode(ctx, conn, h3Conn, bindAddr, authority, payloadBytes, probeTimeout, logger, &result)
	case "midflight-upload":
		err = runMidflightUploadMode(ctx, conn, h3Conn, bindAddr, authority, payloadBytes, probeTimeout, migrationAtBytes, chunkBytes, chunkDelay, logger, &result)
	case "midflight-download":
		err = runMidflightDownloadMode(ctx, conn, h3Conn, bindAddr, authority, payloadBytes, probeTimeout, migrationAtBytes, chunkBytes, chunkDelay, logger, &result)
	}
	if err != nil {
		return failResult(result, err)
	}

	if err := checkPostMigrationAddress(&result, logger); err != nil {
		return failResult(result, err)
	}
	if postSendWait > 0 {
		if err := waitAfterSend(ctx, postSendWait, logger); err != nil {
			return failResult(result, err)
		}
	}

	result.OK = true
	result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
	_ = logger.Log("client_success", map[string]any{
		"task_count": len(result.Tasks),
		"mode":       mode,
	})
	return result, nil
}

func runUploadDownloadMode(ctx context.Context, conn *quic.Conn, h3Conn *http3.ClientConn, bindAddr, authority string, payloadBytes int, probeTimeout time.Duration, logger *common.JSONLLogger, result *clientResult) error {
	before, err := doUpload(ctx, h3Conn, authority, "before", payloadBytes)
	if err != nil {
		return err
	}
	result.Tasks = append(result.Tasks, before)
	_ = logger.Log("h3_task_done", taskLogFields(before))

	migration, err := prepareMigrationPath(conn, bindAddr, result, logger)
	if err != nil {
		return err
	}
	defer migration.Close()
	if _, err := performMigration(ctx, conn, migration.path, probeTimeout, result, logger); err != nil {
		return err
	}

	after, err := doDownload(ctx, h3Conn, authority, "after", payloadBytes)
	if err != nil {
		return err
	}
	result.Tasks = append(result.Tasks, after)
	result.ConnectionLocalAddrAfterAfter = conn.LocalAddr().String()
	_ = logger.Log("h3_task_done", taskLogFields(after))
	return nil
}

func runMidflightUploadMode(ctx context.Context, conn *quic.Conn, h3Conn *http3.ClientConn, bindAddr, authority string, payloadBytes int, probeTimeout time.Duration, migrationAtBytes, chunkBytes int, chunkDelay time.Duration, logger *common.JSONLLogger, result *clientResult) error {
	migration, err := prepareMigrationPath(conn, bindAddr, result, logger)
	if err != nil {
		return err
	}
	defer migration.Close()

	var event migrationEvent
	trigger := func(bytesSeen int) error {
		if event.Triggered {
			return nil
		}
		_ = logger.Log("midflight_migration_threshold_reached", map[string]any{
			"mode":       "midflight-upload",
			"bytes_seen": bytesSeen,
		})
		performed, err := performMigration(ctx, conn, migration.path, probeTimeout, result, logger)
		performed.AtBytes = bytesSeen
		event = performed
		return err
	}

	task, err := doMidflightUpload(ctx, h3Conn, authority, "midflight-upload", payloadBytes, migrationAtBytes, chunkBytes, chunkDelay, trigger)
	applyMigrationEvent(&task, event)
	if err != nil {
		return err
	}
	if !task.MigrationTriggered {
		return fmt.Errorf("midflight upload completed without triggering migration")
	}
	result.Tasks = append(result.Tasks, task)
	result.ConnectionLocalAddrAfterAfter = conn.LocalAddr().String()
	_ = logger.Log("h3_task_done", taskLogFields(task))
	return nil
}

func runMidflightDownloadMode(ctx context.Context, conn *quic.Conn, h3Conn *http3.ClientConn, bindAddr, authority string, payloadBytes int, probeTimeout time.Duration, migrationAtBytes, chunkBytes int, chunkDelay time.Duration, logger *common.JSONLLogger, result *clientResult) error {
	migration, err := prepareMigrationPath(conn, bindAddr, result, logger)
	if err != nil {
		return err
	}
	defer migration.Close()

	var event migrationEvent
	trigger := func(bytesSeen int) error {
		if event.Triggered {
			return nil
		}
		_ = logger.Log("midflight_migration_threshold_reached", map[string]any{
			"mode":       "midflight-download",
			"bytes_seen": bytesSeen,
		})
		performed, err := performMigration(ctx, conn, migration.path, probeTimeout, result, logger)
		performed.AtBytes = bytesSeen
		event = performed
		return err
	}

	task, err := doMidflightDownload(ctx, h3Conn, authority, "midflight-download", payloadBytes, migrationAtBytes, chunkBytes, chunkDelay, trigger)
	applyMigrationEvent(&task, event)
	if err != nil {
		return err
	}
	if !task.MigrationTriggered {
		return fmt.Errorf("midflight download completed without triggering migration")
	}
	result.Tasks = append(result.Tasks, task)
	result.ConnectionLocalAddrAfterAfter = conn.LocalAddr().String()
	_ = logger.Log("h3_task_done", taskLogFields(task))
	return nil
}

func prepareMigrationPath(conn *quic.Conn, bindAddr string, result *clientResult, logger *common.JSONLLogger) (*migrationPath, error) {
	udpB, err := listenLocalUDP(bindAddr)
	if err != nil {
		return nil, err
	}
	trB := &quic.Transport{Conn: udpB}
	result.SocketBLocalAddr = udpB.LocalAddr().String()
	_ = logger.Log("second_path_socket_ready", map[string]any{
		"socket_b_local_addr": result.SocketBLocalAddr,
	})

	path, err := conn.AddPath(trB)
	if err != nil {
		_ = trB.Close()
		return nil, err
	}
	return &migrationPath{udp: udpB, tr: trB, path: path}, nil
}

func (m *migrationPath) Close() {
	if m == nil {
		return
	}
	if m.tr != nil {
		_ = m.tr.Close()
		return
	}
	if m.udp != nil {
		_ = m.udp.Close()
	}
}

func performMigration(ctx context.Context, conn *quic.Conn, path *quic.Path, probeTimeout time.Duration, result *clientResult, logger *common.JSONLLogger) (migrationEvent, error) {
	event := migrationEvent{
		Triggered: true,
		StartedAt: time.Now().UTC().Format(time.RFC3339Nano),
	}
	switchErr := path.Switch()
	if switchErr != nil {
		result.SwitchBeforeProbeError = switchErr.Error()
	}
	result.SwitchBeforeProbeMatched = errors.Is(switchErr, quic.ErrPathNotValidated)
	_ = logger.Log("switch_before_probe_checked", map[string]any{
		"error":   result.SwitchBeforeProbeError,
		"matched": result.SwitchBeforeProbeMatched,
	})
	if !result.SwitchBeforeProbeMatched {
		return event, fmt.Errorf("expected ErrPathNotValidated before Probe, got %v", switchErr)
	}

	probeCtx, cancelProbe := context.WithTimeout(ctx, probeTimeout)
	probeStarted := time.Now()
	err := path.Probe(probeCtx)
	cancelProbe()
	result.ProbeDurationMillis = time.Since(probeStarted).Milliseconds()
	result.ConnectionLocalAddrAfterProbe = conn.LocalAddr().String()
	if err != nil {
		return event, err
	}
	_ = logger.Log("path_probe_success", map[string]any{
		"duration_ms":                 result.ProbeDurationMillis,
		"connection_local_addr_after": result.ConnectionLocalAddrAfterProbe,
	})

	if err := path.Switch(); err != nil {
		return event, err
	}
	result.ConnectionLocalAddrAfterSwitch = conn.LocalAddr().String()
	event.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
	event.LocalAddrAfter = result.ConnectionLocalAddrAfterSwitch
	_ = logger.Log("path_switch_success", map[string]any{
		"connection_local_addr_after": result.ConnectionLocalAddrAfterSwitch,
		"socket_b_local_addr":         result.SocketBLocalAddr,
	})
	return event, nil
}

func checkPostMigrationAddress(result *clientResult, logger *common.JSONLLogger) error {
	result.LocalAddrChangedToSocketB = result.ConnectionLocalAddrAfterAfter == result.SocketBLocalAddr
	_ = logger.Log("post_migration_addr_checked", map[string]any{
		"connection_local_addr_after_after_request": result.ConnectionLocalAddrAfterAfter,
		"socket_b_local_addr":                       result.SocketBLocalAddr,
		"changed_to_socket_b":                       result.LocalAddrChangedToSocketB,
	})
	if !result.LocalAddrChangedToSocketB {
		return fmt.Errorf("connection local address did not switch to socket B after HTTP/3 workload: conn=%s socket_b=%s", result.ConnectionLocalAddrAfterAfter, result.SocketBLocalAddr)
	}
	return nil
}

func waitAfterSend(ctx context.Context, postSendWait time.Duration, logger *common.JSONLLogger) error {
	_ = logger.Log("post_send_wait_start", map[string]any{
		"duration_ms": postSendWait.Milliseconds(),
	})
	select {
	case <-time.After(postSendWait):
	case <-ctx.Done():
		return ctx.Err()
	}
	_ = logger.Log("post_send_wait_done", map[string]any{
		"duration_ms": postSendWait.Milliseconds(),
	})
	return nil
}

func clientH3TLSConfig(keyLogPath string) (*tls.Config, io.Closer, error) {
	tlsConf, closer, err := common.ClientTLSConfig(keyLogPath)
	if err != nil {
		return nil, nil, err
	}
	tlsConf.NextProtos = []string{http3.NextProtoH3}
	return tlsConf, closer, nil
}

func listenLocalUDP(bindAddr string) (*net.UDPConn, error) {
	addr, err := net.ResolveUDPAddr("udp", bindAddr)
	if err != nil {
		return nil, err
	}
	return net.ListenUDP("udp", addr)
}

func doUpload(ctx context.Context, h3Conn *http3.ClientConn, authority, label string, payloadBytes int) (h3TaskResult, error) {
	started := time.Now().UTC()
	msg, header, err := common.BuildMessage(label, payloadBytes)
	if err != nil {
		return h3TaskResult{}, err
	}
	target := (&url.URL{Scheme: "https", Host: authority, Path: "/upload"}).String()
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, target, bytes.NewReader(msg))
	if err != nil {
		return h3TaskResult{}, err
	}
	req.ContentLength = int64(len(msg))
	req.Header.Set("Content-Type", "application/octet-stream")
	req.Header.Set("X-Experiment-Label", label)
	resp, err := h3Conn.RoundTrip(req)
	if err != nil {
		return h3TaskResult{}, err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return h3TaskResult{}, err
	}
	if resp.StatusCode != http.StatusOK {
		return h3TaskResult{}, fmt.Errorf("upload status=%d body=%q", resp.StatusCode, string(body))
	}
	return h3TaskResult{
		Label:         header.Label,
		Method:        http.MethodPost,
		Path:          "/upload",
		RequestBytes:  header.PayloadBytes,
		RequestSHA256: header.SHA256,
		ResponseBytes: len(body),
		StatusCode:    resp.StatusCode,
		StartedAt:     started.Format(time.RFC3339Nano),
		CompletedAt:   time.Now().UTC().Format(time.RFC3339Nano),
	}, nil
}

func doDownload(ctx context.Context, h3Conn *http3.ClientConn, authority, label string, payloadBytes int) (h3TaskResult, error) {
	started := time.Now().UTC()
	target := (&url.URL{
		Scheme: "https",
		Host:   authority,
		Path:   "/download",
		RawQuery: url.Values{
			"label": []string{label},
			"bytes": []string{fmt.Sprint(payloadBytes)},
		}.Encode(),
	}).String()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target, nil)
	if err != nil {
		return h3TaskResult{}, err
	}
	resp, err := h3Conn.RoundTrip(req)
	if err != nil {
		return h3TaskResult{}, err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return h3TaskResult{}, err
	}
	if resp.StatusCode != http.StatusOK {
		return h3TaskResult{}, fmt.Errorf("download status=%d body=%q", resp.StatusCode, string(body))
	}
	decoded, err := common.DecodeMessage(body)
	if err != nil {
		return h3TaskResult{}, err
	}
	if decoded.Header.Label != label {
		return h3TaskResult{}, fmt.Errorf("download label mismatch: got=%s want=%s", decoded.Header.Label, label)
	}
	if decoded.Header.PayloadBytes != payloadBytes {
		return h3TaskResult{}, fmt.Errorf("download payload size mismatch: got=%d want=%d", decoded.Header.PayloadBytes, payloadBytes)
	}
	return h3TaskResult{
		Label:          decoded.Header.Label,
		Method:         http.MethodGet,
		Path:           "/download",
		ResponseBytes:  decoded.Header.PayloadBytes,
		ResponseSHA256: decoded.Header.SHA256,
		StatusCode:     resp.StatusCode,
		StartedAt:      started.Format(time.RFC3339Nano),
		CompletedAt:    time.Now().UTC().Format(time.RFC3339Nano),
	}, nil
}

func doMidflightUpload(ctx context.Context, h3Conn *http3.ClientConn, authority, label string, payloadBytes, migrationAtBytes, chunkBytes int, chunkDelay time.Duration, trigger func(int) error) (h3TaskResult, error) {
	started := time.Now().UTC()
	msg, header, err := common.BuildMessage(label, payloadBytes)
	if err != nil {
		return h3TaskResult{}, err
	}
	triggerAt, err := normalizeTriggerAt(len(msg), migrationAtBytes)
	if err != nil {
		return h3TaskResult{}, err
	}
	target := (&url.URL{Scheme: "https", Host: authority, Path: "/upload"}).String()
	bodyReader := &throttledTriggerReader{
		data:       msg,
		chunkBytes: chunkBytes,
		chunkDelay: chunkDelay,
		triggerAt:  triggerAt,
		trigger:    trigger,
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, target, bodyReader)
	if err != nil {
		return h3TaskResult{}, err
	}
	req.ContentLength = int64(len(msg))
	req.Header.Set("Content-Type", "application/octet-stream")
	req.Header.Set("X-Experiment-Label", label)
	resp, err := h3Conn.RoundTrip(req)
	if err != nil {
		return h3TaskResult{}, err
	}
	defer resp.Body.Close()
	response, err := io.ReadAll(resp.Body)
	if err != nil {
		return h3TaskResult{}, err
	}
	if resp.StatusCode != http.StatusOK {
		return h3TaskResult{}, fmt.Errorf("midflight upload status=%d body=%q", resp.StatusCode, string(response))
	}
	if !bodyReader.triggered {
		return h3TaskResult{}, fmt.Errorf("midflight upload threshold was not reached: trigger_at=%d sent=%d", triggerAt, bodyReader.offset)
	}
	return h3TaskResult{
		Label:         header.Label,
		Method:        http.MethodPost,
		Path:          "/upload",
		RequestBytes:  header.PayloadBytes,
		RequestSHA256: header.SHA256,
		ResponseBytes: len(response),
		StatusCode:    resp.StatusCode,
		StartedAt:     started.Format(time.RFC3339Nano),
		CompletedAt:   time.Now().UTC().Format(time.RFC3339Nano),
	}, nil
}

func doMidflightDownload(ctx context.Context, h3Conn *http3.ClientConn, authority, label string, payloadBytes, migrationAtBytes, chunkBytes int, chunkDelay time.Duration, trigger func(int) error) (h3TaskResult, error) {
	started := time.Now().UTC()
	triggerAt := migrationAtBytes
	if triggerAt <= 0 {
		triggerAt = payloadBytes / 2
	}
	if triggerAt <= 0 {
		triggerAt = 1
	}
	delayMillis := chunkDelay.Milliseconds()
	if chunkDelay > 0 && delayMillis == 0 {
		delayMillis = 1
	}
	target := (&url.URL{
		Scheme: "https",
		Host:   authority,
		Path:   "/download",
		RawQuery: url.Values{
			"label":       []string{label},
			"bytes":       []string{fmt.Sprint(payloadBytes)},
			"stream":      []string{"true"},
			"chunk_bytes": []string{fmt.Sprint(chunkBytes)},
			"delay_ms":    []string{fmt.Sprint(delayMillis)},
		}.Encode(),
	}).String()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target, nil)
	if err != nil {
		return h3TaskResult{}, err
	}
	resp, err := h3Conn.RoundTrip(req)
	if err != nil {
		return h3TaskResult{}, err
	}
	defer resp.Body.Close()
	body, triggered, err := readAllWithTrigger(resp.Body, triggerAt, chunkBytes, trigger)
	if err != nil {
		return h3TaskResult{}, err
	}
	if resp.StatusCode != http.StatusOK {
		return h3TaskResult{}, fmt.Errorf("midflight download status=%d body=%q", resp.StatusCode, string(body))
	}
	if !triggered {
		return h3TaskResult{}, fmt.Errorf("midflight download threshold was not reached: trigger_at=%d received=%d", triggerAt, len(body))
	}
	decoded, err := common.DecodeMessage(body)
	if err != nil {
		return h3TaskResult{}, err
	}
	if decoded.Header.Label != label {
		return h3TaskResult{}, fmt.Errorf("download label mismatch: got=%s want=%s", decoded.Header.Label, label)
	}
	if decoded.Header.PayloadBytes != payloadBytes {
		return h3TaskResult{}, fmt.Errorf("download payload size mismatch: got=%d want=%d", decoded.Header.PayloadBytes, payloadBytes)
	}
	return h3TaskResult{
		Label:          decoded.Header.Label,
		Method:         http.MethodGet,
		Path:           "/download",
		ResponseBytes:  decoded.Header.PayloadBytes,
		ResponseSHA256: decoded.Header.SHA256,
		StatusCode:     resp.StatusCode,
		StartedAt:      started.Format(time.RFC3339Nano),
		CompletedAt:    time.Now().UTC().Format(time.RFC3339Nano),
	}, nil
}

func (r *throttledTriggerReader) Read(p []byte) (int, error) {
	if len(p) == 0 {
		return 0, nil
	}
	if r.offset >= len(r.data) {
		return 0, io.EOF
	}
	maxRead := len(p)
	if r.chunkBytes > 0 && maxRead > r.chunkBytes {
		maxRead = r.chunkBytes
	}
	remaining := len(r.data) - r.offset
	if maxRead > remaining {
		maxRead = remaining
	}
	n := copy(p[:maxRead], r.data[r.offset:r.offset+maxRead])
	r.offset += n
	if !r.triggered && r.triggerAt > 0 && r.offset >= r.triggerAt {
		r.triggered = true
		if err := r.trigger(r.offset); err != nil {
			return n, err
		}
	}
	if r.chunkDelay > 0 {
		time.Sleep(r.chunkDelay)
	}
	return n, nil
}

func (r *throttledTriggerReader) Close() error {
	return nil
}

func readAllWithTrigger(r io.Reader, triggerAt, chunkBytes int, trigger func(int) error) ([]byte, bool, error) {
	if chunkBytes <= 0 {
		chunkBytes = 32 * 1024
	}
	buf := make([]byte, chunkBytes)
	var out bytes.Buffer
	triggered := false
	for {
		n, err := r.Read(buf)
		if n > 0 {
			out.Write(buf[:n])
			if !triggered && triggerAt > 0 && out.Len() >= triggerAt {
				triggered = true
				if triggerErr := trigger(out.Len()); triggerErr != nil {
					return out.Bytes(), triggered, triggerErr
				}
			}
		}
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			return out.Bytes(), triggered, err
		}
	}
	return out.Bytes(), triggered, nil
}

func normalizeTriggerAt(totalBytes, requested int) (int, error) {
	if totalBytes < 2 {
		return 0, fmt.Errorf("body is too small for mid-flight migration: total=%d", totalBytes)
	}
	if requested <= 0 {
		return totalBytes / 2, nil
	}
	if requested >= totalBytes {
		return 0, fmt.Errorf("migration-at-bytes must be smaller than body size: requested=%d total=%d", requested, totalBytes)
	}
	return requested, nil
}

func applyMigrationEvent(task *h3TaskResult, event migrationEvent) {
	task.MigrationTriggered = event.Triggered
	task.MigrationAtBytes = event.AtBytes
	task.MigrationStartedAt = event.StartedAt
	task.MigrationCompletedAt = event.CompletedAt
	task.MigrationLocalAddrAfter = event.LocalAddrAfter
}

func taskLogFields(task h3TaskResult) map[string]any {
	return map[string]any{
		"label":               task.Label,
		"method":              task.Method,
		"path":                task.Path,
		"status_code":         task.StatusCode,
		"request_bytes":       task.RequestBytes,
		"response_bytes":      task.ResponseBytes,
		"migration_triggered": task.MigrationTriggered,
		"migration_at_bytes":  task.MigrationAtBytes,
	}
}

func isSupportedMode(mode string) bool {
	switch mode {
	case "upload-download", "midflight-upload", "midflight-download":
		return true
	default:
		return false
	}
}

func failResult(result clientResult, err error) (clientResult, error) {
	result.Error = err.Error()
	result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
	return result, err
}
