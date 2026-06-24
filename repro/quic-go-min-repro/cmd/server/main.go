package main

import (
	"context"
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

type receivedPayload struct {
	Label                         string `json:"label"`
	PayloadBytes                  int    `json:"payload_bytes"`
	SHA256                        string `json:"sha256"`
	StreamID                      string `json:"stream_id"`
	ReceivedAt                    string `json:"received_at"`
	ConnectionLocalAddrAtReceive  string `json:"connection_local_addr_at_receive"`
	ConnectionRemoteAddrAtReceive string `json:"connection_remote_addr_at_receive"`
}

type serverResult struct {
	Role                 string            `json:"role"`
	OK                   bool              `json:"ok"`
	StartedAt            string            `json:"started_at"`
	CompletedAt          string            `json:"completed_at"`
	ListenAddr           string            `json:"listen_addr"`
	ConnectionLocalAddr  string            `json:"connection_local_addr,omitempty"`
	ConnectionRemoteAddr string            `json:"connection_remote_addr,omitempty"`
	ConnectionIDMode     string            `json:"connection_id_mode"`
	AWSServerID          string            `json:"aws_server_id,omitempty"`
	Received             []receivedPayload `json:"received"`
	Error                string            `json:"error,omitempty"`
}

func main() {
	addr := flag.String("addr", "127.0.0.1:4242", "UDP listen address")
	logPath := flag.String("log", "artifacts/logs/server.jsonl", "JSONL log path")
	resultPath := flag.String("result", "artifacts/results/server.json", "result JSON path")
	keyLogPath := flag.String("keylog", "", "TLS key log path")
	qlogDir := flag.String("qlog-dir", "artifacts/qlog", "qlog output directory")
	timeout := flag.Duration("timeout", 30*time.Second, "overall server timeout")
	serverIDHex := flag.String("server-id", "", "optional AWS NLB QUIC Server ID as 16 hex chars")
	flag.Parse()

	result, err := run(*addr, *logPath, *resultPath, *keyLogPath, *qlogDir, *timeout, *serverIDHex)
	if writeErr := common.WriteJSONFile(*resultPath, result); writeErr != nil {
		log.Printf("write result: %v", writeErr)
	}
	if err != nil {
		log.Fatal(err)
	}
}

func run(addr, logPath, resultPath, keyLogPath, qlogDir string, timeout time.Duration, serverIDHex string) (serverResult, error) {
	started := time.Now().UTC()
	result := serverResult{
		Role:             "server",
		StartedAt:        started.Format(time.RFC3339Nano),
		ListenAddr:       addr,
		ConnectionIDMode: "default",
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

	logger, err := common.NewJSONLLogger(logPath, "server")
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

	quicConf := &quic.Config{
		Tracer:          qlog.DefaultConnectionTracer,
		MaxIdleTimeout:  30 * time.Second,
		KeepAlivePeriod: 5 * time.Second,
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

	listener, err := transport.Listen(tlsConf, quicConf)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	defer listener.Close()

	_ = logger.Log("listening", map[string]any{
		"addr":               listener.Addr().String(),
		"qlog_dir":           qlogDir,
		"result":             resultPath,
		"timeout_ms":         timeout.Milliseconds(),
		"connection_id_mode": result.ConnectionIDMode,
		"aws_server_id":      result.AWSServerID,
	})

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	conn, err := listener.Accept(ctx)
	if err != nil {
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}
	defer conn.CloseWithError(0, "server done")

	result.ConnectionLocalAddr = conn.LocalAddr().String()
	result.ConnectionRemoteAddr = conn.RemoteAddr().String()
	_ = logger.Log("connection_accepted", map[string]any{
		"local_addr":  result.ConnectionLocalAddr,
		"remote_addr": result.ConnectionRemoteAddr,
	})

	seen := map[string]bool{}
	for len(result.Received) < 2 {
		stream, err := conn.AcceptUniStream(ctx)
		if err != nil {
			result.Error = err.Error()
			result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
			return result, err
		}
		raw, err := io.ReadAll(stream)
		if err != nil {
			result.Error = err.Error()
			result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
			return result, err
		}
		decoded, err := common.DecodeMessage(raw)
		if err != nil {
			result.Error = err.Error()
			result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
			return result, err
		}
		item := receivedPayload{
			Label:                         decoded.Header.Label,
			PayloadBytes:                  decoded.Header.PayloadBytes,
			SHA256:                        decoded.Header.SHA256,
			StreamID:                      fmt.Sprint(stream.StreamID()),
			ReceivedAt:                    time.Now().UTC().Format(time.RFC3339Nano),
			ConnectionLocalAddrAtReceive:  conn.LocalAddr().String(),
			ConnectionRemoteAddrAtReceive: conn.RemoteAddr().String(),
		}
		result.Received = append(result.Received, item)
		seen[item.Label] = true
		_ = logger.Log("stream_received", map[string]any{
			"label":         item.Label,
			"payload_bytes": item.PayloadBytes,
			"sha256":        item.SHA256,
			"stream_id":     item.StreamID,
			"local_addr":    item.ConnectionLocalAddrAtReceive,
			"remote_addr":   item.ConnectionRemoteAddrAtReceive,
		})
	}

	if !seen["before"] || !seen["after"] {
		err := fmt.Errorf("expected before and after labels, got %v", seen)
		result.Error = err.Error()
		result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
		return result, err
	}

	result.OK = true
	result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
	_ = logger.Log("server_success", map[string]any{
		"received_count": len(result.Received),
	})
	return result, nil
}
