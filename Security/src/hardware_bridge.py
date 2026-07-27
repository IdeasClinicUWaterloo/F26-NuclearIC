import os
import time
import serial  # Requires standard 'pip install pyserial'
from blueprint_loader import BlueprintLoader
from policy_manager import PolicyManager
from graph_engine import GraphEngine


def _resolve_default_escort_for_role(policy_manager, role, system_state):
    """Finds the configured escort role for a role/state pair, if any zone requires one."""
    state = system_state.lower()
    for zone_cfg in policy_manager.zone_policies.values():
        role_cfg = zone_cfg.get(state, {}).get(role, {})
        if role_cfg.get("requires_escort", False):
            return role_cfg.get("escort_role") or "security_officer"
    return None


def run_hardware_serial_bridge(com_port="COM3", baud_rate=115200):
   src_dir = os.path.dirname(os.path.abspath(__file__))
   root_dir = os.path.dirname(src_dir)
   # 1. Initialize active structural mapping models
   loader = BlueprintLoader(os.path.join(root_dir, "data", "facility_blueprint.json"))
   pm = PolicyManager(os.path.join(root_dir, "data", "policy_config.json"), loader)
   engine = GraphEngine(loader, pm)
   # NTAG215 Hardware Map Registry
   NFC_REGISTRY = {
       "04:3E:5B:A2:91:5D:80": "contractor",
       "04:3C:4E:47:9E:61:80": "reactor_operator",
       "04:A1:7C:E2:8F:40:81": "maintenance_technician",
       "04:D2:9A:F2:3C:11:82": "security_officer"
   }
   print(f"[*] Opening Serial Connection on {com_port}...")
   try:
       ser = serial.Serial(com_port, baud_rate, timeout=1)
       time.sleep(2)  # Give Arduino brief window to complete reboot sequence
       print("[+] PPS Serial Bridge Active. Scan an NTAG215 Badge on the terminal...")
   except Exception as e:
       print(f"[X] Serial Connection Failure: {e}")
       return
   while True:
        # Check if there are incoming bytes waiting in the serial buffer
        if ser.in_waiting > 0:
            # Read incoming raw text broadcasted from Arduino
            raw_data = ser.readline().decode('utf-8').strip()
            if not raw_data:
                continue

            # 1. Filter out Arduino setup logs / status messages
            # A valid 7-byte NTAG215 UID string splits into exactly 7 colon-separated parts
            if len(raw_data.split(":")) != 7:
                print(f"[*] Arduino Boot Message: {raw_data}")
                continue

            # 2. Process actual UID scans
            print(f"\n[+] Raw Hardware Intercept: UID Scanned -> {raw_data}")
            role = NFC_REGISTRY.get(raw_data)
            
            if not role:
                print("    [-] UNKNOWN CREDENTIAL: Access Denied.")
                ser.write(b'0')  # Transmit failure token to flash Red LED
                continue

            escort_role = _resolve_default_escort_for_role(pm, role, "Normal")
            active_escorts = [escort_role] if escort_role else []
            present_roles = [role]
            if escort_role and escort_role not in present_roles:
                present_roles.append(escort_role)

            # Formulate context vector tracking metrics
            context = {
                "system_state": "Normal",
                "time_of_day": 12,
                "active_escorts": active_escorts,
                "present_roles": present_roles,
                "guards_distracted": False
            }

            # Run Dijkstra checking validation routines
            print(f"    [*] Auditing path for '{role}' from parking to fuel corridor...")
            result = engine.verify_path("outer_parking", "fuel_service_corridor", role, context)

            if result["path_found"]:
                print(f"    [✔] TRAJECTORY VERIFIED: Access Granted ({result['total_time']} mins).")
                ser.write(b'1')  # Transmit success token to activate Green LED
            else:
                print(f"    [X] POLICY RESTRICTION: Access Blocked. Reason: {result['audit_trail'][-1]}")
                ser.write(b'0')  # Transmit failure token to flash Red LED
                
        time.sleep(0.01)
if __name__ == "__main__":
   # Students find their assigned hardware port using Device Manager
   run_hardware_serial_bridge(com_port="COM3")