import os
from blueprint_loader import BlueprintLoader
from policy_manager import PolicyManager
from graph_engine import GraphEngine

class OperationalGuardrails:
    def __init__(self, blueprint_loader: BlueprintLoader, policy_manager: PolicyManager, graph_engine: GraphEngine):
        self.blueprint = blueprint_loader
        self.policy = policy_manager
        self.engine = graph_engine

    def verify_facility_operations(self, entry_point="perimeter_gate"):
        """
        Validates that the current policy allows all critical personnel roles 
        to reach checkpoints, calculating a cumulative Facility Efficiency Score.
        """
        all_roles = self.blueprint.operational_requirements.keys()
        system_passed = True
        total_facility_delay = 0
        guardrail_log = []

        guardrail_log.append("==================================================")
        guardrail_log.append("       STARTING OPERATIONAL GUARDRAIL CHECKS      ")
        guardrail_log.append("==================================================")
        guardrail_log.append(f"[*] Facility Entry Point Designated As: '{entry_point}'")

        # Inject standard supervision and dual-presence context to evaluate standard operational capability
        for role in all_roles:
            # PRIORITY 1.2: Validate role exists in blueprint
            if role not in self.blueprint.operational_requirements:
                guardrail_log.append(f"\n[!] Configuration Error: Role '{role}' not in blueprint operational_requirements.")
                system_passed = False
                continue
            
            context = {
                "system_state": "Normal", 
                "time_of_day": 12, 
                "active_escorts": ["security_officer"],
                "present_roles": [role, "security_officer"] # Enforces the Two-Person Rule buddy presence
            }

            required_rooms = self.blueprint.get_role_requirements(role)
            guardrail_log.append(f"\n[*] Evaluating Mission Capability for Role: '{role}'")
            
            for room in required_rooms:
                result = self.engine.verify_path(entry_point, room, role, context)
                
                if result["path_found"]:
                    path_time = result["total_time"]
                    total_facility_delay += path_time
                    guardrail_log.append(f"    [+] PASS: Route confirmed to '{room}' ({path_time} mins elapsed).")
                else:
                    guardrail_log.append(f"    [X] CRITICAL BLOCK: Role is physically unable to access '{room}'!")
                    system_passed = False
                    
        guardrail_log.append("\n==================================================")
        guardrail_log.append("             OPERATIONAL EFFICIENCY REPORT        ")
        guardrail_log.append("==================================================")
        guardrail_log.append(f"[->] Cumulative Facility Mission Delay: {total_facility_delay} operational minutes.")
        
        # Calculate a baseline grade: Perfect uninhibited routing takes roughly 25 minutes total across all profiles
        if total_facility_delay == 0:
            efficiency_rating = 0
        else:
            efficiency_rating = max(10, min(100, int((25 / total_facility_delay) * 100)))
        guardrail_log.append(f"[->] Total Operational Feasibility Rating: {efficiency_rating}/100")
        
        if system_passed:
            guardrail_log.append("\nAUDIT RESULT: OPERATIONAL COMPLIANCE ARCHIVED")
        else:
            guardrail_log.append("\nAUDIT RESULT: OPERATIONAL SYSTEM FAULT (DEADLOCK)")
        guardrail_log.append("==================================================")

        return {
            "operational_viable": system_passed,
            "total_delay": total_facility_delay,
            "efficiency_rating": efficiency_rating,
            "log": guardrail_log
        }

if __name__ == "__main__":
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        loader = BlueprintLoader(os.path.join(project_root, "data", "facility_blueprint.json"))
        pm = PolicyManager(os.path.join(project_root, "data", "policy_config.json"), loader)
        engine = GraphEngine(loader, pm)
        
        guardrails = OperationalGuardrails(loader, pm, engine)
        report = guardrails.verify_facility_operations()
        
        for line in report["log"]:
            print(line)

    except Exception as e:
        print(f"Guardrail System Critical Failure: {e}")