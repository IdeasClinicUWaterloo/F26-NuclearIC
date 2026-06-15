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
        to physically reach their mandatory operational checkpoints.
        
        Returns:
            dict: {
                "operational_viable": bool,
                "log": list of logging strings
            }
        """
        all_roles = self.blueprint.operational_requirements.keys()
        system_passed = True
        guardrail_log = []

        guardrail_log.append("==================================================")
        guardrail_log.append("       STARTING OPERATIONAL GUARDRAIL CHECKS      ")
        guardrail_log.append("==================================================")
        guardrail_log.append(f"[*] Facility Entry Point Designated As: '{entry_point}'")

        for role in all_roles:
            required_rooms = self.blueprint.get_role_requirements(role)
            guardrail_log.append(f"\n[*] Evaluating Mission Capability for Role: '{role}'")
            
            for room in required_rooms:
                # Execute the pathfinding engine to simulate the person walking to work
                result = self.engine.verify_path(entry_point, room, role)
                
                if result["path_found"]:
                    guardrail_log.append(f"    [+] PASS: Clear route discovered to '{room}'.")
                else:
                    guardrail_log.append(f"    [X] CRITICAL BLOCK: Role is physically unable to access '{room}'!")
                    system_passed = False
                    
        guardrail_log.append("\n==================================================")
        if system_passed:
            guardrail_log.append(" AUDIT RESULT: OPERATIONAL COMPLIANCE ARCHIVED     ")
            guardrail_log.append(" -> Core staffing can execute required duties.     ")
        else:
            guardrail_log.append(" AUDIT RESULT: OPERATIONAL SYSTEM FAULT            ")
            guardrail_log.append(" -> Critical roles are locked out of required zones.")
        guardrail_log.append("==================================================")

        return {
            "operational_viable": system_passed,
            "log": guardrail_log
        }


# --- Local Orchestration & Test Run ---
if __name__ == "__main__":
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        blueprint_path = os.path.join(project_root, "data", "facility_blueprint.json")
        policy_path = os.path.join(project_root, "data", "policy_config.json")
        
        # Initialize full infrastructure chain
        loader = BlueprintLoader(blueprint_path)
        pm = PolicyManager(policy_path, loader)
        engine = GraphEngine(loader, pm)
        
        # Initialize Guardrails
        guardrails = OperationalGuardrails(loader, pm, engine)
        
        # Run the full validation check
        report = guardrails.verify_facility_operations()
        
        # Print results to console
        for line in report["log"]:
            print(line)

    except Exception as e:
        print(f"Guardrail System Critical Failure: {e}")