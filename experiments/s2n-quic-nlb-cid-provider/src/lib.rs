use s2n_quic::provider::connection_id::{ConnectionInfo, Generator, LocalId, Validator};
use serde::Serialize;
use std::{fmt, num::ParseIntError};

pub const AWS_QUIC_LB_CONFIG_ROTATION_BYTE: u8 = 0x00;
pub const AWS_SERVER_ID_LEN: usize = 8;
pub const AWS_NLB_NONCE_LEN: usize = 7;
pub const AWS_NLB_CID_LEN: usize = 1 + AWS_SERVER_ID_LEN + AWS_NLB_NONCE_LEN;

#[derive(Debug)]
pub enum AwsNlbCidError {
    InvalidServerIdHexLen { got: usize },
    InvalidServerIdHex(ParseIntError),
    InvalidCidLen { got: usize },
    InvalidConfigByte { got: u8 },
}

impl fmt::Display for AwsNlbCidError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidServerIdHexLen { got } => write!(
                f,
                "AWS NLB QUIC server id must be {} hex chars, got {}",
                AWS_SERVER_ID_LEN * 2,
                got
            ),
            Self::InvalidServerIdHex(err) => write!(f, "decode AWS NLB QUIC server id: {err}"),
            Self::InvalidCidLen { got } => {
                write!(f, "AWS NLB CID must be {AWS_NLB_CID_LEN} bytes, got {got}")
            }
            Self::InvalidConfigByte { got } => {
                write!(f, "AWS NLB CID config byte must be 0x00, got 0x{got:02x}")
            }
        }
    }
}

impl std::error::Error for AwsNlbCidError {}

#[derive(Clone, Debug)]
pub struct AwsNlbCidFormat {
    server_id: [u8; AWS_SERVER_ID_LEN],
    nonce_counter: u64,
}

impl AwsNlbCidFormat {
    pub fn new(server_id: [u8; AWS_SERVER_ID_LEN]) -> Self {
        Self {
            server_id,
            nonce_counter: 0,
        }
    }

    pub fn from_hex(server_id_hex: &str) -> Result<Self, AwsNlbCidError> {
        Ok(Self::new(parse_server_id_hex(server_id_hex)?))
    }

    pub fn server_id(&self) -> [u8; AWS_SERVER_ID_LEN] {
        self.server_id
    }

    pub fn server_id_hex(&self) -> String {
        hex::encode(self.server_id)
    }

    pub fn generate_cid_bytes(&mut self) -> [u8; AWS_NLB_CID_LEN] {
        let mut cid = [0u8; AWS_NLB_CID_LEN];
        cid[0] = AWS_QUIC_LB_CONFIG_ROTATION_BYTE;
        cid[1..1 + AWS_SERVER_ID_LEN].copy_from_slice(&self.server_id);

        let nonce = self.nonce_counter.to_be_bytes();
        cid[1 + AWS_SERVER_ID_LEN..].copy_from_slice(&nonce[1..]);
        self.nonce_counter = self.nonce_counter.wrapping_add(1);

        cid
    }
}

impl Generator for AwsNlbCidFormat {
    fn generate(&mut self, _connection_info: &ConnectionInfo) -> LocalId {
        let cid = self.generate_cid_bytes();
        LocalId::try_from_bytes(&cid).expect("AWS NLB CID length is fixed and valid")
    }

    fn rotate_handshake_connection_id(&self) -> bool {
        true
    }
}

impl Validator for AwsNlbCidFormat {
    fn validate(&self, _connection_info: &ConnectionInfo, buffer: &[u8]) -> Option<usize> {
        if buffer.len() >= AWS_NLB_CID_LEN {
            Some(AWS_NLB_CID_LEN)
        } else {
            None
        }
    }
}

pub fn parse_server_id_hex(value: &str) -> Result<[u8; AWS_SERVER_ID_LEN], AwsNlbCidError> {
    let value = value.trim().strip_prefix("0x").unwrap_or(value.trim());
    if value.len() != AWS_SERVER_ID_LEN * 2 {
        return Err(AwsNlbCidError::InvalidServerIdHexLen { got: value.len() });
    }

    let mut out = [0u8; AWS_SERVER_ID_LEN];
    for (idx, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let chunk = std::str::from_utf8(chunk).expect("hex chunks are utf8");
        out[idx] = u8::from_str_radix(chunk, 16).map_err(AwsNlbCidError::InvalidServerIdHex)?;
    }
    Ok(out)
}

pub fn extract_server_id(cid: &[u8]) -> Result<[u8; AWS_SERVER_ID_LEN], AwsNlbCidError> {
    if cid.len() != AWS_NLB_CID_LEN {
        return Err(AwsNlbCidError::InvalidCidLen { got: cid.len() });
    }
    if cid[0] != AWS_QUIC_LB_CONFIG_ROTATION_BYTE {
        return Err(AwsNlbCidError::InvalidConfigByte { got: cid[0] });
    }

    let mut server_id = [0u8; AWS_SERVER_ID_LEN];
    server_id.copy_from_slice(&cid[1..1 + AWS_SERVER_ID_LEN]);
    Ok(server_id)
}

#[derive(Clone, Debug, Serialize)]
pub struct RouteTable {
    target_a: [u8; AWS_SERVER_ID_LEN],
    target_b: [u8; AWS_SERVER_ID_LEN],
}

impl RouteTable {
    pub fn new(target_a: [u8; AWS_SERVER_ID_LEN], target_b: [u8; AWS_SERVER_ID_LEN]) -> Self {
        Self { target_a, target_b }
    }

    pub fn route(&self, cid: &[u8]) -> Option<&'static str> {
        let server_id = extract_server_id(cid).ok()?;
        if server_id == self.target_a {
            Some("target-a")
        } else if server_id == self.target_b {
            Some("target-b")
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generates_aws_nlb_plaintext_cid_layout() {
        let server_id = parse_server_id_hex("a1b2c3d4e5f65890").unwrap();
        let mut format = AwsNlbCidFormat::new(server_id);

        let first = format.generate_cid_bytes();
        let second = format.generate_cid_bytes();

        assert_eq!(first.len(), AWS_NLB_CID_LEN);
        assert_eq!(first[0], AWS_QUIC_LB_CONFIG_ROTATION_BYTE);
        assert_eq!(&first[1..1 + AWS_SERVER_ID_LEN], &server_id);
        assert_eq!(hex::encode(first), "00a1b2c3d4e5f6589000000000000000");
        assert_eq!(hex::encode(second), "00a1b2c3d4e5f6589000000000000001");
        assert_ne!(first, second);
    }

    #[test]
    fn parses_server_id_hex_with_or_without_prefix() {
        let expected = [0xa1, 0xb2, 0xc3, 0xd4, 0xe5, 0xf6, 0x58, 0x90];
        assert_eq!(parse_server_id_hex("a1b2c3d4e5f65890").unwrap(), expected);
        assert_eq!(parse_server_id_hex("0xa1b2c3d4e5f65890").unwrap(), expected);
        assert!(parse_server_id_hex("abcd").is_err());
    }

    #[test]
    fn simulated_route_table_uses_embedded_server_id() {
        let target_a = parse_server_id_hex("a1b2c3d4e5f65890").unwrap();
        let target_b = parse_server_id_hex("a1b2c3d4e5f65999").unwrap();
        let wrong = parse_server_id_hex("ffffffffffffffff").unwrap();

        let mut cid_a = AwsNlbCidFormat::new(target_a);
        let mut cid_b = AwsNlbCidFormat::new(target_b);
        let mut cid_wrong = AwsNlbCidFormat::new(wrong);
        let router = RouteTable::new(target_a, target_b);

        assert_eq!(router.route(&cid_a.generate_cid_bytes()), Some("target-a"));
        assert_eq!(router.route(&cid_b.generate_cid_bytes()), Some("target-b"));
        assert_eq!(router.route(&cid_wrong.generate_cid_bytes()), None);
    }
}
