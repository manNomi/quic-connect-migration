package common

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"
)

type MessageHeader struct {
	Label        string `json:"label"`
	PayloadBytes int    `json:"payload_bytes"`
	SHA256       string `json:"sha256"`
	GeneratedAt  string `json:"generated_at"`
}

type DecodedMessage struct {
	Header MessageHeader
	Data   []byte
}

func BuildMessage(label string, size int) ([]byte, MessageHeader, error) {
	if label == "" {
		return nil, MessageHeader{}, fmt.Errorf("label is required")
	}
	if size < 0 {
		return nil, MessageHeader{}, fmt.Errorf("payload size must be non-negative")
	}
	data := DeterministicPayload(label, size)
	header := MessageHeader{
		Label:        label,
		PayloadBytes: len(data),
		SHA256:       SHA256Hex(data),
		GeneratedAt:  time.Now().UTC().Format(time.RFC3339Nano),
	}
	headerBytes, err := json.Marshal(header)
	if err != nil {
		return nil, MessageHeader{}, err
	}
	msg := make([]byte, 0, len(headerBytes)+1+len(data))
	msg = append(msg, headerBytes...)
	msg = append(msg, '\n')
	msg = append(msg, data...)
	return msg, header, nil
}

func DecodeMessage(msg []byte) (DecodedMessage, error) {
	idx := bytes.IndexByte(msg, '\n')
	if idx < 0 {
		return DecodedMessage{}, fmt.Errorf("missing JSON header delimiter")
	}
	var header MessageHeader
	if err := json.Unmarshal(msg[:idx], &header); err != nil {
		return DecodedMessage{}, fmt.Errorf("decode header: %w", err)
	}
	data := msg[idx+1:]
	if header.PayloadBytes != len(data) {
		return DecodedMessage{}, fmt.Errorf("payload length mismatch: header=%d actual=%d", header.PayloadBytes, len(data))
	}
	actual := SHA256Hex(data)
	if header.SHA256 != actual {
		return DecodedMessage{}, fmt.Errorf("payload checksum mismatch: header=%s actual=%s", header.SHA256, actual)
	}
	return DecodedMessage{Header: header, Data: data}, nil
}

func DeterministicPayload(label string, size int) []byte {
	data := make([]byte, size)
	seed := []byte("quic-cm-repro:" + label + ":")
	for i := range data {
		data[i] = seed[i%len(seed)] ^ byte((i*31+len(label))%251)
	}
	return data
}

func SHA256Hex(data []byte) string {
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])
}
