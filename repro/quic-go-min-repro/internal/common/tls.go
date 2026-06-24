package common

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"io"
	"math/big"
	"net"
	"os"
	"time"
)

const ALPN = "quic-cm-repro"

func ServerTLSConfig(keyLogPath string) (*tls.Config, io.Closer, error) {
	cert, err := generateSelfSignedCert()
	if err != nil {
		return nil, nil, err
	}
	keyLog, err := openKeyLog(keyLogPath)
	if err != nil {
		return nil, nil, err
	}
	return &tls.Config{
		Certificates: []tls.Certificate{cert},
		NextProtos:   []string{ALPN},
		KeyLogWriter: keyLog,
	}, keyLog, nil
}

func ClientTLSConfig(keyLogPath string) (*tls.Config, io.Closer, error) {
	keyLog, err := openKeyLog(keyLogPath)
	if err != nil {
		return nil, nil, err
	}
	return &tls.Config{
		ServerName:         "localhost",
		InsecureSkipVerify: true,
		NextProtos:         []string{ALPN},
		KeyLogWriter:       keyLog,
	}, keyLog, nil
}

func openKeyLog(path string) (io.WriteCloser, error) {
	if path == "" {
		return nil, nil
	}
	if err := EnsureParentDir(path); err != nil {
		return nil, err
	}
	return os.Create(path)
}

func generateSelfSignedCert() (tls.Certificate, error) {
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return tls.Certificate{}, err
	}
	serialLimit := new(big.Int).Lsh(big.NewInt(1), 128)
	serial, err := rand.Int(rand.Reader, serialLimit)
	if err != nil {
		return tls.Certificate{}, err
	}
	template := x509.Certificate{
		SerialNumber: serial,
		Subject: pkix.Name{
			CommonName: "quic-cm-repro.local",
		},
		NotBefore:             time.Now().Add(-time.Hour),
		NotAfter:              time.Now().Add(24 * time.Hour),
		KeyUsage:              x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		BasicConstraintsValid: true,
		DNSNames:              []string{"localhost", "quic-cm-repro.local"},
		IPAddresses:           []net.IP{net.ParseIP("127.0.0.1"), net.ParseIP("::1")},
	}
	derBytes, err := x509.CreateCertificate(rand.Reader, &template, &template, &privateKey.PublicKey, privateKey)
	if err != nil {
		return tls.Certificate{}, err
	}
	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: derBytes})
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY", Bytes: x509.MarshalPKCS1PrivateKey(privateKey)})
	return tls.X509KeyPair(certPEM, keyPEM)
}
