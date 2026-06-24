package common

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"io"
	"strings"

	"github.com/quic-go/quic-go"
)

const (
	AWSQUICLBConfigRotationByte = 0
	AWSServerIDLen              = 8
	AWSNLBNonceLen              = 7
	AWSNLBConnIDLen             = 1 + AWSServerIDLen + AWSNLBNonceLen
)

type AWSNLBConnectionIDGenerator struct {
	serverID [AWSServerIDLen]byte
}

func NewAWSNLBConnectionIDGenerator(serverID [AWSServerIDLen]byte) *AWSNLBConnectionIDGenerator {
	return &AWSNLBConnectionIDGenerator{serverID: serverID}
}

func (g *AWSNLBConnectionIDGenerator) GenerateConnectionID() (quic.ConnectionID, error) {
	id := make([]byte, AWSNLBConnIDLen)
	id[0] = AWSQUICLBConfigRotationByte
	copy(id[1:1+AWSServerIDLen], g.serverID[:])
	if _, err := io.ReadFull(rand.Reader, id[1+AWSServerIDLen:]); err != nil {
		return quic.ConnectionID{}, err
	}
	return quic.ConnectionIDFromBytes(id), nil
}

func (g *AWSNLBConnectionIDGenerator) ConnectionIDLen() int {
	return AWSNLBConnIDLen
}

func (g *AWSNLBConnectionIDGenerator) ServerIDHex() string {
	return hex.EncodeToString(g.serverID[:])
}

func ParseAWSServerIDHex(value string) ([AWSServerIDLen]byte, error) {
	var out [AWSServerIDLen]byte
	value = strings.TrimPrefix(strings.TrimSpace(value), "0x")
	if value == "" {
		return out, nil
	}
	if len(value) != AWSServerIDLen*2 {
		return out, fmt.Errorf("AWS NLB QUIC server id must be %d hex chars, got %d", AWSServerIDLen*2, len(value))
	}
	decoded, err := hex.DecodeString(value)
	if err != nil {
		return out, fmt.Errorf("decode AWS NLB QUIC server id: %w", err)
	}
	copy(out[:], decoded)
	return out, nil
}
