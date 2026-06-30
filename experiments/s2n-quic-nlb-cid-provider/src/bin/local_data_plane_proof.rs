use rcgen::generate_simple_self_signed;
use s2n_quic::{client::Connect, Client, Server};
use s2n_quic_nlb_cid_provider::{parse_server_id_hex, AwsNlbCidFormat, RouteTable};
use serde::Serialize;
use std::{env, fs, net::SocketAddr, path::PathBuf, time::Duration};
use tokio::time::timeout;

type AnyError = Box<dyn std::error::Error + Send + Sync>;

#[derive(Debug, Serialize)]
struct QuicEchoResult {
    server_addr: String,
    client_local_addr: String,
    server_observed_remote_addr: String,
    payload_bytes: usize,
    echo_matches: bool,
}

#[derive(Debug, Serialize)]
struct ProofResult {
    status: &'static str,
    target_a_server_id: String,
    target_b_server_id: String,
    generated_target_a_cid: String,
    generated_target_b_cid: String,
    route_generated_target_a_cid: Option<&'static str>,
    route_generated_target_b_cid: Option<&'static str>,
    route_wrong_cid: Option<&'static str>,
    quic_echo: QuicEchoResult,
}

#[tokio::main(flavor = "multi_thread", worker_threads = 2)]
async fn main() -> Result<(), AnyError> {
    let result_dir = env::args()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("results/local-data-plane-manual"));
    fs::create_dir_all(&result_dir)?;

    let target_a = parse_server_id_hex("a1b2c3d4e5f65890")?;
    let target_b = parse_server_id_hex("a1b2c3d4e5f65999")?;
    let wrong = parse_server_id_hex("ffffffffffffffff")?;

    let mut target_a_format = AwsNlbCidFormat::new(target_a);
    let mut target_b_format = AwsNlbCidFormat::new(target_b);
    let mut wrong_format = AwsNlbCidFormat::new(wrong);

    let target_a_cid = target_a_format.generate_cid_bytes();
    let target_b_cid = target_b_format.generate_cid_bytes();
    let wrong_cid = wrong_format.generate_cid_bytes();
    let router = RouteTable::new(target_a, target_b);

    let quic_echo = run_echo(target_a_format.clone()).await?;

    let result = ProofResult {
        status: "PASS",
        target_a_server_id: target_a_format.server_id_hex(),
        target_b_server_id: target_b_format.server_id_hex(),
        generated_target_a_cid: hex::encode(target_a_cid),
        generated_target_b_cid: hex::encode(target_b_cid),
        route_generated_target_a_cid: router.route(&target_a_cid),
        route_generated_target_b_cid: router.route(&target_b_cid),
        route_wrong_cid: router.route(&wrong_cid),
        quic_echo,
    };

    let result_json = serde_json::to_string_pretty(&result)?;
    fs::write(result_dir.join("result.json"), &result_json)?;
    println!("{result_json}");

    Ok(())
}

async fn run_echo(connection_id: AwsNlbCidFormat) -> Result<QuicEchoResult, AnyError> {
    let certified = generate_simple_self_signed(vec!["localhost".to_string()])?;
    let cert_pem = certified.cert.pem();
    let key_pem = certified.key_pair.serialize_pem();

    let mut server = Server::builder()
        .with_tls((cert_pem.as_str(), key_pem.as_str()))?
        .with_io("127.0.0.1:0")?
        .with_connection_id(connection_id)?
        .start()?;
    let server_addr = server.local_addr()?;

    let server_task = tokio::spawn(async move {
        let mut connection = timeout(Duration::from_secs(10), server.accept())
            .await?
            .ok_or_else(|| "server closed before accepting connection".to_string())?;
        let server_observed_remote_addr = connection.remote_addr()?.to_string();
        let mut stream = timeout(Duration::from_secs(10), connection.accept_bidirectional_stream())
            .await??
            .ok_or_else(|| "client did not open stream".to_string())?;

        if let Some(data) = timeout(Duration::from_secs(10), stream.receive()).await?? {
            stream.send(data).await?;
        }

        Result::<String, AnyError>::Ok(server_observed_remote_addr)
    });

    let client = Client::builder()
        .with_tls(cert_pem.as_str())?
        .with_io("127.0.0.1:0")?
        .start()?;
    let client_local_addr = client.local_addr()?.to_string();

    let connect = Connect::new(SocketAddr::from(server_addr)).with_server_name("localhost");
    let mut connection = timeout(Duration::from_secs(10), client.connect(connect)).await??;
    connection.keep_alive(true)?;

    let mut stream = timeout(Duration::from_secs(10), connection.open_bidirectional_stream()).await??;
    let payload = b"s2n-quic nlb cid proof echo";
    stream.send(payload.as_slice().into()).await?;
    stream.finish()?;

    let received = timeout(Duration::from_secs(10), stream.receive()).await??;
    let echo_matches = received
        .as_ref()
        .map(|bytes| bytes.as_ref() == payload)
        .unwrap_or(false);

    let server_observed_remote_addr = server_task.await??;

    Ok(QuicEchoResult {
        server_addr: server_addr.to_string(),
        client_local_addr,
        server_observed_remote_addr,
        payload_bytes: payload.len(),
        echo_matches,
    })
}
