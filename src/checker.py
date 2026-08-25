import re
from typing import Dict, List, Optional, Tuple

class CommandSafetyValidator:
    """
    Validates Cisco IOS CLI remediation commands against a strict security blacklist
    to prevent staging or executing destructive commands that could cause network downtime,
    data loss, or configuration wipes.
    """
    DESTRUCTIVE_PATTERNS = [
        r"\breload\b",
        r"\bwrite\s+erase\b",
        r"\berase\s+startup-config\b",
        r"\bformat\s+\S+\b",
        r"\bdelete\s+(/recursive\s+)?(flash|nvram|disk\d*):",
        r"\brmdir\s+\S+",
        r"\bboot\s+system\b",
        r"\bno\s+aaa\s+new-model\b",
        r"\bno\s+service\s+password-encryption\b",
        r"\bclear\s+ip\s+bgp\s+\*\b",
        r"\bdefault\s+interface\s+\S+\b",
        r"\bfactory-reset\b"
    ]

    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.DESTRUCTIVE_PATTERNS]

    def validate_command(self, cmd: str) -> Tuple[bool, Optional[str]]:
        """
        Validates a single CLI command.
        Returns (is_safe: bool, warning_message: Optional[str]).
        """
        clean_cmd = cmd.strip()
        if not clean_cmd or clean_cmd.startswith("!"):
            return True, None

        for pattern in self.compiled_patterns:
            if pattern.search(clean_cmd):
                return False, f"CRITICAL SECURITY ALERT: Destructive command detected matching pattern '{pattern.pattern}'. Command blocked: '{clean_cmd}'."

        return True, None

    def validate_fix_steps(self, fix_steps: List[str]) -> Tuple[bool, List[str]]:
        """
        Validates a list of CLI remediation steps.
        Returns (is_all_safe: bool, list_of_warnings: List[str]).
        """
        warnings = []
        is_all_safe = True

        for step in fix_steps:
            safe, warning = self.validate_command(step)
            if not safe:
                is_all_safe = False
                warnings.append(warning)

        return is_all_safe, warnings


class DeterministicChecker:
    def __init__(self):
        self.safety_validator = CommandSafetyValidator()
        
        # Dictionary of rules. Key is error name, Value is a tuple of (Regex pattern, OSI Layer, Remediation template, fix_steps list)
        self.rules = {
            "ADMIN_DOWN": (
                r"(?P<interface>[A-Za-z0-9/.]+)\s+is administratively down",
                "Layer 1",
                "Interface {interface} is administratively shut down.",
                ["configure terminal", "interface {interface}", "no shutdown"]
            ),
            "MISSING_OVERLOAD": (
                r"ip nat inside source list \d+ interface (?P<interface>\S+)[\s\S]*?NAT configuration missing overload",
                "Layer 3",
                "NAT overload (PAT) is not configured on interface {interface}.",
                ["configure terminal", "ip nat inside source list 1 interface {interface} overload"]
            ),
            "MISMATCHED_VLAN": (
                r"(?P<interface>[A-Za-z0-9/.]+)\s+is up[\s\S]*?Access Mode VLAN: (?P<vlan>\d+)",
                "Layer 2",
                "Interface {interface} is assigned to incorrect VLAN {vlan}.",
                ["configure terminal", "interface {interface}", "switchport access vlan <correct_vlan>"]
            ),
            "BPDU_GUARD": (
                r"(?P<interface>[A-Za-z0-9/.]+)\s+is down,\s+line protocol is down\s+\(err-disabled\)[\s\S]*?BPDU guard",
                "Layer 2",
                "Interface {interface} is err-disabled due to BPDU Guard.",
                ["configure terminal", "interface {interface}", "shutdown", "no shutdown"]
            ),
            "PORT_SECURITY": (
                r"(?P<interface>[A-Za-z0-9/.]+)\s+is down,\s+line protocol is down\s+\(err-disabled\)[\s\S]*?Port Security Violation:[\s\S]*?MAC\s+(?P<mac>[a-f0-9.]+)",
                "Layer 2",
                "Interface {interface} is err-disabled due to a port-security violation by MAC {mac}.",
                ["configure terminal", "interface {interface}", "shutdown", "no shutdown"]
            ),
            "NATIVE_MISMATCH": (
                r"%CDP-4-NATIVE_VLAN_MISMATCH:\s*Native\s+VLAN\s+mismatch\s+discovered\s+on\s+(?P<interface>[A-Za-z0-9/.]+)\s*\((?P<native_vlan>\d+)\),?\s+with\s+(?P<neighbor>\S+)\s+(?P<neighbor_interface>[A-Za-z0-9/.]+)\s*\((?P<neighbor_vlan>\d+)\)",
                "Layer 2",
                "Native VLAN mismatch: Local {interface} ({native_vlan}) vs Neighbor {neighbor} {neighbor_interface} ({neighbor_vlan}).",
                ["configure terminal", "interface {interface}", "switchport trunk native vlan {neighbor_vlan}"]
            ),
            "SSH_DISABLED": (
                r"% SSH has not been enabled - please create rsa keys first.",
                "Layer 7",
                "SSH is disabled because the RSA key pair has not been generated.",
                ["configure terminal", "crypto key generate rsa"]
            )
        }

    def check(self, show_outputs: str) -> Optional[Dict]:
        """
        Runs deterministic checks on the provided show_outputs.
        Returns a diagnostic dictionary if an error is detected, else None.
        """
        if not show_outputs or not isinstance(show_outputs, str):
            return None

        for rule_name, (pattern, osi_layer, description_template, fix_steps_template) in self.rules.items():
            match = re.search(pattern, show_outputs)
            if match:
                evidence = match.group(0)
                
                # Format description if groups are present
                kwargs = match.groupdict()
                root_cause = description_template.format(**kwargs) if kwargs else description_template
                
                fix_steps = [step.format(**kwargs) if kwargs else step for step in fix_steps_template]
                is_safe, safety_warnings = self.safety_validator.validate_fix_steps(fix_steps)

                return {
                    "status": "ERRORS_DETECTED",
                    "diagnostic": {
                        "rule_id": rule_name,
                        "root_cause": root_cause,
                        "osi_layer": osi_layer,
                        "confidence": 1.0,  # Deterministic means 100% confidence
                        "evidence": evidence,
                        "next_command": "show running-config",
                        "fix_steps": fix_steps,
                        "is_safe": is_safe,
                        "safety_warnings": safety_warnings
                    }
                }
        
        return None
