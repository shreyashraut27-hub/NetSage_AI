import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.checker import DeterministicChecker, CommandSafetyValidator
from src.engine import DiagnosticEngine
from src.connector import CiscoDeviceConnector

class TestNetSageDiagnostics(unittest.TestCase):

    def setUp(self):
        self.checker = DeterministicChecker()
        self.safety_validator = CommandSafetyValidator()
        self.engine = DiagnosticEngine()
        self.connector = CiscoDeviceConnector(mode="simulation")

    # ==================== 1. DETERMINISTIC RULE TESTS ====================

    def test_deterministic_admin_down(self):
        show_output = "GigabitEthernet0/0.30 is administratively down, line protocol is down"
        res = self.checker.check(show_output)
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "ERRORS_DETECTED")
        self.assertEqual(res["diagnostic"]["osi_layer"], "Layer 1")
        self.assertIn("GigabitEthernet0/0.30", res["diagnostic"]["root_cause"])
        self.assertTrue(res["diagnostic"]["is_safe"])
        self.assertIn("no shutdown", res["diagnostic"]["fix_steps"][-1])

    def test_deterministic_vlan_mismatch(self):
        show_output = (
            "FastEthernet0/1 is up, line protocol is up\n"
            "Switchport: Enabled\n"
            "Administrative Mode: dynamic auto\n"
            "Operational Mode: static access\n"
            "Access Mode VLAN: 1 (default)"
        )
        res = self.checker.check(show_output)
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "ERRORS_DETECTED")
        self.assertEqual(res["diagnostic"]["osi_layer"], "Layer 2")
        self.assertIn("FastEthernet0/1", res["diagnostic"]["root_cause"])
        self.assertIn("VLAN 1", res["diagnostic"]["root_cause"])
        self.assertTrue(res["diagnostic"]["is_safe"])

    def test_deterministic_missing_overload(self):
        show_output = (
            "ip nat inside source list 1 interface GigabitEthernet0/1\n"
            "NAT configuration missing overload"
        )
        res = self.checker.check(show_output)
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "ERRORS_DETECTED")
        self.assertEqual(res["diagnostic"]["osi_layer"], "Layer 3")
        self.assertIn("GigabitEthernet0/1", res["diagnostic"]["root_cause"])
        self.assertTrue(res["diagnostic"]["is_safe"])

    def test_deterministic_bpdu_guard(self):
        show_output = "FastEthernet0/5 is down, line protocol is down (err-disabled)\n  BPDU guard enabled on port received BPDU"
        res = self.checker.check(show_output)
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "ERRORS_DETECTED")
        self.assertEqual(res["diagnostic"]["osi_layer"], "Layer 2")
        self.assertIn("BPDU Guard", res["diagnostic"]["root_cause"])
        self.assertTrue(res["diagnostic"]["is_safe"])

    def test_deterministic_port_security(self):
        show_output = "FastEthernet0/10 is down, line protocol is down (err-disabled)\n  Port Security Violation: SecureMacAddr violation on MAC 0011.2233.4455"
        res = self.checker.check(show_output)
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "ERRORS_DETECTED")
        self.assertEqual(res["diagnostic"]["osi_layer"], "Layer 2")
        self.assertIn("port-security", res["diagnostic"]["root_cause"])
        self.assertTrue(res["diagnostic"]["is_safe"])

    def test_deterministic_native_vlan_mismatch(self):
        show_output = "%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on GigabitEthernet0/1 (99) with SW2 GigabitEthernet0/1 (1)."
        res = self.checker.check(show_output)
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "ERRORS_DETECTED")
        self.assertEqual(res["diagnostic"]["osi_layer"], "Layer 2")
        self.assertIn("Native VLAN mismatch", res["diagnostic"]["root_cause"])
        self.assertTrue(res["diagnostic"]["is_safe"])

    def test_deterministic_ssh_disabled(self):
        show_output = "% SSH has not been enabled - please create rsa keys first."
        res = self.checker.check(show_output)
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "ERRORS_DETECTED")
        self.assertEqual(res["diagnostic"]["osi_layer"], "Layer 7")
        self.assertIn("SSH is disabled", res["diagnostic"]["root_cause"])
        self.assertTrue(res["diagnostic"]["is_safe"])

    # ==================== 2. COMMAND SAFETY GATE TESTS ====================

    def test_safety_gate_blocks_destructive_commands(self):
        dangerous_commands = [
            "reload",
            "write erase",
            "erase startup-config",
            "format flash:",
            "delete /recursive flash:configs",
            "boot system flash:bad_ios.bin",
            "no aaa new-model",
            "factory-reset"
        ]
        for cmd in dangerous_commands:
            is_safe, warning = self.safety_validator.validate_command(cmd)
            self.assertFalse(is_safe, f"Safety gate failed to block dangerous command: {cmd}")
            self.assertIsNotNone(warning)

    def test_safety_gate_allows_benign_commands(self):
        safe_commands = [
            "configure terminal",
            "interface GigabitEthernet0/0.10",
            "no shutdown",
            "switchport access vlan 20",
            "ip ospf hello-interval 10",
            "crypto key generate rsa",
            "ip nat inside source list 1 interface Gi0/1 overload"
        ]
        for cmd in safe_commands:
            is_safe, warning = self.safety_validator.validate_command(cmd)
            self.assertTrue(is_safe, f"Safety gate incorrectly blocked safe command: {cmd}")
            self.assertIsNone(warning)

    # ==================== 3. 30 BENCHMARK CASES ENGINE COVERAGE ====================

    def test_all_30_benchmark_cases_resolve(self):
        self.assertEqual(len(self.engine.fallback_catalog), 30, "Fallback catalog must contain all 30 benchmark cases.")
        for case_num in range(1, 31):
            case_id = f"NET-{case_num:03d}"
            self.assertIn(case_id, self.engine.fallback_catalog)
            entry = self.engine.fallback_catalog[case_id]
            self.assertIn("root_cause", entry)
            self.assertIn("osi_layer", entry)
            self.assertIn("confidence", entry)
            self.assertIn("fix_steps", entry)
            self.assertGreater(len(entry["fix_steps"]), 0)

    # ==================== 4. CONNECTOR & DRY-RUN TESTS ====================

    def test_device_connector_simulation_and_dry_run(self):
        safe_cmds = ["configure terminal", "interface Gi0/0.30", "no shutdown"]
        res = self.connector.deploy_remediation("R1", safe_cmds, dry_run=True)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "DRY_RUN_PASSED")

        res_deployed = self.connector.deploy_remediation("R1", safe_cmds, dry_run=False)
        self.assertTrue(res_deployed["success"])
        self.assertEqual(res_deployed["status"], "SIMULATION_DEPLOYED")

        bad_cmds = ["configure terminal", "reload"]
        res_blocked = self.connector.deploy_remediation("R1", bad_cmds)
        self.assertFalse(res_blocked["success"])
        self.assertEqual(res_blocked["status"], "BLOCKED_BY_SAFETY_GATE")

    # ==================== 5. MALFORMED / EMPTY INPUT TESTS ====================

    def test_malformed_empty_input_handling(self):
        self.assertIsNone(self.checker.check(""))
        self.assertIsNone(self.checker.check(None))
        
        diag = self.engine.diagnose("UNKNOWN-999", "Random junk data with no pattern match")
        self.assertEqual(diag["status"], "ANOMALY_DETECTED")
        self.assertIn("is_safe", diag["diagnostic"])

if __name__ == "__main__":
    unittest.main()
