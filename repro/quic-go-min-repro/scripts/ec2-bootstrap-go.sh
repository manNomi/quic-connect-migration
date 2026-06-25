#!/usr/bin/env bash
set -euo pipefail

GO_VERSION="${GO_VERSION:-1.26.4}"

version_at_least() {
  local current="$1"
  local required="$2"
  [[ "$(printf '%s\n%s\n' "$required" "$current" | sort -V | tail -n 1)" == "$current" ]]
}

INSTALL_GO=1
if command -v go >/dev/null 2>&1; then
  CURRENT_GO_VERSION="$(go version | awk '{print $3}' | sed 's/^go//')"
  if version_at_least "$CURRENT_GO_VERSION" "$GO_VERSION"; then
    INSTALL_GO=0
  fi
fi

if [[ "$INSTALL_GO" == "1" ]]; then
  case "$(uname -m)" in
    x86_64) GO_ARCH="amd64" ;;
    arm64|aarch64) GO_ARCH="arm64" ;;
    *)
      echo "unsupported architecture: $(uname -m)" >&2
      exit 1
      ;;
  esac

  TMP_DIR="$(mktemp -d)"
  trap 'rm -rf "$TMP_DIR"' EXIT

  curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-${GO_ARCH}.tar.gz" -o "$TMP_DIR/go.tgz"
  sudo rm -rf /usr/local/go
  sudo tar -C /usr/local -xzf "$TMP_DIR/go.tgz"
fi

PROFILE_SNIPPET='export PATH=/usr/local/go/bin:$PATH'
if ! grep -qF "$PROFILE_SNIPPET" "$HOME/.profile" 2>/dev/null; then
  printf '\n%s\n' "$PROFILE_SNIPPET" >> "$HOME/.profile"
fi

export PATH="/usr/local/go/bin:$PATH"
go version

if command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y tcpdump
elif command -v yum >/dev/null 2>&1; then
  sudo yum install -y tcpdump
elif command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y tcpdump
fi
