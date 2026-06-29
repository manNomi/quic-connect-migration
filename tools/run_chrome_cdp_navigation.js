#!/usr/bin/env node
"use strict";

const fs = require("fs/promises");
const net = require("net");
const path = require("path");
const { spawn } = require("child_process");

function parseArgs(argv) {
  const args = {
    "net-log-capture-mode": "Default",
    "timeout-seconds": "30",
    "hold-seconds": "5",
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      throw new Error(`unexpected positional argument: ${token}`);
    }
    const key = token.slice(2);
    const next = argv[index + 1];
    if (next === undefined || next.startsWith("--")) {
      args[key] = "true";
    } else {
      args[key] = next;
      index += 1;
    }
  }
  return args;
}

function requireArg(args, key) {
  const value = args[key];
  if (!value) {
    throw new Error(`missing --${key}`);
  }
  return value;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(() => resolve(address.port));
    });
  });
}

async function pollJSON(url, timeoutMillis) {
  const deadline = Date.now() + timeoutMillis;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return await response.json();
      }
      lastError = new Error(`HTTP ${response.status} from ${url}`);
    } catch (error) {
      lastError = error;
    }
    await sleep(100);
  }
  throw lastError || new Error(`timed out polling ${url}`);
}

async function writeJSONFile(filePath, data) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const tmpPath = `${filePath}.tmp-${process.pid}`;
  await fs.writeFile(tmpPath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
  await fs.rename(tmpPath, filePath);
}

function createCDPClient(wsURL) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsURL);
    let nextID = 1;
    const pending = new Map();
    const eventWaiters = new Map();

    ws.addEventListener("open", () => {
      const client = {
        send(method, params = {}) {
          const id = nextID;
          nextID += 1;
          const payload = JSON.stringify({ id, method, params });
          return new Promise((res, rej) => {
            pending.set(id, { resolve: res, reject: rej, method });
            ws.send(payload);
          });
        },
        waitForEvent(method, timeoutMillis) {
          return new Promise((res, rej) => {
            const timer = setTimeout(() => {
              const waiters = eventWaiters.get(method) || [];
              eventWaiters.set(
                method,
                waiters.filter((waiter) => waiter.reject !== rej),
              );
              rej(new Error(`timed out waiting for ${method}`));
            }, timeoutMillis);
            const waiters = eventWaiters.get(method) || [];
            waiters.push({
              resolve: (event) => {
                clearTimeout(timer);
                res(event);
              },
              reject: rej,
            });
            eventWaiters.set(method, waiters);
          });
        },
        close() {
          ws.close();
        },
      };
      resolve(client);
    });

    ws.addEventListener("message", (message) => {
      let event;
      try {
        event = JSON.parse(message.data);
      } catch {
        return;
      }
      if (event.id !== undefined) {
        const waiter = pending.get(event.id);
        if (!waiter) {
          return;
        }
        pending.delete(event.id);
        if (event.error) {
          waiter.reject(new Error(`${waiter.method}: ${event.error.message || JSON.stringify(event.error)}`));
        } else {
          waiter.resolve(event.result || {});
        }
        return;
      }
      if (event.method) {
        const waiters = eventWaiters.get(event.method) || [];
        if (waiters.length > 0) {
          const waiter = waiters.shift();
          eventWaiters.set(event.method, waiters);
          waiter.resolve(event);
        }
      }
    });

    ws.addEventListener("error", (event) => {
      reject(new Error(`websocket error: ${event.message || "unknown"}`));
    });
  });
}

function chromeArgs(options) {
  const args = [
    "--headless=new",
    "--no-first-run",
    "--disable-gpu",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-sync",
    "--disable-extensions",
    "--enable-quic",
    `--user-data-dir=${options.profileDir}`,
    `--log-net-log=${options.netlogPath}`,
    `--net-log-capture-mode=${options.netLogCaptureMode}`,
    `--remote-debugging-port=${options.remoteDebuggingPort}`,
  ];
  if (options.originToForceQuicOn) {
    args.push(`--origin-to-force-quic-on=${options.originToForceQuicOn}`);
  }
  if (options.spkiHash) {
    args.push(`--ignore-certificate-errors-spki-list=${options.spkiHash}`);
  }
  args.push("about:blank");
  return args;
}

async function waitForExit(child, timeoutMillis) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      child.kill("SIGTERM");
    }, timeoutMillis);
    child.on("exit", (code, signal) => {
      clearTimeout(timer);
      resolve({ code, signal });
    });
  });
}

async function evaluateReadyExpression(client, expression) {
  const wrappedExpression = `(async () => {
    try {
      const value = await (${expression});
      return JSON.stringify({ ok: Boolean(value), value: String(value) });
    } catch (error) {
      return JSON.stringify({
        ok: false,
        error: error && error.message ? error.message : String(error)
      });
    }
  })()`;
  const evaluation = await client.send("Runtime.evaluate", {
    expression: wrappedExpression,
    returnByValue: true,
    awaitPromise: true,
  });
  const raw = evaluation.result && evaluation.result.value ? evaluation.result.value : "{}";
  return JSON.parse(raw);
}

async function waitForReadyExpression(client, options) {
  const deadline = Date.now() + options.timeoutSeconds * 1000;
  const startedAt = new Date().toISOString();
  let attempts = 0;
  let lastEvaluation = null;

  while (Date.now() <= deadline) {
    attempts += 1;
    lastEvaluation = await evaluateReadyExpression(client, options.expression);
    if (lastEvaluation.ok) {
      const result = {
        ok: true,
        expression: options.expression,
        attempts,
        started_at: startedAt,
        matched_at: new Date().toISOString(),
        last_evaluation: lastEvaluation,
      };
      if (options.outputPath) {
        await writeJSONFile(options.outputPath, result);
      }
      return result;
    }
    await sleep(options.pollIntervalMillis);
  }

  const result = {
    ok: false,
    expression: options.expression,
    attempts,
    started_at: startedAt,
    timed_out_at: new Date().toISOString(),
    timeout_seconds: options.timeoutSeconds,
    last_evaluation: lastEvaluation,
  };
  if (options.outputPath) {
    await writeJSONFile(options.outputPath, result);
  }
  const error = new Error(`ready expression did not match within ${options.timeoutSeconds}s`);
  error.readyResult = result;
  throw error;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const chromeBin = requireArg(args, "chrome-bin");
  const url = requireArg(args, "url");
  const artifactDir = requireArg(args, "artifact-dir");
  const netlogName = requireArg(args, "netlog-name");
  const dumpName = requireArg(args, "dump-name");
  const timeoutSeconds = Number(args["timeout-seconds"]);
  const holdSeconds = Number(args["hold-seconds"]);
  const readyExpression = args["ready-expression"] || "";
  const readyTimeoutSeconds = Number(args["ready-timeout-seconds"] || timeoutSeconds);
  const readyPollIntervalMillis = Number(args["ready-poll-interval-ms"] || "250");
  const profileDirName = args["profile-dir-name"] || "profile-cdp";
  const port = await freePort();

  const chromeDir = path.join(artifactDir, "chrome");
  await fs.mkdir(chromeDir, { recursive: true });
  const stderrPath = path.join(chromeDir, `${dumpName}.stderr.log`);
  const summaryPath = path.join(chromeDir, "cdp-summary.json");
  const profileDir = path.join(chromeDir, profileDirName);
  const netlogPath = path.join(chromeDir, netlogName);
  const dumpPath = path.join(chromeDir, dumpName);
  const stderr = await fs.open(stderrPath, "w");

  const child = spawn(
    chromeBin,
    chromeArgs({
      profileDir,
      netlogPath,
      netLogCaptureMode: args["net-log-capture-mode"],
      remoteDebuggingPort: port,
      originToForceQuicOn: args["origin-to-force-quic-on"],
      spkiHash: args["spki-hash"],
    }),
    {
      stdio: ["ignore", "ignore", stderr.fd],
    },
  );

  let client;
  const summary = {
    url,
    hold_seconds: holdSeconds,
    remote_debugging_port: port,
    navigation_loaded: false,
    evaluation_ok: false,
    ready: readyExpression
      ? {
          enabled: true,
          expression: readyExpression,
          timeout_seconds: readyTimeoutSeconds,
          poll_interval_ms: readyPollIntervalMillis,
          output: args["ready-output"] || null,
          ok: false,
        }
      : { enabled: false },
    chrome_exit: null,
  };

  try {
    const targets = await pollJSON(`http://127.0.0.1:${port}/json/list`, Math.min(timeoutSeconds * 1000, 10000));
    const page = targets.find((target) => target.type === "page" && target.webSocketDebuggerUrl);
    if (!page) {
      throw new Error("no debuggable page target found");
    }
    client = await createCDPClient(page.webSocketDebuggerUrl);
    await client.send("Page.enable");
    await client.send("Runtime.enable");
    await client.send("Network.enable");

    const loadPromise = client.waitForEvent("Page.loadEventFired", Math.min(timeoutSeconds * 1000, 15000)).catch(() => null);
    await client.send("Page.navigate", { url });
    const loadEvent = await loadPromise;
    summary.navigation_loaded = Boolean(loadEvent);

    if (readyExpression) {
      const ready = await waitForReadyExpression(client, {
        expression: readyExpression,
        timeoutSeconds: readyTimeoutSeconds,
        pollIntervalMillis: readyPollIntervalMillis,
        outputPath: args["ready-output"] || "",
      });
      summary.ready = {
        ...summary.ready,
        ...ready,
      };
    }

    await sleep(Math.max(0, holdSeconds) * 1000);

    const expression = `(() => JSON.stringify({
      url: location.href,
      readyState: document.readyState,
      title: document.title,
      bodyDataset: Object.fromEntries(Object.entries(document.body ? document.body.dataset : {})),
      text: document.body ? document.body.innerText : "",
      html: document.documentElement ? document.documentElement.outerHTML : ""
    }))()`;
    const evaluation = await client.send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    const raw = evaluation.result && evaluation.result.value ? evaluation.result.value : "{}";
    const pageState = JSON.parse(raw);
    await fs.writeFile(dumpPath, `${pageState.html || ""}\n`, "utf8");
    summary.evaluation_ok = true;
    summary.page_state = {
      url: pageState.url,
      ready_state: pageState.readyState,
      title: pageState.title,
      body_dataset: pageState.bodyDataset,
      text: pageState.text,
      html_bytes: Buffer.byteLength(pageState.html || "", "utf8"),
    };

    try {
      await client.send("Browser.close");
    } catch {
      child.kill("SIGTERM");
    }
  } catch (error) {
    if (error.readyResult) {
      summary.ready = {
        ...summary.ready,
        ...error.readyResult,
      };
    }
    summary.error = error.message;
    child.kill("SIGTERM");
    await fs.writeFile(dumpPath, `CDP_ERROR: ${error.message}\n`, "utf8");
  } finally {
    if (client) {
      client.close();
    }
    const exit = await waitForExit(child, 5000);
    summary.chrome_exit = exit.code;
    summary.chrome_signal = exit.signal;
    await fs.writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
    await stderr.close();
  }

  if (summary.error || !summary.evaluation_ok) {
    return 1;
  }
  return 0;
}

main()
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    console.error(error.stack || error.message);
    process.exitCode = 1;
  });
