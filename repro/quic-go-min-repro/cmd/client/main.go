package main

import (
	"bytes"
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"time"

	"github.com/quic-go/quic-go"
	"github.com/quic-go/quic-go/qlog"

	"quic-cm/quic-go-min-repro/internal/common"
)

type sentPayload struct {
	Label        string `json:"label"`
	PayloadBytes int    `json:"payload_bytes"`
	SHA256       string `json:"sha256"`
	StreamID     string `json:"stream_id"`
	SentAt       string `json:"sent_at"`
}

type clientResult struct {
	Role                           string        `json:"role"`
	OK                             bool          `json:"ok"`
	Mode                           string        `json:"mode"`
	StartedAt                      string        `json:"started_at"`
	CompletedAt                    string        `json:"completed_at"`
	ServerAddr                     string        `json:"server_addr"`
	SocketALocalAddr               string        `json:"socket_a_local_addr"`
	SocketBLocalAddr               string        `json:"socket_b_local_addr"`
	ConnectionLocalAddrAfterDial   string        `json:"connection_local_addr_after_dial"`
	ConnectionLocalAddrAfterProbe  string        `json:"connection_local_addr_after_probe"`
	ConnectionLocalAddrAfterSwitch string        `json:"connection_local_addr_after_switch"`
	ConnectionLocalAddrAfterAfter  string        `json:"connection_local_addr_after_after_payload"`
	BindAddr                       string        `json:"bind_addr"`
	SwitchBeforeProbeError         string        `json:"switch_before_probe_error"`
	SwitchBeforeProbeMatched       bool          `json:"switch_before_probe_matched"`
	ProbeDurationMillis            int64         `json:"probe_duration_millis"`
	LocalAddrChangedToSocketB      bool          `json:"local_addr_changed_to_socket_b"`
	Sent                           []sentPayload `json:"sent"`
	Error                          string        `json:"error,omitempty"`
}

func main() {
	server := flag.String("server", "127.0.0.1:4242", "server UDP address")
	bindAddr := flag.String("bind", "0.0.0.0:0", "local UDP bind address for both client paths")
	payloadBytes := flag.Int("payload-bytes", 1048576, "payload size per stream")
	probeTimeout := flag.Duration("probe-timeout", 3*time.Second, "path probe timeout")
	logPath := flag.String("log", "artifacts/logs/client.jsonl", "JSONL log path")
	resultPath := flag.String("result", "artifacts/results/client.json", "result JSON path")
	keyLogPath := flag.String("keylog", "", "TLS key log path")
	qlogDir := flag.String("qlog-dir", "artifacts/qlog", "qlog output directory")
	mode := flag.String("mode", "happy-path", "experiment mode")
	timeout := flag.Duration("timeout", 30*time.Second, "overall client timeout")
	postSendWait := flag.Duration("post-send-wait", 0, "optional wait after final stream close before closing connection")
	flag.Parse()

	result, err := run(*server, *bindAddr, *payloadBytes, *probeTimeout, *logPath, *resultPath, *keyLogPath, *qlogDir, *mode, *timeout, *postSendWait)
	if writeErr := common.WriteJSONFile(*resultPath, result); writeErr != nil {
		log.Printf("write result: %v", writeErr)
	}
	if err != nil {
		log.Fatal(err)
	}
}

func run(server, bindAddr string, payloadBytes int, probeTimeout time.Duration, logPath, resultPath, keyLogPath, qlogDir, mode string, timeout, postSendWait time.Duration) (clientResult, error) {
	started := time.Now().UTC()
	result := clientResult{
		Role:       "client",
		Mode:       mode,
		StartedAt:  started.Format(time.RFC3339Nano),
		ServerAddr: server,
		BindAddr:   bindAddr,
	}
	if mode != "happy-path" {
		err := fmt.Errorf("unsupported mode %q", mode)
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}

	logger, err := common.NewJSONLLogger(logPath, "client")
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

	tlsConf, keyLogCloser, err := common.ClientTLSConfig(keyLogPath)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	if keyLogCloser != nil {
		defer keyLogCloser.Close()
	}

	serverAddr, err := net.ResolveUDPAddr("udp", server)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}

	udpA, err := listenLocalUDP(bindAddr)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	trA := &quic.Transport{Conn: udpA}
	defer trA.Close()
	result.SocketALocalAddr = udpA.LocalAddr().String()

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	quicConf := &quic.Config{
		Tracer:          qlog.DefaultConnectionTracer,
		MaxIdleTimeout:  30 * time.Second,
		KeepAlivePeriod: 5 * time.Second,
	}
	_ = logger.Log("dial_start", map[string]any{
		"server_addr":         server,
		"socket_a_local_addr": result.SocketALocalAddr,
		"payload_bytes":       payloadBytes,
		"qlog_dir":            qlogDir,
		"result":              resultPath,
	})
	conn, err := trA.Dial(ctx, serverAddr, tlsConf, quicConf)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	defer conn.CloseWithError(0, "client done")
	result.ConnectionLocalAddrAfterDial = conn.LocalAddr().String()
	_ = logger.Log("dial_success", map[string]any{
		"connection_local_addr":  result.ConnectionLocalAddrAfterDial,
		"connection_remote_addr": conn.RemoteAddr().String(),
	})

	before, err := sendPayload(ctx, conn, "before", payloadBytes)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	result.Sent = append(result.Sent, before)
	_ = logger.Log("payload_sent", map[string]any{
		"label":         before.Label,
		"payload_bytes": before.PayloadBytes,
		"sha256":        before.SHA256,
		"stream_id":     before.StreamID,
	})

	udpB, err := listenLocalUDP(bindAddr)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	trB := &quic.Transport{Conn: udpB}
	defer trB.Close()
	result.SocketBLocalAddr = udpB.LocalAddr().String()
	_ = logger.Log("second_path_socket_ready", map[string]any{
		"socket_b_local_addr": result.SocketBLocalAddr,
	})

	path, err := conn.AddPath(trB)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
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
		err := fmt.Errorf("expected ErrPathNotValidated before Probe, got %v", switchErr)
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}

	probeCtx, cancelProbe := context.WithTimeout(ctx, probeTimeout)
	probeStarted := time.Now()
	err = path.Probe(probeCtx)
	cancelProbe()
	result.ProbeDurationMillis = time.Since(probeStarted).Milliseconds()
	result.ConnectionLocalAddrAfterProbe = conn.LocalAddr().String()
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	_ = logger.Log("path_probe_success", map[string]any{
		"duration_ms":                 result.ProbeDurationMillis,
		"connection_local_addr_after": result.ConnectionLocalAddrAfterProbe,
	})

	if err := path.Switch(); err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	result.ConnectionLocalAddrAfterSwitch = conn.LocalAddr().String()
	_ = logger.Log("path_switch_success", map[string]any{
		"connection_local_addr_after": result.ConnectionLocalAddrAfterSwitch,
		"socket_b_local_addr":         result.SocketBLocalAddr,
	})

	after, err := sendPayload(ctx, conn, "after", payloadBytes)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	result.Sent = append(result.Sent, after)
	_ = logger.Log("payload_sent", map[string]any{
		"label":         after.Label,
		"payload_bytes": after.PayloadBytes,
		"sha256":        after.SHA256,
		"stream_id":     after.StreamID,
	})
	result.ConnectionLocalAddrAfterAfter = conn.LocalAddr().String()
	result.LocalAddrChangedToSocketB = result.ConnectionLocalAddrAfterAfter == result.SocketBLocalAddr
	_ = logger.Log("post_migration_addr_checked", map[string]any{
		"connection_local_addr_after_after_payload": result.ConnectionLocalAddrAfterAfter,
		"socket_b_local_addr":                       result.SocketBLocalAddr,
		"changed_to_socket_b":                       result.LocalAddrChangedToSocketB,
	})
	if !result.LocalAddrChangedToSocketB {
		err := fmt.Errorf("connection local address did not switch to socket B after post-migration payload: conn=%s socket_b=%s", result.ConnectionLocalAddrAfterAfter, result.SocketBLocalAddr)
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	if postSendWait > 0 {
		_ = logger.Log("post_send_wait_start", map[string]any{
			"duration_ms": postSendWait.Milliseconds(),
		})
		select {
		case <-time.After(postSendWait):
		case <-ctx.Done():
			result.Error = ctx.Err().Error()
			result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
			return result, ctx.Err()
		}
		_ = logger.Log("post_send_wait_done", map[string]any{
			"duration_ms": postSendWait.Milliseconds(),
		})
	}

	result.OK = true
	result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
	_ = logger.Log("client_success", map[string]any{
		"sent_count": len(result.Sent),
	})
	return result, nil
}

func listenLocalUDP(bindAddr string) (*net.UDPConn, error) {
	addr, err := net.ResolveUDPAddr("udp", bindAddr)
	if err != nil {
		return nil, err
	}
	return net.ListenUDP("udp", addr)
}

func sendPayload(ctx context.Context, conn *quic.Conn, label string, payloadBytes int) (sentPayload, error) {
	msg, header, err := common.BuildMessage(label, payloadBytes)
	if err != nil {
		return sentPayload{}, err
	}
	stream, err := conn.OpenUniStreamSync(ctx)
	if err != nil {
		return sentPayload{}, err
	}
	written, err := io.Copy(stream, bytes.NewReader(msg))
	if err != nil {
		return sentPayload{}, err
	}
	if written != int64(len(msg)) {
		return sentPayload{}, fmt.Errorf("short stream write: wrote=%d expected=%d", written, len(msg))
	}
	if err := stream.Close(); err != nil {
		return sentPayload{}, err
	}
	return sentPayload{
		Label:        header.Label,
		PayloadBytes: header.PayloadBytes,
		SHA256:       header.SHA256,
		StreamID:     fmt.Sprint(stream.StreamID()),
		SentAt:       time.Now().UTC().Format(time.RFC3339Nano),
	}, nil
}
