use rcgen::generate_simple_self_signed;
use std::{env, fs, path::PathBuf};

type AnyError = Box<dyn std::error::Error + Send + Sync>;

fn main() -> Result<(), AnyError> {
    let cert_path = PathBuf::from(
        env::args()
            .nth(1)
            .ok_or("usage: generate_localhost_cert <cert-pem-path> <key-pem-path>")?,
    );
    let key_path = PathBuf::from(
        env::args()
            .nth(2)
            .ok_or("usage: generate_localhost_cert <cert-pem-path> <key-pem-path>")?,
    );
    if let Some(parent) = cert_path.parent() {
        fs::create_dir_all(parent)?;
    }
    if let Some(parent) = key_path.parent() {
        fs::create_dir_all(parent)?;
    }

    let certified = generate_simple_self_signed(vec!["localhost".to_string()])?;
    fs::write(cert_path, certified.cert.pem())?;
    fs::write(key_path, certified.key_pair.serialize_pem())?;
    Ok(())
}
