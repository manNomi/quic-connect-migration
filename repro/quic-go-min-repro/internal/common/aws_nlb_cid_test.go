package common

import "testing"

func TestAWSNLBConnectionIDGenerator(t *testing.T) {
	serverID, err := ParseAWSServerIDHex("0xa1b2c3d4e5f65890")
	if err != nil {
		t.Fatal(err)
	}
	generator := NewAWSNLBConnectionIDGenerator(serverID)

	first, err := generator.GenerateConnectionID()
	if err != nil {
		t.Fatal(err)
	}
	second, err := generator.GenerateConnectionID()
	if err != nil {
		t.Fatal(err)
	}

	if first.Len() != AWSNLBConnIDLen {
		t.Fatalf("first len = %d, want %d", first.Len(), AWSNLBConnIDLen)
	}
	if second.Len() != AWSNLBConnIDLen {
		t.Fatalf("second len = %d, want %d", second.Len(), AWSNLBConnIDLen)
	}
	if got := first.Bytes()[0]; got != AWSQUICLBConfigRotationByte {
		t.Fatalf("first CID config byte = %x, want %x", got, AWSQUICLBConfigRotationByte)
	}
	if got := second.Bytes()[0]; got != AWSQUICLBConfigRotationByte {
		t.Fatalf("second CID config byte = %x, want %x", got, AWSQUICLBConfigRotationByte)
	}
	if got := first.Bytes()[1 : 1+AWSServerIDLen]; string(got) != string(serverID[:]) {
		t.Fatalf("first CID server id = %x, want %x", got, serverID)
	}
	if got := second.Bytes()[1 : 1+AWSServerIDLen]; string(got) != string(serverID[:]) {
		t.Fatalf("second CID server id = %x, want %x", got, serverID)
	}
	if string(first.Bytes()) == string(second.Bytes()) {
		t.Fatal("generated CIDs should not be identical")
	}
}

func TestParseAWSServerIDHex(t *testing.T) {
	serverID, err := ParseAWSServerIDHex("a1b2c3d4e5f65890")
	if err != nil {
		t.Fatal(err)
	}
	if got := serverID; got != [8]byte{0xa1, 0xb2, 0xc3, 0xd4, 0xe5, 0xf6, 0x58, 0x90} {
		t.Fatalf("server id = %x", got)
	}

	if _, err := ParseAWSServerIDHex("abcd"); err == nil {
		t.Fatal("expected short server id to fail")
	}
}
