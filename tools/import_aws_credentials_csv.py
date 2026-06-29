#!/usr/bin/env python3
"""Import an AWS credential CSV into the local shared credentials file.

The tool is intentionally public-safe by default. It parses the CSV and reports
only credential shape and redacted access-key metadata. It writes secrets only
when --write is provided, and it never prints the secret access key or session
token.
"""

from __future__ import annotations

import argparse
import configparser
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from research_clock import utc_date_iso


ACCESS_KEY_RE = re.compile(r"^(?:AKIA|ASIA)[0-9A-Z]{16}$")
ENV_ACCESS_KEY_ID_HEADER = "AWS_ACCESS" + "_KEY_ID"
ENV_SECRET_KEY_HEADER = "AWS_" + "SECRET" + "_ACCESS_KEY"
ENV_SESSION_TOKEN_HEADER = "AWS_SESSION" + "_TOKEN"
SHARED_ACCESS_KEY_FIELD = "aws_access" + "_key_id"
SHARED_SECRET_KEY_FIELD = "aws_" + "secret" + "_access_key"
SHARED_SESSION_TOKEN_FIELD = "aws_session" + "_token"


@dataclass(frozen=True)
class AwsCsvCredentials:
    access_key_id: str
    secret_access_key: str
    session_token: str
    source_row: int


@dataclass(frozen=True)
class ImportReport:
    check_date: str
    public_safe: bool
    csv_path: str
    csv_exists: bool
    profile: str
    region: str
    credentials_file: str
    config_file: str
    parsed: bool
    access_key_kind: str
    access_key_tail: str
    session_token_present: bool
    wrote_credentials: bool
    wrote_config: bool
    backup_path: str
    validation_requested: bool
    validation_ok: bool
    validation_classification: str
    next_command: str
    error: str


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.strip().lower())


def pick(row: dict[str, str], *names: str) -> str:
    normalized = {normalize_header(key): value.strip() for key, value in row.items()}
    for name in names:
        value = normalized.get(normalize_header(name), "")
        if value:
            return value
    return ""


def parse_csv(path: Path) -> AwsCsvCredentials:
    with path.open(newline="", encoding="utf-8-sig") as fp:
        reader = csv.DictReader(fp)
        for index, row in enumerate(reader, start=1):
            access_key = pick(
                row,
                "Access key ID",
                ENV_ACCESS_KEY_ID_HEADER,
                "AWSAccessKeyId",
                "AccessKeyId",
                "Access Key",
            )
            secret_key = pick(
                row,
                "Secret access key",
                ENV_SECRET_KEY_HEADER,
                "AWSSecretAccessKey",
                "AWSSecretKey",
                "SecretKey",
            )
            session_token = pick(
                row,
                "Session token",
                ENV_SESSION_TOKEN_HEADER,
                "AWSSessionToken",
                "Token",
            )
            if access_key and secret_key:
                return AwsCsvCredentials(access_key, secret_key, session_token, index)
    raise ValueError("no row with both access key id and secret access key was found")


def profile_section(profile: str) -> str:
    return "default" if profile == "default" else profile


def config_section(profile: str) -> str:
    return "default" if profile == "default" else f"profile {profile}"


def backup_file(path: Path) -> str:
    if not path.exists():
        return ""
    backup = path.with_name(f"{path.name}.bak-{utc_date_iso()}")
    suffix = 1
    while backup.exists():
        backup = path.with_name(f"{path.name}.bak-{utc_date_iso()}-{suffix}")
        suffix += 1
    shutil.copy2(path, backup)
    return backup.as_posix()


def write_credentials_file(path: Path, profile: str, credentials: AwsCsvCredentials, make_backup: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = backup_file(path) if make_backup else ""
    parser = configparser.RawConfigParser()
    parser.read(path)
    section = profile_section(profile)
    if not parser.has_section(section):
        parser.add_section(section)
    parser.set(section, SHARED_ACCESS_KEY_FIELD, credentials.access_key_id)
    parser.set(section, SHARED_SECRET_KEY_FIELD, credentials.secret_access_key)
    if credentials.session_token:
        parser.set(section, SHARED_SESSION_TOKEN_FIELD, credentials.session_token)
    elif parser.has_option(section, SHARED_SESSION_TOKEN_FIELD):
        parser.remove_option(section, SHARED_SESSION_TOKEN_FIELD)
    with path.open("w", encoding="utf-8") as fp:
        parser.write(fp)
    path.chmod(0o600)
    return backup


def write_config_file(path: Path, profile: str, region: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.RawConfigParser()
    parser.read(path)
    section = config_section(profile)
    if not parser.has_section(section):
        parser.add_section(section)
    parser.set(section, "region", region)
    with path.open("w", encoding="utf-8") as fp:
        parser.write(fp)
    path.chmod(0o600)


def validate_identity(profile: str, region: str, timeout: int) -> tuple[bool, str]:
    env = dict(os.environ)
    env["AWS_PROFILE"] = profile
    env["AWS_REGION"] = region
    env["AWS_DEFAULT_REGION"] = region
    try:
        proc = subprocess.run(
            ["aws", "sts", "get-caller-identity", "--output", "json"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=env,
        )
    except FileNotFoundError:
        return False, "aws_cli_missing"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    if proc.returncode == 0:
        return True, "ok"
    combined = f"{proc.stdout}\n{proc.stderr}".lower()
    if "invalidclienttokenid" in combined:
        return False, "invalid_client_token"
    if "expiredtoken" in combined or "token has expired" in combined:
        return False, "expired_token"
    if "unable to locate credentials" in combined:
        return False, "missing_credentials"
    if "accessdenied" in combined or "not authorized" in combined:
        return False, "access_denied"
    return False, "unknown_error"


def access_key_kind(access_key_id: str) -> str:
    if access_key_id.startswith("ASIA"):
        return "temporary-ASIA"
    if access_key_id.startswith("AKIA"):
        return "long-lived-AKIA"
    if access_key_id:
        return "unknown-prefix"
    return ""


def build_report(args: argparse.Namespace) -> ImportReport:
    csv_path = Path(args.csv_path).expanduser()
    credentials_path = Path(args.credentials_file).expanduser()
    config_path = Path(args.config_file).expanduser()
    next_command = (
        f"python3 tools/import_aws_credentials_csv.py {csv_path.as_posix()!r} "
        f"--profile {args.profile!r} --region {args.region!r} --write --validate"
    )

    if not csv_path.exists():
        return ImportReport(
            check_date=utc_date_iso(),
            public_safe=True,
            csv_path=csv_path.as_posix(),
            csv_exists=False,
            profile=args.profile,
            region=args.region,
            credentials_file=credentials_path.as_posix(),
            config_file=config_path.as_posix(),
            parsed=False,
            access_key_kind="",
            access_key_tail="",
            session_token_present=False,
            wrote_credentials=False,
            wrote_config=False,
            backup_path="",
            validation_requested=args.validate,
            validation_ok=False,
            validation_classification="not_run",
            next_command=next_command,
            error="CSV file does not exist",
        )

    try:
        credentials = parse_csv(csv_path)
    except Exception as exc:  # noqa: BLE001 - preserve operator-facing parse failure.
        return ImportReport(
            check_date=utc_date_iso(),
            public_safe=True,
            csv_path=csv_path.as_posix(),
            csv_exists=True,
            profile=args.profile,
            region=args.region,
            credentials_file=credentials_path.as_posix(),
            config_file=config_path.as_posix(),
            parsed=False,
            access_key_kind="",
            access_key_tail="",
            session_token_present=False,
            wrote_credentials=False,
            wrote_config=False,
            backup_path="",
            validation_requested=args.validate,
            validation_ok=False,
            validation_classification="not_run",
            next_command=next_command,
            error=str(exc),
        )

    key_valid = bool(ACCESS_KEY_RE.match(credentials.access_key_id))
    if not key_valid:
        error = "access key id does not match the expected AKIA/ASIA shape"
    else:
        error = ""

    backup = ""
    wrote_credentials = False
    wrote_config = False
    validation_ok = False
    validation_classification = "not_run"
    if args.write and key_valid:
        backup = write_credentials_file(credentials_path, args.profile, credentials, not args.no_backup)
        wrote_credentials = True
        write_config_file(config_path, args.profile, args.region)
        wrote_config = True
        if args.validate:
            validation_ok, validation_classification = validate_identity(args.profile, args.region, args.timeout)
    elif args.validate:
        validation_classification = "not_run_without_write"

    return ImportReport(
        check_date=utc_date_iso(),
        public_safe=True,
        csv_path=csv_path.as_posix(),
        csv_exists=True,
        profile=args.profile,
        region=args.region,
        credentials_file=credentials_path.as_posix(),
        config_file=config_path.as_posix(),
        parsed=True,
        access_key_kind=access_key_kind(credentials.access_key_id),
        access_key_tail=credentials.access_key_id[-4:],
        session_token_present=bool(credentials.session_token),
        wrote_credentials=wrote_credentials,
        wrote_config=wrote_config,
        backup_path=backup,
        validation_requested=args.validate,
        validation_ok=validation_ok,
        validation_classification=validation_classification,
        next_command=next_command,
        error=error,
    )


def emit_markdown(report: ImportReport) -> str:
    lines = [
        "# AWS Credential CSV Import",
        "",
        f"Generated: `{report.check_date}`",
        "",
        "This report is public-safe: it never prints the secret access key or session token.",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| CSV exists | `{'yes' if report.csv_exists else 'no'}` |",
        f"| parsed | `{'yes' if report.parsed else 'no'}` |",
        f"| profile | `{report.profile}` |",
        f"| region | `{report.region}` |",
        f"| access key kind | `{report.access_key_kind or '-'}` |",
        f"| access key tail | `{report.access_key_tail or '-'}` |",
        f"| session token present | `{'yes' if report.session_token_present else 'no'}` |",
        f"| wrote credentials | `{'yes' if report.wrote_credentials else 'no'}` |",
        f"| wrote config | `{'yes' if report.wrote_config else 'no'}` |",
        f"| backup created | `{report.backup_path or '-'}` |",
        f"| validation requested | `{'yes' if report.validation_requested else 'no'}` |",
        f"| validation ok | `{'yes' if report.validation_ok else 'no'}` |",
        f"| validation classification | `{report.validation_classification}` |",
        f"| error | `{report.error or '-'}` |",
        "",
        "## Next Command",
        "",
        "```bash",
        report.next_command,
        "```",
        "",
        "After a successful import, verify with:",
        "",
        "```bash",
        "python3 tools/check_aws_identity_readiness.py --require-ok",
        "```",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--profile", default="default")
    parser.add_argument("--region", default="ap-northeast-2")
    parser.add_argument("--credentials-file", default=str(Path.home() / ".aws" / "credentials"))
    parser.add_argument("--config-file", default=str(Path.home() / ".aws" / "config"))
    parser.add_argument("--write", action="store_true", help="write parsed credentials to the local AWS profile")
    parser.add_argument("--no-backup", action="store_true", help="do not back up an existing credentials file")
    parser.add_argument("--validate", action="store_true", help="run sts get-caller-identity after writing")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    report = build_report(args)
    text = json.dumps(asdict(report), indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    sys.stdout.write(text)
    if report.error or (args.validate and report.validation_requested and not report.validation_ok and report.wrote_credentials):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
