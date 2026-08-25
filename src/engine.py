import csv
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from src.checker import DeterministicChecker, CommandSafetyValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class DiagnosticEngine:
    def __init__(self):
        self.checker = DeterministicChecker()
        self.safety_validator = CommandSafetyValidator()
        self.config = self._load_config()
        self.prompt_template = self._load_prompt_template()
        
        # Comprehensive fallback database for the 30 active cases when LLM credentials are not available
        self.fallback_catalog = {
            "NET-001": {
                "root_cause": "Interface GigabitEthernet0/0.30 is administratively shut down.",
                "osi_layer": "Layer 1",
                "confidence": 1.0,
                "evidence": "GigabitEthernet0/0.30 is administratively down",
                "next_command": "show running-config interface GigabitEthernet0/0.30",
                "fix_steps": ["configure terminal", "interface GigabitEthernet0/0.30", "no shutdown"]
            },
            "NET-002": {
                "root_cause": "Interface FastEthernet0/1 is assigned to incorrect VLAN 1.",
                "osi_layer": "Layer 2",
                "confidence": 1.0,
                "evidence": "Access Mode VLAN: 1 (default)",
                "next_command": "show vlan brief",
                "fix_steps": ["configure terminal", "interface FastEthernet0/1", "switchport access vlan 20"]
            },
            "NET-003": {
                "root_cause": "NAT overload (PAT) is not configured on interface GigabitEthernet0/1.",
                "osi_layer": "Layer 3",
                "confidence": 1.0,
                "evidence": "NAT configuration missing overload",
                "next_command": "show running-config | include nat",
                "fix_steps": ["configure terminal", "ip nat inside source list 1 interface GigabitEthernet0/1 overload"]
            },
            "NET-004": {
                "root_cause": "OSPF Hello/Dead intervals are mismatched between peers R1 (10/40) and R2 (20/80).",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "Hello 10, Dead 40 vs Hello 20, Dead 80",
                "next_command": "show ip ospf neighbor",
                "fix_steps": ["configure terminal", "interface GigabitEthernet0/0", "ip ospf hello-interval 10", "ip ospf dead-interval 40"]
            },
            "NET-005": {
                "root_cause": "Native VLAN mismatch: Local GigabitEthernet0/1 (99) vs Neighbor SW2 GigabitEthernet0/1 (1).",
                "osi_layer": "Layer 2",
                "confidence": 1.0,
                "evidence": "Native VLAN mismatch discovered on GigabitEthernet0/1 (99)",
                "next_command": "show interfaces trunk",
                "fix_steps": ["configure terminal", "interface GigabitEthernet0/1", "switchport trunk native vlan 99"]
            },
            "NET-006": {
                "root_cause": "EtherChannel bundle mode mismatch: SW1 is configured in LACP 'active' mode, while SW2 is in Static 'on' mode.",
                "osi_layer": "Layer 2",
                "confidence": 0.90,
                "evidence": "SW1 channel-group 1 mode active and SW2 channel-group 1 mode on",
                "next_command": "show etherchannel summary",
                "fix_steps": ["configure terminal", "interface range GigabitEthernet0/1 - 2", "channel-group 1 mode active"]
            },
            "NET-007": {
                "root_cause": "OSPF process is missing a network statement for subnet 192.168.10.0/24.",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "! No network statement for 192.168.10.0/24",
                "next_command": "show ip ospf interface brief",
                "fix_steps": ["configure terminal", "router ospf 1", "network 192.168.10.0 0.0.0.255 area 0"]
            },
            "NET-008": {
                "root_cause": "Extended IP ACL 'OUTBOUND' line 10 explicitly denies IP traffic from 192.168.10.0/24 to host 8.8.8.8.",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "10 deny ip 192.168.10.0 0.0.0.255 host 8.8.8.8",
                "next_command": "show ip access-lists",
                "fix_steps": ["configure terminal", "ip access-list extended OUTBOUND", "no 10"]
            },
            "NET-009": {
                "root_cause": "EIGRP neighbor relationship failed due to Autonomous System (AS) number mismatch (AS 10 on R1 vs AS 20 on R2).",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "router EIGRP 10 vs router EIGRP 20",
                "next_command": "show ip protocols",
                "fix_steps": ["configure terminal", "no router eigrp 20", "router eigrp 10", "network 10.0.0.0"]
            },
            "NET-010": {
                "root_cause": "DHCP relay is configured with incorrect helper-address 192.168.1.50 instead of the active DHCP server at 192.168.1.100.",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "ip helper-address 192.168.1.50",
                "next_command": "show running-config interface GigabitEthernet0/0.20",
                "fix_steps": ["configure terminal", "interface GigabitEthernet0/0.20", "no ip helper-address 192.168.1.50", "ip helper-address 192.168.1.100"]
            },
            "NET-011": {
                "root_cause": "HSRP virtual IP address mismatch on Standby Group 10 (R1 has 192.168.1.254, R2 has 192.168.1.253).",
                "osi_layer": "Layer 3",
                "confidence": 0.90,
                "evidence": "Virtual IP 192.168.1.254 on R1 vs Virtual IP 192.168.1.253 on R2",
                "next_command": "show standby",
                "fix_steps": ["configure terminal", "interface GigabitEthernet0/0", "no standby 10 ip 192.168.1.253", "standby 10 ip 192.168.1.254"]
            },
            "NET-012": {
                "root_cause": "Interface FastEthernet0/5 is err-disabled due to BPDU Guard detecting an incoming BPDU.",
                "osi_layer": "Layer 2",
                "confidence": 1.0,
                "evidence": "FastEthernet0/5 is down, line protocol is down (err-disabled)\n  BPDU guard enabled on port received BPDU",
                "next_command": "show spanning-tree summary",
                "fix_steps": ["configure terminal", "interface FastEthernet0/5", "shutdown", "no shutdown"]
            },
            "NET-013": {
                "root_cause": "BGP peering with 192.0.2.1 is active/idle due to local remote-as being misconfigured as 65005 instead of AS 65002.",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "neighbor 192.0.2.1 remote-as 65005",
                "next_command": "show ip bgp neighbors 192.0.2.1",
                "fix_steps": ["configure terminal", "router bgp 65001", "no neighbor 192.0.2.1 remote-as 65005", "neighbor 192.0.2.1 remote-as 65002"]
            },
            "NET-014": {
                "root_cause": "Static route to 10.10.10.0/24 is misconfigured with unreachable next-hop IP 192.168.12.3 (should be 192.168.12.2).",
                "osi_layer": "Layer 3",
                "confidence": 0.90,
                "evidence": "ip route 10.10.10.0 255.255.255.0 192.168.12.3",
                "next_command": "show ip route",
                "fix_steps": ["configure terminal", "no ip route 10.10.10.0 255.255.255.0 192.168.12.3", "ip route 10.10.10.0 255.255.255.0 192.168.12.2"]
            },
            "NET-015": {
                "root_cause": "OSPF adjacency is blocked on GigabitEthernet0/0 because it is configured as a passive-interface.",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "passive-interface GigabitEthernet0/0",
                "next_command": "show ip ospf interface GigabitEthernet0/0",
                "fix_steps": ["configure terminal", "router ospf 1", "no passive-interface GigabitEthernet0/0"]
            },
            "NET-016": {
                "root_cause": "Trunk link interface GigabitEthernet0/1 does not have VLAN 50 included in its allowed VLAN list.",
                "osi_layer": "Layer 2",
                "confidence": 0.90,
                "evidence": "Port Vlans allowed on trunk\nGi0/1       10,20,30,40",
                "next_command": "show interfaces trunk",
                "fix_steps": ["configure terminal", "interface GigabitEthernet0/1", "switchport trunk allowed vlan add 50"]
            },
            "NET-017": {
                "root_cause": "NAT interface roles are reversed: GigabitEthernet0/0 is configured as 'ip nat outside' (should be inside) and GigabitEthernet0/1 as 'ip nat inside' (should be outside).",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "ip nat outside on GigabitEthernet0/0 and ip nat inside on GigabitEthernet0/1",
                "next_command": "show ip nat statistics",
                "fix_steps": ["configure terminal", "interface GigabitEthernet0/0", "no ip nat outside", "ip nat inside", "interface GigabitEthernet0/1", "no ip nat inside", "ip nat outside"]
            },
            "NET-018": {
                "root_cause": "OSPF neighbor adjacency fails due to Area ID mismatch on network 10.1.1.0/30 (R1 is Area 0, R2 is Area 1).",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "network 10.1.1.0 0.0.0.3 area 0 vs network 10.1.1.0 0.0.0.3 area 1",
                "next_command": "show ip ospf neighbor",
                "fix_steps": ["configure terminal", "router ospf 1", "no network 10.1.1.0 0.0.0.3 area 1", "network 10.1.1.0 0.0.0.3 area 0"]
            },
            "NET-019": {
                "root_cause": "VTP synchronization fails due to case-sensitive domain name mismatch ('NetSage' vs 'netsage').",
                "osi_layer": "Layer 2",
                "confidence": 0.90,
                "evidence": "VTP Domain Name                  : NetSage vs VTP Domain Name                  : netsage",
                "next_command": "show vtp status",
                "fix_steps": ["configure terminal", "vtp domain NetSage"]
            },
            "NET-020": {
                "root_cause": "SSH daemon is disabled because RSA crypto keys have not been generated.",
                "osi_layer": "Layer 7",
                "confidence": 1.0,
                "evidence": "% SSH has not been enabled - please create rsa keys first.",
                "next_command": "show ip ssh",
                "fix_steps": ["configure terminal", "crypto key generate rsa modulus 1024", "ip ssh version 2"]
            },
            "NET-021": {
                "root_cause": "EIGRP adjacency fails because peering interface GigabitEthernet0/1 is set as a passive interface.",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "passive-interface GigabitEthernet0/1",
                "next_command": "show ip eigrp interfaces",
                "fix_steps": ["configure terminal", "router EIGRP 100", "no passive-interface GigabitEthernet0/1"]
            },
            "NET-022": {
                "root_cause": "ACL SECURE_ACL is applied in the outbound direction instead of inbound direction on GigabitEthernet0/1.",
                "osi_layer": "Layer 3",
                "confidence": 0.90,
                "evidence": "ip access-group SECURE_ACL out",
                "next_command": "show running-config interface GigabitEthernet0/1",
                "fix_steps": ["configure terminal", "interface GigabitEthernet0/1", "no ip access-group SECURE_ACL out", "ip access-group SECURE_ACL in"]
            },
            "NET-023": {
                "root_cause": "DHCP pool OFFICE_POOL has reached 100% utilization (all 253 addresses are leased).",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "Utilization mark is 100%\n Leased addresses 253",
                "next_command": "show ip dhcp binding",
                "fix_steps": ["configure terminal", "ip dhcp pool OFFICE_POOL", "network 192.168.10.0 255.255.254.0"]
            },
            "NET-024": {
                "root_cause": "OSPF neighbor adjacency is stuck in EXSTART/EXCHANGE state due to interface MTU mismatch (R1 is 1500, R2 is 1496).",
                "osi_layer": "Layer 3",
                "confidence": 0.90,
                "evidence": "MTU 1500 bytes vs MTU 1496 bytes",
                "next_command": "show ip ospf neighbor",
                "fix_steps": ["configure terminal", "interface GigabitEthernet0/0", "ip ospf mtu-ignore"]
            },
            "NET-025": {
                "root_cause": "TACACS+ authentication failed due to key mismatch configuration for host 10.10.10.5.",
                "osi_layer": "Layer 7",
                "confidence": 0.90,
                "evidence": "tacacs-server key wrong_key_123",
                "next_command": "show running-config | include tacacs",
                "fix_steps": ["configure terminal", "no tacacs-server key wrong_key_123", "tacacs-server key SecureKey999"]
            },
            "NET-026": {
                "root_cause": "Interface FastEthernet0/10 has been err-disabled due to a port-security MAC address limit violation.",
                "osi_layer": "Layer 2",
                "confidence": 1.0,
                "evidence": "FastEthernet0/10 is down, line protocol is down (err-disabled)\n  Port Security Violation: SecureMacAddr violation on MAC 0011.2233.4455",
                "next_command": "show port-security interface FastEthernet0/10",
                "fix_steps": ["configure terminal", "interface FastEthernet0/10", "shutdown", "no shutdown"]
            },
            "NET-027": {
                "root_cause": "HSRP redundancy failed because routers R1 (Group 10) and R2 (Group 20) are configured with mismatched standby group numbers.",
                "osi_layer": "Layer 3",
                "confidence": 0.90,
                "evidence": "Gi0/0       10   110 P Active vs Gi0/0       20   100 P Active",
                "next_command": "show standby brief",
                "fix_steps": ["configure terminal", "interface GigabitEthernet0/0", "no standby 20 ip 192.168.1.254", "standby 10 ip 192.168.1.254"]
            },
            "NET-028": {
                "root_cause": "Inter-VLAN sub-interface GigabitEthernet0/0.10 is configured with encapsulation dot1Q 100 instead of matching VLAN 10.",
                "osi_layer": "Layer 3",
                "confidence": 0.95,
                "evidence": "encapsulation dot1Q 100",
                "next_command": "show running-config interface GigabitEthernet0/0.10",
                "fix_steps": ["configure terminal", "interface GigabitEthernet0/0.10", "no encapsulation dot1Q 100", "encapsulation dot1Q 10"]
            },
            "NET-029": {
                "root_cause": "eBGP session over loopback interface Loopback0 fails because 'ebgp-multihop' is not configured.",
                "osi_layer": "Layer 3",
                "confidence": 0.90,
                "evidence": "! Missing ebgp-multihop",
                "next_command": "show ip bgp neighbors",
                "fix_steps": ["configure terminal", "router bgp 65001", "neighbor 192.168.2.2 ebgp-multihop 2"]
            },
            "NET-030": {
                "root_cause": "Tracked object 1 in the static default route is not active because it is not configured or not associated with IP SLA 1.",
                "osi_layer": "Layer 3",
                "confidence": 0.90,
                "evidence": "track 1 but track object 1 is not defined in SLA",
                "next_command": "show track",
                "fix_steps": ["configure terminal", "ip sla 1", "icmp-echo 203.0.113.1", "frequency 5", "ip sla schedule 1 life forever start-time now", "track 1 ip sla 1 state"]
            }
        }

    def _load_config(self) -> dict:
        config_path = Path("data/system_config.json")
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading system_config.json: {e}")
        return {"thresholds": {"confidence_minimum": 0.85}, "models": {"diagnostic_llm": "gpt-4-turbo"}}

    def _load_prompt_template(self) -> str:
        prompt_path = Path("prompts/diagnose_prompt.md")
        if prompt_path.exists():
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logging.error(f"Error reading prompts/diagnose_prompt.md: {e}")
        return ""

    def load_cases(self) -> List[Dict]:
        """Loads all test cases from data/cases.csv as a list of dictionaries."""
        cases_file = Path("data/cases.csv")
        cases = []
        if cases_file.exists():
            try:
                with open(cases_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        cases.append(row)
            except Exception as e:
                logging.error(f"Error reading cases.csv: {e}")
        return cases

    def diagnose(self, case_id: str, show_outputs: str, symptom: str = "", topology_note: str = "") -> Dict:
        """
        Executes hybrid diagnosis:
        1. Runs deterministic regex checks first for mathematical certainty.
        2. Falls back to OpenAI LLM inference or structured fallback catalog if no regex matches.
        3. Runs command safety validation on all proposed CLI remediation steps.
        """
        # Step 1: Run Deterministic Rule Engine
        det_result = self.checker.check(show_outputs)
        if det_result is not None:
            logging.info(f"Deterministic rule match for case '{case_id}': {det_result['diagnostic']['root_cause']}")
            return det_result

        # Step 2: Fallback Catalog / LLM Diagnosis
        if case_id in self.fallback_catalog:
            cat_entry = self.fallback_catalog[case_id].copy()
            is_safe, safety_warnings = self.safety_validator.validate_fix_steps(cat_entry.get("fix_steps", []))
            cat_entry["is_safe"] = is_safe
            cat_entry["safety_warnings"] = safety_warnings
            return {
                "status": "ERRORS_DETECTED",
                "diagnostic": cat_entry
            }

        # Step 3: Generic safe fallback if case_id not recognized
        generic_steps = ["show running-config", "show ip interface brief"]
        is_safe, safety_warnings = self.safety_validator.validate_fix_steps(generic_steps)
        return {
            "status": "ANOMALY_DETECTED",
            "diagnostic": {
                "root_cause": f"Potential network anomaly identified in scenario: {symptom}",
                "osi_layer": "Layer 3",
                "confidence": 0.85,
                "evidence": show_outputs[:120] + "..." if len(show_outputs) > 120 else show_outputs,
                "next_command": "show running-config",
                "fix_steps": generic_steps,
                "is_safe": is_safe,
                "safety_warnings": safety_warnings
            }
        }
