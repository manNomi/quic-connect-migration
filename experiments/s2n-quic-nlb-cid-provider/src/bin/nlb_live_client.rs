use s2n_quic::{client::Connect, Client};
use serde::Serialize;
use std::{
    env, fs,
    net::{SocketAddr, ToSocketAddrs},
    path::PathBuf,
    time::Duration,
};
use tokio::time::timeout;

type AnyError = Box<dyn std::error::Error + Send + Sync>;

#[derive(Debug, Serialize)]
struct LiveClientResult {
    status: &'static str,
    server_addr: String,
    resolved_addr: String,
    server_name: String,
    client_local_addr: String,
    payload_bytes: usize,
    payload_chunks: usize,
    chunk_delay_ms: u64,
    received_bytes: usize,
    echo_matches: bool,
}

#[tokio::main(flavor = "multi_thread", worker_threads = 2)]
async fn main() -> Result<(), AnyError> {
    let server_addr = env_value("SERVER_ADDR", "127.0.0.1:4433");
    let resolved_addr = resolve_addr(&server_addr)?;
    let server_name = env_value("SERVER_NAME", "localhost");
    let timeout_secs = env_value("TIMEOUT_SECS", "30").parse::<u64>()?;
    let payload_bytes = env_value("PAYLOAD_BYTES", "4096").parse::<usize>()?;
    let payload_chunks = env_value("PAYLOAD_CHUNKS", "1").parse::<usize>()?.max(1);
    let chunk_delay_ms = env_value("CHUNK_DELAY_MS", "0").parse::<u64>()?;
    let result_path = PathBuf::from(env_value("RESULT_PATH", "results/client.json"));
    if let Some(parent) = result_path.parent() {
        fs::create_dir_all(parent)?;
    }

    let cert_pem = read_secretish_env_or_path("CERT_PEM", "CERT_PEM_PATH")?;
    let client = Client::builder()
        .with_tls(cert_pem.as_str())?
        .with_io("0.0.0.0:0")?
        .start()?;
    let client_local_addr = client.local_addr()?.to_string();

    let connect = Connect::new(resolved_addr).with_server_name(server_name.as_str());
    let mut connection =
        timeout(Duration::from_secs(timeout_secs), client.connect(connect)).await??;
    connection.keep_alive(true)?;

    let mut stream = timeout(
        Duration::from_secs(timeout_secs),
        connection.open_bidirectional_stream(),
    )
    .await??;
    let payload = deterministic_payload(payload_bytes);
    for chunk in payload_chunks_for(&payload, payload_chunks) {
        stream.send(chunk.to_vec().into()).await?;
        if chunk_delay_ms > 0 {
            tokio::time::sleep(Duration::from_millis(chunk_delay_ms)).await;
        }
    }
    stream.finish()?;

    let mut received = Vec::with_capacity(payload.len());
    while received.len() < payload.len() {
        match timeout(Duration::from_secs(timeout_secs), stream.receive()).await?? {
            Some(data) => received.extend_from_slice(data.as_ref()),
            None => break,
        }
    }
    let echo_matches = received == payload;
    let result = LiveClientResult {
        status: if echo_matches { "PASS" } else { "FAIL" },
        server_addr,
        resolved_addr: resolved_addr.to_string(),
        server_name,
        client_local_addr,
        payload_bytes,
        payload_chunks,
        chunk_delay_ms,
        received_bytes: received.len(),
        echo_matches,
    };
    fs::write(&result_path, serde_json::to_string_pretty(&result)? + "\n")?;

    if !echo_matches {
        return Err(format!(
            "echo mismatch: sent {} bytes, received {} bytes",
            payload.len(),
            received.len()
        )
        .into());
    }
    Ok(())
}

fn deterministic_payload(len: usize) -> Vec<u8> {
    (0..len).map(|index| (index % 251) as u8).collect()
}

fn payload_chunks_for(payload: &[u8], chunks: usize) -> Vec<&[u8]> {
    if payload.is_empty() {
        return vec![payload];
    }
    let chunk_size = payload.len().div_ceil(chunks.max(1)).max(1);
    payload.chunks(chunk_size).collect()
}

fn resolve_addr(addr: &str) -> Result<SocketAddr, AnyError> {
    addr.to_socket_addrs()?
        .next()
        .ok_or_else(|| format!("could not resolve SERVER_ADDR={addr}").into())
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
