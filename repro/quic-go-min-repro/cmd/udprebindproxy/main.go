package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"path/filepath"
	"sync"
	"syscall"
	"time"
)

type proxyResult struct {
	Role                   string `json:"role"`
	OK                     bool   `json:"ok"`
	StartedAt              string `json:"started_at"`
	CompletedAt            string `json:"completed_at"`
	ListenAddr             string `json:"listen_addr"`
	ServerAddr             string `json:"server_addr"`
	UpstreamAAddr          string `json:"upstream_a_addr"`
	UpstreamBAddr          string `json:"upstream_b_addr"`
	SwitchAfterMillis      int64  `json:"switch_after_ms"`
	Switched               bool   `json:"switched"`
	FirstClientAt          string `json:"first_client_at,omitempty"`
	SwitchedAt             string `json:"switched_at,omitempty"`
	LastClientAddr         string `json:"last_client_addr,omitempty"`
	ClientPackets          int    `json:"client_packets"`
	ServerPacketsA         int    `json:"server_packets_a"`
	ServerPacketsB         int    `json:"server_packets_b"`
	DropAServerAfterSwitch bool   `json:"drop_a_server_after_switch"`
	DropBServerAfterSwitch bool   `json:"drop_b_server_after_switch"`
	DroppedServerPacketsA  int    `json:"dropped_server_packets_a"`
	DroppedServerPacketsB  int    `json:"dropped_server_packets_b"`
	DroppedServerBytesA    int    `json:"dropped_server_bytes_a"`
	DroppedServerBytesB    int    `json:"dropped_server_bytes_b"`
	BytesClientToSrv       int    `json:"bytes_client_to_server"`
	BytesServerToCli       int    `json:"bytes_server_to_client"`
	Error                  string `json:"error,omitempty"`
}

type jsonlLogger struct {
	mu sync.Mutex
	f  *os.File
}

func newJSONLLogger(path string) (*jsonlLogger, error) {
	if path == "" {
		return &jsonlLogger{}, nil
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}
	f, err := os.Create(path)
	if err != nil {
		return nil, err
	}
	return &jsonlLogger{f: f}, nil
}

func (l *jsonlLogger) close() error {
	if l.f == nil {
		return nil
	}
	return l.f.Close()
}

func (l *jsonlLogger) log(event string, fields map[string]any) {
	if l.f == nil {
		return
	}
	entry := map[string]any{
		"ts":    time.Now().UTC().Format(time.RFC3339Nano),
		"event": event,
	}
	for key, value := range fields {
		entry[key] = value
	}
	line, err := json.Marshal(entry)
	if err != nil {
		return
	}
	l.mu.Lock()
	defer l.mu.Unlock()
	_, _ = l.f.Write(append(line, '\n'))
}

func main() {
	listen := flag.String("listen", "127.0.0.1:4443", "client-facing UDP listen address")
	server := flag.String("server", "127.0.0.1:4444", "upstream QUIC server UDP address")
	switchAfter := flag.Duration("switch-after", 3*time.Second, "delay before forwarding new client packets via upstream socket B")
	dropAServerAfterSwitch := flag.Bool("drop-a-server-after-switch", false, "drop server-to-client packets arriving on upstream A after client traffic has switched to upstream B")
	dropBServerAfterSwitch := flag.Bool("drop-b-server-after-switch", false, "drop server-to-client packets arriving on upstream B after client traffic has switched to upstream B")
	timeout := flag.Duration("timeout", 45*time.Second, "maximum proxy runtime")
	logPath := flag.String("log", "", "optional JSONL proxy log path")
	resultPath := flag.String("result", "", "optional result JSON path")
	flag.Parse()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	ctx, cancel := context.WithTimeout(ctx, *timeout)
	defer cancel()

	result, err := run(ctx, *listen, *server, *switchAfter, *dropAServerAfterSwitch, *dropBServerAfterSwitch, *logPath)
	if err != nil {
		result.Error = err.Error()
	}
	result.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
	result.OK = result.Error == "" && result.ClientPackets > 0 && (result.ServerPacketsA+result.ServerPacketsB) > 0
	if *resultPath != "" {
		if writeErr := writeJSON(*resultPath, result); writeErr != nil {
			log.Printf("write result: %v", writeErr)
		}
	}
	if err != nil {
		log.Fatal(err)
	}
}

func run(ctx context.Context, listenAddr, serverAddr string, switchAfter time.Duration, dropAServerAfterSwitch, dropBServerAfterSwitch bool, logPath string) (proxyResult, error) {
	started := time.Now().UTC()
	result := proxyResult{
		Role:                   "udprebindproxy",
		StartedAt:              started.Format(time.RFC3339Nano),
		ListenAddr:             listenAddr,
		ServerAddr:             serverAddr,
		SwitchAfterMillis:      switchAfter.Milliseconds(),
		DropAServerAfterSwitch: dropAServerAfterSwitch,
		DropBServerAfterSwitch: dropBServerAfterSwitch,
	}

	clientUDPAddr, err := net.ResolveUDPAddr("udp", listenAddr)
	if err != nil {
		return result, err
	}
	serverUDPAddr, err := net.ResolveUDPAddr("udp", serverAddr)
	if err != nil {
		return result, err
	}
	clientConn, err := net.ListenUDP("udp", clientUDPAddr)
	if err != nil {
		return result, err
	}
	defer clientConn.Close()

	upstreamBind := &net.UDPAddr{IP: serverUDPAddr.IP, Port: 0}
	if upstreamBind.IP == nil || upstreamBind.IP.IsUnspecified() {
		upstreamBind.IP = net.ParseIP("127.0.0.1")
	}
	upstreamA, err := net.ListenUDP("udp", upstreamBind)
	if err != nil {
		return result, err
	}
	defer upstreamA.Close()
	upstreamB, err := net.ListenUDP("udp", upstreamBind)
	if err != nil {
		return result, err
	}
	defer upstreamB.Close()
	result.UpstreamAAddr = upstreamA.LocalAddr().String()
	result.UpstreamBAddr = upstreamB.LocalAddr().String()

	logger, err := newJSONLLogger(logPath)
	if err != nil {
		return result, err
	}
	defer logger.close()
	logger.log("proxy_started", map[string]any{
		"listen":                     listenAddr,
		"server":                     serverAddr,
		"upstream_a":                 result.UpstreamAAddr,
		"upstream_b":                 result.UpstreamBAddr,
		"switch_after":               switchAfter.String(),
		"drop_a_server_after_switch": dropAServerAfterSwitch,
		"drop_b_server_after_switch": dropBServerAfterSwitch,
	})

	var mu sync.Mutex
	var clientAddr *net.UDPAddr
	var firstClientAt time.Time
	var wg sync.WaitGroup

	closeAll := func() {
		_ = clientConn.Close()
		_ = upstreamA.Close()
		_ = upstreamB.Close()
	}
	go func() {
		<-ctx.Done()
		closeAll()
	}()

	forwardToClient := func(name string, conn *net.UDPConn) {
		defer wg.Done()
		buf := make([]byte, 65535)
		for {
			n, _, err := conn.ReadFromUDP(buf)
			if err != nil {
				return
			}
			mu.Lock()
			dst := cloneUDPAddr(clientAddr)
			if name == "A" && dropAServerAfterSwitch && result.Switched {
				result.DroppedServerPacketsA++
				result.DroppedServerBytesA += n
				mu.Unlock()
				logger.log("server_to_client_dropped", map[string]any{
					"upstream": "A",
					"bytes":    n,
					"reason":   "drop_a_server_after_switch",
				})
				continue
			}
			if name == "B" && dropBServerAfterSwitch && result.Switched {
				result.DroppedServerPacketsB++
				result.DroppedServerBytesB += n
				mu.Unlock()
				logger.log("server_to_client_dropped", map[string]any{
					"upstream": "B",
					"bytes":    n,
					"reason":   "drop_b_server_after_switch",
				})
				continue
			}
			if name == "A" {
				result.ServerPacketsA++
			} else {
				result.ServerPacketsB++
			}
			result.BytesServerToCli += n
			mu.Unlock()
			if dst == nil {
				continue
			}
			if _, err := clientConn.WriteToUDP(buf[:n], dst); err != nil {
				logger.log("server_to_client_write_error", map[string]any{"upstream": name, "error": err.Error()})
				return
			}
		}
	}

	wg.Add(3)
	go forwardToClient("A", upstreamA)
	go forwardToClient("B", upstreamB)
	go func() {
		defer wg.Done()
		buf := make([]byte, 65535)
		for {
			n, addr, err := clientConn.ReadFromUDP(buf)
			if err != nil {
				return
			}
			now := time.Now().UTC()
			mu.Lock()
			if firstClientAt.IsZero() {
				firstClientAt = now
				result.FirstClientAt = now.Format(time.RFC3339Nano)
			}
			useB := now.Sub(firstClientAt) >= switchAfter
			mu.Unlock()
			upstream := upstreamA
			upstreamName := "A"
			if useB {
				upstream = upstreamB
				upstreamName = "B"
			}
			mu.Lock()
			clientAddr = cloneUDPAddr(addr)
			result.LastClientAddr = addr.String()
			result.ClientPackets++
			result.BytesClientToSrv += n
			if useB && !result.Switched {
				result.Switched = true
				result.SwitchedAt = now.Format(time.RFC3339Nano)
			}
			mu.Unlock()
			logger.log("client_to_server", map[string]any{
				"bytes":    n,
				"client":   addr.String(),
				"upstream": upstreamName,
			})
			if _, err := upstream.WriteToUDP(buf[:n], serverUDPAddr); err != nil {
				logger.log("client_to_server_write_error", map[string]any{"upstream": upstreamName, "error": err.Error()})
				return
			}
		}
	}()

	<-ctx.Done()
	closeAll()
	wg.Wait()
	if ctx.Err() != nil && ctx.Err() != context.Canceled && ctx.Err() != context.DeadlineExceeded {
		return result, ctx.Err()
	}
	return result, nil
}

func cloneUDPAddr(addr *net.UDPAddr) *net.UDPAddr {
	if addr == nil {
		return nil
	}
	clone := *addr
	if addr.IP != nil {
		clone.IP = append(net.IP(nil), addr.IP...)
	}
	return &clone
}

func writeJSON(path string, value any) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func (r proxyResult) String() string {
	return fmt.Sprintf("%s %s -> %s", r.Role, r.ListenAddr, r.ServerAddr)
}
