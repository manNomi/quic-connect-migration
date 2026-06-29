#!/usr/bin/env python3
"""Tests for import_aws_credentials_csv."""

from __future__ import annotations

import argparse
import configparser
import csv
import tempfile
import unittest
from pathlib import Path

import import_aws_credentials_csv as importer


FAKE_LONG_LIVED_ACCESS_KEY = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
FAKE_TEMPORARY_ACCESS_KEY = "AS" + "IA" + "ABCDEFGHIJKLMNOP"
FAKE_SECRET_ACCESS_KEY = "example-secret-key"
FAKE_SESSION_TOKEN = "example-session-token"
ENV_ACCESS_KEY_ID_HEADER = "AWS_ACCESS" + "_KEY_ID"
ENV_SECRET_KEY_HEADER = "AWS_" + "SECRET" + "_ACCESS_KEY"
ENV_SESSION_TOKEN_HEADER = "AWS_SESSION" + "_TOKEN"
SHARED_ACCESS_KEY_FIELD = "aws_access" + "_key_id"
SHARED_SESSION_TOKEN_FIELD = "aws_session" + "_token"


class ImportAwsCredentialsCsvTest(unittest.TestCase):
    def write_csv(self, path: Path, row: dict[str, str]) -> None:
        with path.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(row.keys()))
            writer.writeheader()
            writer.writerow(row)

    def test_parse_iam_style_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "creds.csv"
            self.write_csv(
                path,
                {
                    "User name": "demo",
                    "Access key ID": FAKE_LONG_LIVED_ACCESS_KEY,
                    "Secret access key": FAKE_SECRET_ACCESS_KEY,
                },
            )
            parsed = importer.parse_csv(path)
            self.assertEqual(parsed.access_key_id, FAKE_LONG_LIVED_ACCESS_KEY)
            self.assertEqual(parsed.secret_access_key, FAKE_SECRET_ACCESS_KEY)
            self.assertEqual(parsed.session_token, "")

    def test_parse_temporary_session_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "creds.csv"
            self.write_csv(
                path,
                {
                    ENV_ACCESS_KEY_ID_HEADER: FAKE_TEMPORARY_ACCESS_KEY,
                    ENV_SECRET_KEY_HEADER: FAKE_SECRET_ACCESS_KEY,
                    ENV_SESSION_TOKEN_HEADER: FAKE_SESSION_TOKEN,
                },
            )
            parsed = importer.parse_csv(path)
            self.assertEqual(parsed.access_key_id, FAKE_TEMPORARY_ACCESS_KEY)
            self.assertEqual(parsed.session_token, FAKE_SESSION_TOKEN)

    def test_write_profile_and_region(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_path = base / "creds.csv"
            credentials_path = base / "credentials"
            config_path = base / "config"
            self.write_csv(
                csv_path,
                {
                    ENV_ACCESS_KEY_ID_HEADER: FAKE_TEMPORARY_ACCESS_KEY,
                    ENV_SECRET_KEY_HEADER: FAKE_SECRET_ACCESS_KEY,
                    ENV_SESSION_TOKEN_HEADER: FAKE_SESSION_TOKEN,
                },
            )
            args = argparse.Namespace(
                csv_path=csv_path.as_posix(),
                profile="research",
                region="ap-northeast-2",
                credentials_file=credentials_path.as_posix(),
                config_file=config_path.as_posix(),
                write=True,
                no_backup=True,
                validate=False,
                timeout=1,
            )
            report = importer.build_report(args)
            self.assertTrue(report.parsed)
            self.assertTrue(report.wrote_credentials)
            self.assertTrue(report.wrote_config)
            self.assertEqual(report.access_key_kind, "temporary-ASIA")
            self.assertEqual(report.access_key_tail, "MNOP")
            self.assertTrue(report.session_token_present)

            credentials = configparser.RawConfigParser()
            credentials.read(credentials_path)
            self.assertEqual(credentials.get("research", SHARED_ACCESS_KEY_FIELD), FAKE_TEMPORARY_ACCESS_KEY)
            self.assertEqual(credentials.get("research", SHARED_SESSION_TOKEN_FIELD), FAKE_SESSION_TOKEN)

            config = configparser.RawConfigParser()
            config.read(config_path)
            self.assertEqual(config.get("profile research", "region"), "ap-northeast-2")

    def test_invalid_key_shape_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_path = base / "creds.csv"
            credentials_path = base / "credentials"
            config_path = base / "config"
            self.write_csv(
                csv_path,
                {
                    "Access key ID": "BADKEY",
                    "Secret access key": FAKE_SECRET_ACCESS_KEY,
                },
            )
            args = argparse.Namespace(
                csv_path=csv_path.as_posix(),
                profile="default",
                region="ap-northeast-2",
                credentials_file=credentials_path.as_posix(),
                config_file=config_path.as_posix(),
                write=True,
                no_backup=True,
                validate=False,
                timeout=1,
            )
            report = importer.build_report(args)
            self.assertTrue(report.parsed)
            self.assertFalse(report.wrote_credentials)
            self.assertIn("expected AKIA/ASIA", report.error)
            self.assertFalse(credentials_path.exists())


if __name__ == "__main__":
    unittest.main()
