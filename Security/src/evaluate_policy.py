import os
import sys
from blueprint_loader import BlueprintLoader
from policy_manager import PolicyManager
from graph_engine import GraphEngine
from guardrails import OperationalGuardrails
from attackers import SocialEngineer, Impersonator, Insider, EmergencyExploiter
def run_comprehensive_evaluation():
   # Establish workspace directory paths
   src_dir = os.path.dirname(os.path.abspath(__file__))
   root_dir = os.path.dirname(src_dir)
   blueprint_path = os.path.join(root_dir, "data", "facility_blueprint.json")
   policy_path = os.path.join(root_dir, "data", "policy_config.json")
   if not os.path.exists(policy_path):
       print("[X] EVALUATION CRITICAL ERROR: No deployed policy configuration discovered!")
       print("    Please execute 'policy_dashboard.py' first and click 'Compile & Deploy'.")
       sys.exit(1)
   print("=" * 60)
   print("   SMR PHYSICAL PROTECTION PLATFORM: COMPREHENSIVE EVALUATION")
   print("=" * 60)
   # 1. Initialize Subsystem Modeling Engines
   loader = BlueprintLoader(blueprint_path)
   policy_m = PolicyManager(policy_path, loader)
   engine = GraphEngine(loader, policy_m)
   print(f"[*] Analyzing Blueprint: {loader.facility_name}")
   print(f"[*] Policy Matrix Author: {policy_m.author_name}")
   print("-" * 60)
   # 2. PHASE 1: Run Operational Feasibility Guardrails
   print("\n[PHASE 1] RUNNING OPERATIONAL FEASIBILITY CHECKS...")
   guardrails_suite = OperationalGuardrails(loader, policy_m, engine)
   ops_report = guardrails_suite.verify_facility_operations()
   for line in ops_report["log"]:
       print(line)
   # 3. PHASE 2: Run Active Adversary Threat Simulations
   print("\n[PHASE 2] INITIATING ACTIVE THREAT VECTOR SIMULATIONS...")
   attack_results = {}
   # Threat Profile A: The Social Engineer
   print("\n--> Deploying Threat Actor: The Social Engineer...")
   se_attacker = SocialEngineer(loader, policy_m, engine)
   # Checks if maintenance technicians drop down security levels along their mission route
   report_se = se_attacker.execute_attack(target_role="maintenance_technician")
   attack_results["Social Engineer"] = report_se["attack_successful"]
   for line in report_se["log"]: print(f"    {line}")
   # Threat Profile B: The Impersonator
   print("\n--> Deploying Threat Actor: The Impersonator...")
   imp_attacker = Impersonator(loader, policy_m, engine)
   # Probes if unescorted contractors can breach vital nodes via guard congestion/distraction
   report_imp = imp_attacker.execute_attack()
   attack_results["Impersonator"] = report_imp["attack_successful"]
   for line in report_imp["log"]: print(f"    {line}")
   # Threat Profile C: The Insider
   print("\n--> Deploying Threat Actor: The Insider...")
   ins_attacker = Insider(loader, policy_m, engine)
   # Tests if a rogue technician can execute unauthorized lateral sweeps into the control room
   report_ins = ins_attacker.execute_attack(rogue_role="maintenance_technician", unauthorized_targets=["main_control_room"])
   attack_results["Insider"] = report_ins["attack_successful"]
   for line in report_ins["log"]: print(f"    {line}")
   # Threat Profile D: The Emergency Exploiter
   print("\n--> Deploying Threat Actor: The Emergency Exploiter...")
   ee_attacker = EmergencyExploiter(loader, policy_m, engine)
   # Verifies if emergency response velocity holds or if alert rules cause systemic deadlocks
   report_ee = ee_attacker.execute_attack()
   attack_results["Emergency Exploiter"] = report_ee["attack_successful"]
   for line in report_ee["log"]: print(f"    {line}")
   # 4. PHASE 3: Compile and Render Final System Scorecard
   print("\n" + "=" * 60)
   print("                    FINAL SYSTEM SCORECARD")
   print("=" * 60)
   print(f"Designer/Group Name      : {policy_m.author_name}")
   print(f"Plant Operational Status : {'COMPLIANT' if ops_report['operational_viable'] else 'DEADLOCKED / NON-VIABLE'}")
   print(f"Facility Efficiency Score : {ops_report['efficiency_rating']}/100")
   print("-" * 60)
   print("THREAT VECTOR MITIGATION LOGS:")
   total_mitigated = 0
   for threat, breached in attack_results.items():
       status_str = "❌ BREACHED (Vulnerability Exploited)" if breached else "🛡️ REPELLED (Controls Verified)"
       if not breached:
           total_mitigated += 1
       print(f" • {threat:<22}: {status_str}")
   print("-" * 60)
   security_score = int((total_mitigated / 4) * 100)
   print(f"Overall Security Defense Rating : {security_score}/100")
   # 5. Determine Overall Certification Standing
   print("\nSYSTEM EVALUATION VERDICT:")
   if not ops_report["operational_viable"]:
       print("🔴 STATUS: CERTIFICATION DENIED\nReason: Plant operations are deadlocked. Staff cannot perform vital duties.")
   elif security_score < 100:
       print("⚠️ STATUS: CERTIFICATION DEFERRED\nReason: Plant is operationally viable, but critical threat vulnerabilities remain unmitigated.")
   else:
       print("🏆 STATUS: PASSED - DESIGN CERTIFIED SECURE\nCongratulations: Perfect security defense matrix with verified operational feasibility.")
   print("=" * 60)
if __name__ == "__main__":
   run_comprehensive_evaluation()