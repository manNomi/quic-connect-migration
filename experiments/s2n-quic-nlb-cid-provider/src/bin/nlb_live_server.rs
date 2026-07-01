use s2n_quic::Server;
use s2n_quic_nlb_cid_provider::AwsNlbCidFormat;
use serde::Serialize;
use std::{env, fs, path::PathBuf, time::Duration};
use tokio::time::timeout;

type AnyError = Box<dyn std::error::Error + Send + Sync>;

#[derive(Debug, Serialize)]
struct LiveServerResult {
    status: &'static str,
    listen_addr: String,
    local_addr: String,
    server_id: String,
    observed_remote_addr: String,
    received_bytes: usize,
    echoed_bytes: usize,
}

#[tokio::main(flavor = "multi_thread", worker_threads = 2)]
async fn main() -> Result<(), AnyError> {
    let listen_addr = env_value("LISTEN_ADDR", "0.0.0.0:4433");
    let server_id = env_value("SERVER_ID", "a1b2c3d4e5f65890");
    let timeout_secs = env_value("TIMEOUT_SECS", "120").parse::<u64>()?;
    let result_path = PathBuf::from(env_value("RESULT_PATH", "results/server.json"));
    if let Some(parent) = result_path.parent() {
        fs::create_dir_all(parent)?;
    }

    let cert_pem = read_secretish_env_or_path("CERT_PEM", "CERT_PEM_PATH")?;
    let key_pem = read_secretish_env_or_path("KEY_PEM", "KEY_PEM_PATH")?;
    let connection_id = AwsNlbCidFormat::from_hex(&server_id)?;

    let mut server = Server::builder()
        .with_tls((cert_pem.as_str(), key_pem.as_str()))?
        .with_io(listen_addr.as_str())?
        .with_connection_id(connection_id)?
        .start()?;
    let local_addr = server.local_addr()?.to_string();

    let mut connection = timeout(Duration::from_secs(timeout_secs), server.accept())
        .await?
        .ok_or_else(|| "server closed before accepting connection".to_string())?;
    let observed_remote_addr = connection.remote_addr()?.to_string();
    let mut stream = timeout(
        Duration::from_secs(timeout_secs),
        connection.accept_bidirectional_stream(),
    )
    .await??
    .ok_or_else(|| "client did not open stream".to_string())?;

    let mut received_bytes = 0usize;
    let mut echoed_bytes = 0usize;
    while let Some(data) = timeout(Duration::from_secs(timeout_secs), stream.receive()).await?? {
        received_bytes += data.len();
        echoed_bytes += data.len();
        stream.send(data).await?;
    }
    stream.finish()?;

    let result = LiveServerResult {
        status: "PASS",
        listen_addr,
        local_addr,
        server_id,
        observed_remote_addr,
        received_bytes,
        echoed_bytes,
    };
    fs::write(result_path, serde_json::to_string_pretty(&result)? + "\n")?;
    Ok(())
}

fn env_value(name: &str, default: &str) -> String {
    env::var(name).unwrap_or_else(|_| default.to_string())
}

fn read_secretish_env_or_path(value_name: &str, path_name: &str) -> Result<String, AnyError> {
    if let Ok(value) = env::var(value_name) {
        return Ok(value);
    }
    let path = env::var(path_name)
        .map_err(|_| format!("missing {value_name} or {path_name} environment variable"))?;
    Ok(fs::read_to_string(path)?)
}
