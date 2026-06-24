package common

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
	"time"
)

type JSONLLogger struct {
	role string
	file *os.File
	enc  *json.Encoder
	mu   sync.Mutex
}

func NewJSONLLogger(path string, role string) (*JSONLLogger, error) {
	if path == "" {
		return &JSONLLogger{role: role}, nil
	}
	if err := EnsureParentDir(path); err != nil {
		return nil, err
	}
	f, err := os.Create(path)
	if err != nil {
		return nil, err
	}
	return &JSONLLogger{
		role: role,
		file: f,
		enc:  json.NewEncoder(f),
	}, nil
}

func (l *JSONLLogger) Log(event string, fields map[string]any) error {
	if l == nil || l.enc == nil {
		return nil
	}
	record := map[string]any{
		"ts":    time.Now().UTC().Format(time.RFC3339Nano),
		"role":  l.role,
		"event": event,
	}
	for k, v := range fields {
		record[k] = v
	}
	l.mu.Lock()
	defer l.mu.Unlock()
	return l.enc.Encode(record)
}

func (l *JSONLLogger) Close() error {
	if l == nil || l.file == nil {
		return nil
	}
	return l.file.Close()
}

func EnsureParentDir(path string) error {
	dir := filepath.Dir(path)
	if dir == "." || dir == "" {
		return nil
	}
	return os.MkdirAll(dir, 0o755)
}

func EnsureDir(path string) error {
	if path == "" {
		return nil
	}
	return os.MkdirAll(path, 0o755)
}

func WriteJSONFile(path string, value any) error {
	if path == "" {
		return nil
	}
	if err := EnsureParentDir(path); err != nil {
		return err
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	return enc.Encode(value)
}
