#!/usr/bin/env python3
"""Tests for plan_public_origin_recovery."""

from __future__ import annotations

import unittest

import plan_public_origin_recovery as planner


class PlanPublicOriginRecoveryTest(unittest.TestCase):
    def test_aws_credentials_invalid_token_blocks_first(self) -> None:
        step = planner.step_aws_credentials({"aws": {"identity_ok": False, "classification": "invalid_client_token"}})
        self.assertEqual(step.step_id, "aws-credentials")
        self.assertEqual(step.status, "blocked")
        self.assertIn("import_aws_credentials_csv.py", step.next_command)

    def test_origin_ready_when_public_readiness_ok(self) -> None:
        step = planner.step_origin_reachable({"ok": True}, {"tcp": {"classification": "ok"}})
        self.assertEqual(step.step_id, "public-origin-reachable")
        self.assertEqual(step.status, "ready")

    def test_origin_recovery_uses_aws_when_identity_ready(self) -> None:
        step = planner.step_origin_reachable(
            {"ok": False},
            {
                "tcp": {"classification": "connection_refused"},
                "recovery_paths": {"aws_identity_ready": True, "remote_ssh_ready": False},
            },
        )
        self.assertEqual(step.status, "blocked")
        self.assertIn("aws-preflight.sh", step.next_command)
        self.assertIn("build_controlled_public_origin_deploy_packet.py", step.next_command)

    def test_active_trials_wait_until_origin_ready(self) -> None:
        step = planner.step_active_trials({"complete": False}, {"ok": False})
        self.assertEqual(step.status, "waiting")
        self.assertIn("origin is unreachable", step.reason)

    def test_active_trials_next_when_origin_ready_and_protocol_incomplete(self) -> None:
        step = planner.step_active_trials({"complete": False}, {"ok": True})
        self.assertEqual(step.status, "next")
        self.assertIn("final-chrome-network-change-run.sh", step.next_command)


if __name__ == "__main__":
    unittest.main()
