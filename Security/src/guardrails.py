import os
from blueprint_loader import BlueprintLoader
from policy_manager import PolicyManager
from graph_engine import GraphEngine
from context_validator import ExecutionContext
from simulation_config import SimulationConstants as CONFIG

class OperationalGuardrails:
    def __init__(self, blueprint_loader: BlueprintLoader, policy_manager: PolicyManager, graph_engine: GraphEngine):
        self.blueprint = blueprint_loader
        self.policy = policy_manager
        self.engine = graph_engine

    def verify_facility_operations(self, entry_point="perimeter_gate"):
        """
        Validates that the current policy allows all critical personnel roles 
        to reach checkpoints, calculating a cumulative Facility Efficiency Score.
        Includes comprehensive error handling for robustness.
        """
        guardrail_log = []
        system_passed = True
        total_facility_delay = 0
        
        guardrail_log.append("==================================================")
        guardrail_log.append("       STARTING OPERATIONAL GUARDRAIL CHECKS      ")
        guardrail_log.append("==================================================")
        guardrail_log.append(f"[*] Facility Entry Point: '{entry_point}'")
        
        try:
            # Validate entry point exists
            if entry_point not in self.blueprint.get_all_rooms():
                guardrail_log.append(f"[!] CONFIGURATION ERROR: Entry point '{entry_point}' not in facility blueprint.")
                return {
                    "operational_viable": False,
                    "total_delay": 0,
                    "efficiency_rating": 0,
                    "log": guardrail_log
                }
            
            all_roles = list(self.blueprint.operational_requirements.keys())
            
            for role in all_roles:
                try:
                    # Validate role
                    if role not in self.blueprint.operational_requirements:
                        guardrail_log.append(f"[!] CONFIGURATION ERROR: Role '{role}' not in blueprint operational_requirements.")
                        system_passed = False
                        continue
                    
                    required_rooms = self.blueprint.get_role_requirements(role)
                    
                    if not required_rooms:
                        guardrail_log.append(f"[*] Role '{role}': No mandatory operational rooms defined.")
                        continue
                    
                    guardrail_log.append(f"\n[*] Evaluating Role: '{role}' with {len(required_rooms)} mandatory room(s)")
                    
                    # Create validated context for this role
                    try:
                        context = ExecutionContext(
                            system_state="Normal",
                            time_of_day=12,
                            active_escorts=["security_officer"],
                            present_roles=[role, "security_officer"]
                        )
                    except (ValueError, TypeError) as ctx_err:
                        guardrail_log.append(f"[!] ERROR: Invalid context for role '{role}': {str(ctx_err)}")
                        system_passed = False
                        continue
                    
                    # Convert to dict for engine.verify_path (for backward compatibility)
                    context_dict = {
                        "system_state": context.system_state,
                        "time_of_day": context.time_of_day,
                        "active_escorts": context.active_escorts,
                        "present_roles": context.present_roles,
                        "guards_distracted": context.guards_distracted
                    }
                    
                    for room in required_rooms:
                        try:
                            result = self.engine.verify_path(entry_point, room, role, context_dict)
                            
                            if result["path_found"]:
                                path_time = result["total_time"]
                                total_facility_delay += path_time
                                guardrail_log.append(f"    [+] PASS: Route confirmed to '{room}' ({path_time} mins elapsed).")
                            else:
                                guardrail_log.append(f"    [X] FAIL: Role is blocked from accessing '{room}'")
                                system_passed = False
                                
                        except Exception as path_error:
                            guardrail_log.append(
                                f"    [!] ERROR: Path evaluation failed for '{room}': {str(path_error)}"
                            )
                            system_passed = False
                            
                except Exception as role_error:
                    guardrail_log.append(
                        f"[!] ERROR: Role evaluation failed for '{role}': {str(role_error)}"
                    )
                    system_passed = False
                    
        except Exception as fatal_error:
            guardrail_log.append(f"[!] FATAL: Operational guardrail evaluation collapsed: {str(fatal_error)}")
            return {
                "operational_viable": False,
                "total_delay": 0,
                "efficiency_rating": 0,
                "log": guardrail_log
            }
        
        # Calculate efficiency rating using SimulationConstants
        efficiency_rating = CONFIG.calculate_efficiency_rating(total_facility_delay)
        
        guardrail_log.append("\n==================================================")
        guardrail_log.append("        OPERATIONAL EFFICIENCY REPORT             ")
        guardrail_log.append("==================================================")
        guardrail_log.append(f"[->] Total Mission Time: {total_facility_delay} minutes")
        guardrail_log.append(f"[->] Baseline Reference: {CONFIG.BASELINE_FACILITY_MISSION_TIME} minutes")
        guardrail_log.append(f"[->] Efficiency Rating: {efficiency_rating}/100")
        
        if system_passed:
            guardrail_log.append("\nAUDIT RESULT: ✓ OPERATIONAL COMPLIANCE ACHIEVED")
        else:
            guardrail_log.append("\nAUDIT RESULT: ✗ OPERATIONAL DEADLOCK DETECTED")
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