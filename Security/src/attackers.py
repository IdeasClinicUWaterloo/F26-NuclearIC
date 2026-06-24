import os
from blueprint_loader import BlueprintLoader
from policy_manager import PolicyManager
from graph_engine import GraphEngine

class SocialEngineer:
    def __init__(self, blueprint_loader: BlueprintLoader, policy_manager: PolicyManager, graph_engine: GraphEngine):
        self.blueprint = blueprint_loader
        self.policy = policy_manager
        self.engine = graph_engine

    def _get_zone_gradient(self, zone_name):
        """Converts a zone identifier string into a numeric gradient level (e.g., 'Zone_3' -> 3)."""
        try:
            return int(zone_name.split("_")[-1])
        except (ValueError, IndexError):
            return 0

    def execute_attack(self, target_role, start_room="perimeter_gate", context=None):
        """
        Simulates a social engineering infiltration attempt by analyzing the 
        target role's trajectory for topographical security fractures.
        """
        # PRIORITY 1.2: Validate target_role input
        if target_role not in self.blueprint.operational_requirements:
            simulation_log = []
            simulation_log.append("==================================================")
            simulation_log.append("      ADVERSARY SIMULATION: THE SOCIAL ENGINEER   ")
            simulation_log.append("==================================================")
            simulation_log.append(f"[!] Invalid target role '{target_role}'.")
            simulation_log.append(f"[!] Valid roles: {list(self.blueprint.operational_requirements.keys())}")
            return {"attack_successful": False, "log": simulation_log}
        
        if context is None:
            context = {"system_state": "Normal", "time_of_day": 12, "active_escorts": []}

        simulation_log = []
        simulation_log.append("==================================================")
        simulation_log.append("      ADVERSARY SIMULATION: THE SOCIAL ENGINEER   ")
        simulation_log.append("==================================================")
        simulation_log.append("[*] Strategy: Target personnel tracking & tailgating.")
        simulation_log.append(f"[*] Target Profile: Tracking '{target_role}' normal operations route.")

        required_rooms = self.blueprint.get_role_requirements(target_role)
        if not required_rooms:
            simulation_log.append(f"[+] Attack Deflected: Role '{target_role}' has no mandatory operational rooms.")
            return {"attack_successful": False, "log": simulation_log}

        for target_room in required_rooms:
            simulation_log.append(f"[*] Analyzing trajectory to destination: '{target_room}'")
            route_result = self.engine.verify_path(start_room, target_room, target_role, context)
            
            if not route_result["path_found"]:
                simulation_log.append(f"    [-] Target path unavailable. Personnel blocked by policy; tracking lost.")
                continue

            path = route_result["path"]
            zone_sequence = [self.policy.room_to_zone.get(room) for room in path]
            gradient_sequence = [self._get_zone_gradient(z) for z in zone_sequence]

            for i in range(len(gradient_sequence)):
                for j in range(i + 2, len(gradient_sequence)):
                    for k in range(i + 1, j):
                        if gradient_sequence[k] < gradient_sequence[i] and gradient_sequence[k] < gradient_sequence[j]:
                            vulnerable_room = path[k]
                            simulation_log.append(f"\n[!] CRITICAL VULNERABILITY EXPLOITED!")
                            simulation_log.append(f"    -> Perimeter Fracture Detected in routing sequence.")
                            simulation_log.append(f"    -> Path Gradient Trend: {gradient_sequence}")
                            simulation_log.append(
                                f"    -> Breach Vector: Target moves from high security ({zone_sequence[i]}) "
                                f"down into low security ({zone_sequence[k]}: '{vulnerable_room}') "
                                f"before climbing back to high security ({zone_sequence[j]})."
                            )
                            simulation_log.append(f"    -> Action: Attacker piggybacked through the transition gate.")
                            simulation_log.append("\n==================================================")
                            simulation_log.append(" SIMULATION RESULT: [ SUCCESSFUL INFILTRATION ]   ")
                            simulation_log.append("==================================================")
                            return {"attack_successful": True, "log": simulation_log}

            simulation_log.append(f"    [+] Trajectory secure. Monotonic zone gradient verified along this branch.")

        simulation_log.append("\n==================================================")
        simulation_log.append(" SIMULATION RESULT: [ ATTACK REPELLED SUCCESSFUL ]")
        simulation_log.append("==================================================")
        return {"attack_successful": False, "log": simulation_log}


class Impersonator:
    def __init__(self, blueprint_loader: BlueprintLoader, policy_manager: PolicyManager, graph_engine: GraphEngine):
        self.blueprint = blueprint_loader
        self.policy = policy_manager
        self.engine = graph_engine

    def execute_attack(self, start_room="perimeter_gate", target_rooms=None, context=None):
        """
        Simulates an impersonation attempt. Weaponizes guard distraction if 
        the facility policy over-allocates security personnel to escort duties.
        """
        if target_rooms is None:
            target_rooms = ["main_control_room", "reactor_containment"]
            
        escort_count = self.policy.get_escort_requirement_count("normal")
        guards_distracted = escort_count >= 2  # Threat Trigger Boundary

        if context is None:
            context = {
                "system_state": "Normal", 
                "time_of_day": 12, 
                "active_escorts": [],
                "guards_distracted": guards_distracted,
                "present_roles": ["contractor"] # Attacker is executing a solo breach
            }

        simulation_log = []
        simulation_log.append("==================================================")
        simulation_log.append("        ADVERSARY SIMULATION: THE IMPERSONATOR    ")
        simulation_log.append("==================================================")
        simulation_log.append("[*] Strategy: Posing as an unescorted contractor via cloned badges.")
        simulation_log.append(f"[*] Guard Staffing Context: Total active escort rules = {escort_count}")
        
        if guards_distracted:
            simulation_log.append("[!] VULNERABILITY DETECTED: Personnel over-allocation discovered!")
            simulation_log.append("    -> Attacker triggers a routine escort request distraction in a lower zone.")

        for room in target_rooms:
            simulation_log.append(f"[*] Attempting contractor entry path to vital node: '{room}'")
            result = self.engine.verify_path(start_room, room, "contractor", context)
            
            if result["path_found"]:
                simulation_log.append(f"\n[!] CRITICAL VULNERABILITY EXPLOITED!")
                if guards_distracted:
                    simulation_log.append(f"    -> Tactical Exploitation: Security Officers were tied up with routine duties.")
                    simulation_log.append(f"    -> Breach Vector: Bypassed checkpoint at '{room}' during resource saturation.")
                else:
                    simulation_log.append(f"    -> Policy Failure: Missing escort verification rule entirely.")
                simulation_log.append(f"    -> Compromised Vital Asset: '{room}' successfully occupied.")
                simulation_log.append("\n==================================================")
                simulation_log.append(" SIMULATION RESULT: [ SUCCESSFUL INFILTRATION ]   ")
                simulation_log.append("==================================================")
                return {"attack_successful": True, "log": simulation_log}
            else:
                simulation_log.append(f"    [+] Defended: Contractor trajectory safely blocked at perimeter.")

        simulation_log.append("\n==================================================")
        simulation_log.append(" SIMULATION RESULT: [ ATTACK REPELLED SUCCESSFUL ]")
        simulation_log.append(" -> Policy utilizes an optimized, lean escort strategy. Security pool is alert.")
        simulation_log.append("==================================================")
        return {"attack_successful": False, "log": simulation_log}


class Insider:
    def __init__(self, blueprint_loader: BlueprintLoader, policy_manager: PolicyManager, graph_engine: GraphEngine):
        self.blueprint = blueprint_loader
        self.policy = policy_manager
        self.engine = graph_engine

    def execute_attack(self, rogue_role="maintenance_technician", unauthorized_targets=None, context=None):
        """
        Simulates a rogue internal actor attempting to escalate privileges or
        traverse laterally into sensitive rooms outside their authorized scope.
        """
        # PRIORITY 1.2: Validate rogue_role input
        if rogue_role not in self.blueprint.operational_requirements:
            simulation_log = []
            simulation_log.append("==================================================")
            simulation_log.append("          ADVERSARY SIMULATION: THE INSIDER       ")
            simulation_log.append("==================================================")
            simulation_log.append(f"[!] Invalid rogue role '{rogue_role}'.")
            simulation_log.append(f"[!] Valid roles: {list(self.blueprint.operational_requirements.keys())}")
            return {"attack_successful": False, "log": simulation_log}
        
        if unauthorized_targets is None:
            unauthorized_targets = ["main_control_room"]
        if context is None:
            context = {
                "system_state": "Normal", 
                "time_of_day": 12, 
                "active_escorts": [],
                "present_roles": [rogue_role] # Rogue employee moving unaccompanied
            }

        simulation_log = []
        simulation_log.append("==================================================")
        simulation_log.append("          ADVERSARY SIMULATION: THE INSIDER       ")
        simulation_log.append("==================================================")
        simulation_log.append(f"[*] Strategy: Rogue internal employee ('{rogue_role}') abusing trusted low-level access.")
        simulation_log.append("[*] Threat Vector: Lateral movement into vital sectors outside mission description.")

        mandatory_rooms = self.blueprint.get_role_requirements(rogue_role)
        
        for target_room in unauthorized_targets:
            if target_room in mandatory_rooms:
                simulation_log.append(f"[!] Simulation Bypass: '{target_room}' is within legitimate scope for '{rogue_role}'.")
                continue

            simulation_log.append(f"[*] Rogue '{rogue_role}' executing unauthorized lateral sweep into: '{target_room}'")
            result = self.engine.verify_path("perimeter_gate", target_room, rogue_role, context)

            if result["path_found"]:
                simulation_log.append(f"\n[!] CRITICAL VULNERABILITY EXPLOITED!")
                simulation_log.append(f"    -> Least-Privilege Architecture Failure: Internal role escalated past boundaries.")
                simulation_log.append(f"    -> Infiltrated Area: Vital node '{target_room}' compromised.")
                simulation_log.append(f"    -> Action: Insider successfully occupied unauthorized high-security workspace.")
                simulation_log.append("\n==================================================")
                simulation_log.append(" SIMULATION RESULT: [ SUCCESSFUL INFILTRATION ]   ")
                simulation_log.append("==================================================")
                return {"attack_successful": True, "log": simulation_log}
            else:
                simulation_log.append(f"    [+] Defended: Internal lateral traversal to '{target_room}' successfully contained.")

        simulation_log.append("\n==================================================")
        simulation_log.append(" SIMULATION RESULT: [ ATTACK REPELLED SUCCESSFUL ]")
        simulation_log.append("==================================================")
        return {"attack_successful": False, "log": simulation_log}


class EmergencyExploiter:
    def __init__(self, blueprint_loader: BlueprintLoader, policy_manager: PolicyManager, graph_engine: GraphEngine):
        self.blueprint = blueprint_loader
        self.policy = policy_manager
        self.engine = graph_engine

    def execute_attack(self, target_roles=None, start_room="perimeter_gate", target_rooms=None):
        """
        Simulates an emergency exploit attempt. Verifies if crisis routing rules 
        properly streamline essential staff fast-paths or contain vulnerabilities.
        """
        if target_roles is None:
            # Emergency responder simulation profile
            target_roles = ["security_officer"]
        
        # PRIORITY 1.2: Validate all target_roles input
        for role in target_roles:
            if role not in self.blueprint.operational_requirements:
                simulation_log = []
                simulation_log.append("==================================================")
                simulation_log.append("      ADVERSARY SIMULATION: EMERGENCY EXPLOITER   ")
                simulation_log.append("==================================================")
                simulation_log.append(f"[!] Invalid target role '{role}'.")
                simulation_log.append(f"[!] Valid roles: {list(self.blueprint.operational_requirements.keys())}")
                return {"attack_successful": False, "log": simulation_log}
        
        if target_rooms is None:
            target_rooms = ["main_control_room"]
            
        context = {
            "system_state": "Emergency", 
            "time_of_day": 12, 
            "active_escorts": [],
            "present_roles": ["security_officer", "reactor_operator"] # Team deployment
        }

        simulation_log = []
        simulation_log.append("==================================================")
        simulation_log.append("      ADVERSARY SIMULATION: EMERGENCY EXPLOITER   ")
        simulation_log.append("==================================================")
        simulation_log.append("[*] Strategy: Monitor essential staff path response times during crisis alarms.")
        simulation_log.append("[*] Threat Vector: Probing for sequential routing blocks or excessive fast-path delays.")

        for role in target_roles:
            for room in target_rooms:
                simulation_log.append(f"[*] Simulating critical deployment path: '{role}' moving to '{room}'...")
                result = self.engine.verify_path(start_room, room, role, context)
                
                if not result["path_found"]:
                    simulation_log.append(f"\n[!] CRITICAL FACILITY FAILURE DETECTED!")
                    simulation_log.append(f"    -> Operational Safety Failure: Critical staff completely blocked during emergency!")
                    simulation_log.append(f"    -> Blocked Target: Access to vital node '{room}' failed.")
                    simulation_log.append("\n==================================================")
                    simulation_log.append(" SIMULATION RESULT: [ SYSTEMIC DEADLOCK DETECTED ] ")
                    simulation_log.append("==================================================")
                    return {"attack_successful": True, "log": simulation_log}
                
                # Check response time threshold
                response_time = result["total_time"]
                simulation_log.append(f"    [+] Trajectory verified. Emergency response completed in {response_time} minutes.")
                
                if response_time > 20:
                    simulation_log.append(f"\n[!] CRITICAL VULNERABILITY EXPLOITED!")
                    simulation_log.append(f"    -> Emergency Response Time Threshold Exceeded: Action delayed by {response_time} mins.")
                    simulation_log.append(f"    -> Cause: Author enforced rigid sequential zone dependencies or escorts during crisis states.")
                    simulation_log.append(f"    -> Action: Saboteur capitalized on delayed response times to execute actions unverified.")
                    simulation_log.append("\n==================================================")
                    simulation_log.append(" SIMULATION RESULT: [ SUCCESSFUL SABOTAGE BREACH ] ")
                    simulation_log.append("==================================================")
                    return {"attack_successful": True, "log": simulation_log}

        simulation_log.append("\n==================================================")
        simulation_log.append(" SIMULATION RESULT: [ ATTACK REPELLED SUCCESSFUL ]")
        simulation_log.append(" -> Fast-path logic successfully streamlined crisis transit times. Sector secure.")
        simulation_log.append("==================================================")
        return {"attack_successful": False, "log": simulation_log}


# --- Comprehensive Full-Suite Adversary Testing Blueprint ---
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    loader = BlueprintLoader(os.path.join(project_root, "data", "facility_blueprint.json"))
    pm_baseline = PolicyManager(os.path.join(project_root, "data", "policy_config.json"), loader)
    engine_baseline = GraphEngine(loader, pm_baseline)

    print(">>> 1. EVALUATING SAFE BASELINE SECURITY POLICY MATRIX <<<\n")
    exploiter_secure = EmergencyExploiter(loader, pm_baseline, engine_baseline)
    report_secure = exploiter_secure.execute_attack()
    for line in report_secure["log"]: print(line)

    print("\n\n" + "="*50 + "\n\n")

    print(">>> 2. EVALUATING VULNERABLE EMERGENCY LOCKDOWN POLICY <<<\n")
    pm_leaky = PolicyManager(os.path.join(project_root, "data", "policy_config.json"), loader)
    
    # Create a complete corridor vulnerability by opening up the entire transition path during a crisis
    open_crisis_rule = {"access": "Permitted", "requires_escort": False, "time_window": [0, 23]}
    
    pm_leaky.zone_policies["Zone_2"]["emergency"]["maintenance_technician"] = open_crisis_rule
    pm_leaky.zone_policies["Zone_3"]["emergency"]["maintenance_technician"] = open_crisis_rule
    pm_leaky.zone_policies["Zone_4"]["emergency"]["maintenance_technician"] = open_crisis_rule
    pm_leaky.zone_policies["Zone_5"]["emergency"]["maintenance_technician"] = open_crisis_rule
    
    engine_leaky = GraphEngine(loader, pm_leaky)
    exploiter_leaky = EmergencyExploiter(loader, pm_leaky, engine_leaky)
    report_leaky = exploiter_leaky.execute_attack()
    for line in report_leaky["log"]: print(line)