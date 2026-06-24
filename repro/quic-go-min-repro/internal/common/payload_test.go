package common

import "testing"

func TestBuildAndDecodeMessage(t *testing.T) {
	msg, header, err := BuildMessage("before", 1024)
	if err != nil {
		t.Fatal(err)
	}
	decoded, err := DecodeMessage(msg)
	if err != nil {
		t.Fatal(err)
	}
	if decoded.Header.Label != "before" {
		t.Fatalf("label mismatch: %q", decoded.Header.Label)
	}
	if decoded.Header.PayloadBytes != 1024 {
		t.Fatalf("payload size mismatch: %d", decoded.Header.PayloadBytes)
	}
	if decoded.Header.SHA256 != header.SHA256 {
		t.Fatalf("checksum mismatch: %s != %s", decoded.Header.SHA256, header.SHA256)
	}
}
