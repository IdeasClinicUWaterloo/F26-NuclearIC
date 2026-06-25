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
   def verify_facility_operations(self, entry_point="visitor_center"):
       """
       Validates that the current policy allows all critical personnel roles
       to reach checkpoints, calculating a cumulative Facility Efficiency Score.
       Includes advanced architectural guardrails for the 13-room advanced SMR layout.
       """
       guardrail_log = []
       system_passed = True
       total_facility_delay = 0
       guardrail_log.append("==================================================")
       guardrail_log.append("       STARTING OPERATIONAL GUARDRAIL CHECKS      ")
       guardrail_log.append("==================================================")
       guardrail_log.append(f"[*] Facility Entry Point: '{entry_point}'")
       try:
           # 1. Validate Entry Point Existence
           if entry_point not in self.blueprint.get_all_rooms():
               guardrail_log.append(f"[!] CONFIGURATION ERROR: Entry point '{entry_point}' not found in facility blueprint.")
               return {
                   "operational_viable": False,
                   "total_delay": 0,
                   "efficiency_rating": 0,
                   "log": guardrail_log
               }
           # 2. Advanced Guardrail: Structural Zoning Isolation Audit
           guardrail_log.append("\n[*] Running Guardrail: Vital Asset Zoning Isolation Audit...")
           vital_assets = ["main_control_room", "reactor_containment", "auxiliary_generator_bldg"]
           for asset in vital_assets:
               if asset in self.policy.room_to_zone:
                   asset_zone = self.policy.room_to_zone[asset]
                   public_rooms = ["visitor_center", "outer_parking"]
                   for public in public_rooms:
                       if self.policy.room_to_zone.get(public) == asset_zone:
                           guardrail_log.append(f"    [X] CRITICAL ZONE FAULT: Vital asset '{asset}' shares '{asset_zone}' with public area '{public}'!")
                           system_passed = False
           # 3. Standard Mission Reachability Checks for All Defined Roles
           all_roles = list(self.blueprint.operational_requirements.keys())
           for role in all_roles:
               required_rooms = self.blueprint.get_role_requirements(role)
               if not required_rooms:
                   guardrail_log.append(f"[*] Role '{role}': No mandatory operational rooms defined.")
                   continue
               guardrail_log.append(f"\n[*] Evaluating Normal Shifts Mission Capability for Role: '{role}'")
               # Build type-safe context representing standard shift pairing
               context_dict = {
                   "system_state": "Normal",
                   "time_of_day": 12,
                   "active_escorts": ["security_officer"],
                   "present_roles": [role, "security_officer"],
                   "guards_distracted": False
               }
               for room in required_rooms:
                   try:
                       result = self.engine.verify_path(entry_point, room, role, context_dict)
                       if result["path_found"]:
                           path_time = result["total_time"]
                           total_facility_delay += path_time
                           guardrail_log.append(f"    [+] PASS: '{role}' reached required node '{room}' ({path_time} mins elapsed).")
                       else:
                           guardrail_log.append(f"    [X] FAIL: '{role}' is completely blocked from accessing required node '{room}'!")
                           system_passed = False
                   except Exception as path_error:
                       guardrail_log.append(f"    [!] ERROR: Path evaluation failed for '{room}': {str(path_error)}")
                       system_passed = False
           # 4. Advanced Guardrail: Emergency First-Responder Fast-Path Verification
           guardrail_log.append("\n[*] Running Guardrail: Emergency First-Responder Fast-Path Verification...")
           emergency_context = {
               "system_state": "Emergency",
               "time_of_day": 2,  # Simulated critical middle-of-the-night alarm state
               "active_escorts": [],
               "present_roles": ["security_officer", "reactor_operator"],
               "guards_distracted": False
           }
           for critical_node in vital_assets:
               if critical_node in self.blueprint.get_all_rooms():
                   res = self.engine.verify_path(entry_point, critical_node, "security_officer", emergency_context)
                   if res["path_found"]:
                       resp_time = res["total_time"]
                       if resp_time > CONFIG.EMERGENCY_RESPONSE_CRITICAL_THRESHOLD:
                           guardrail_log.append(f"    [X] FAIL: Security Officer emergency dispatch to '{critical_node}' took too long ({resp_time} mins)! Max allowed: {CONFIG.EMERGENCY_RESPONSE_CRITICAL_THRESHOLD} mins.")
                           system_passed = False
                       else:
                           guardrail_log.append(f"    [+] PASS: Emergency fast-path verified to '{critical_node}' ({resp_time} mins).")
                   else:
                       guardrail_log.append(f"    [X] FAIL: Security Officers are locked out of '{critical_node}' during Emergency state configuration!")
                       system_passed = False
           # 5. Advanced Guardrail: Subterranean Shortcut Tunnel Least-Privilege Containment
           tunnel_node = "maintenance_bypass_tunnel"
           if tunnel_node in self.blueprint.get_all_rooms():
               guardrail_log.append("\n[*] Running Guardrail: Subterranean Tunnel Least-Privilege Containment...")
               contractor_context = {
                   "system_state": "Normal",
                   "time_of_day": 12,
                   "active_escorts": [],  # Unescorted contractor probe attempt
                   "present_roles": ["contractor"],
                   "guards_distracted": False
               }
               # Unescorted contractors should NEVER have a functional route through the bypass shortcut
               tunnel_check = self.engine.verify_path(entry_point, "fuel_service_corridor", "contractor", contractor_context)
               # Filter path list to see if the shortcut tunnel was utilized to sneak in
               if tunnel_check["path_found"] and tunnel_node in tunnel_check["path"]:
                   guardrail_log.append(f"    [X] LEAST-PRIVILEGE VIOLATION: Unescorted contractors can exploit the '{tunnel_node}' shortcut!")
                   system_passed = False
               else:
                   guardrail_log.append(f"    [+] PASS: Subterranean shortcut tunnel is properly isolated against unauthorized access.")
       except Exception as fatal_error:
           guardrail_log.append(f"[!] FATAL: Operational guardrail evaluation collapsed: {str(fatal_error)}")
           return {
               "operational_viable": False,
               "total_delay": 0,
               "efficiency_rating": 0,
               "log": guardrail_log
           }
       # Calculate final efficiency rating metrics
       efficiency_rating = CONFIG.calculate_efficiency_rating(total_facility_delay)
       guardrail_log.append("\n==================================================")
       guardrail_log.append("        OPERATIONAL EFFICIENCY REPORT             ")
       guardrail_log.append("==================================================")
       guardrail_log.append(f"[->] Cumulative Mission Transit Delay : {total_facility_delay} minutes")
       guardrail_log.append(f"[->] Game Baseline Reference Margin   : {CONFIG.BASELINE_FACILITY_MISSION_TIME} minutes")
       guardrail_log.append(f"[->] Total Operational Feasibility   : {efficiency_rating}/100")
       if system_passed:
           guardrail_log.append("\nAUDIT RESULT: ✓ OPERATIONAL COMPLIANCE ACHIEVED")
       else:
           guardrail_log.append("\nAUDIT RESULT: ✗ OPERATIONAL SYSTEM FAULT DETECTED")
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