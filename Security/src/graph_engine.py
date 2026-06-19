import os
from collections import deque
from blueprint_loader import BlueprintLoader
from policy_manager import PolicyManager

class GraphEngine:
    def __init__(self, blueprint_loader: BlueprintLoader, policy_manager: PolicyManager):
        self.blueprint = blueprint_loader
        self.policy = policy_manager

    def verify_path(self, start_room, end_room, role, context=None):
        """Uses BFS to calculate physical trajectories, verifying advanced rules on every transition."""
        if context is None:
            context = {"system_state": "Normal", "time_of_day": 12, "active_escorts": []}

        audit_trail = []
        audit_trail.append(f"[*] Simulating Transit: Role='{role}' | State='{context['system_state']}' | Time={context['time_of_day']}:00")

        all_rooms = self.blueprint.get_all_rooms()
        if start_room not in all_rooms or end_room not in all_rooms:
            return {"path_found": False, "path": [], "audit_trail": ["[!] Target node mismatch."]}

        # Check origin clearance
        if not self.policy.is_transition_authorized(start_room, role, context, audit_trail):
            return {"path_found": False, "path": [], "audit_trail": audit_trail}

        queue = deque([(start_room, [start_room])])
        visited = set([start_room])

        while queue:
            current_room, current_path = queue.popleft()

            if current_room == end_room:
                audit_trail.append(f"[+] Routing Confirmed: {' -> '.join(current_path)}")
                return {"path_found": True, "path": current_path, "audit_trail": audit_trail}

            for next_room in self.blueprint.get_connected_rooms(current_room):
                if next_room in visited:
                    continue

                if not self.policy.is_transition_authorized(next_room, role, context, audit_trail):
                    continue

                visited.add(next_room)
                queue.append((next_room, current_path + [next_room]))

        audit_trail.append(f"[X] No viable paths found from '{start_room}' to '{end_room}'.")
        return {"path_found": False, "path": [], "audit_trail": audit_trail}

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    loader = BlueprintLoader(os.path.join(project_root, "data", "facility_blueprint.json"))
    pm = PolicyManager(os.path.join(project_root, "data", "policy_config.json"), loader)
    engine = GraphEngine(loader, pm)

    print("==================================================")
    print("      ADVANCED POLICY MATRIX COMPLIANCE TEST      ")
    print("==================================================\n")

    # TEST CASE 1: Normal Operations, Unescorted Contractor/Technician
    # Expectation: Fails at Zone 5 entry due to lack of a Security Officer escort.
    ctx_1 = {"system_state": "Normal", "time_of_day": 10, "active_escorts": []}
    print("[RUN 1: Technician Day Shift - Unescorted]")
    res_1 = engine.verify_path("perimeter_gate", "reactor_containment", "maintenance_technician", ctx_1)
    print(f"Outcome: {'SUCCESS' if res_1['path_found'] else 'FAILED'}")
    print(f"Log Trace: {res_1['audit_trail'][-2]}\n")

    print("--------------------------------------------------\n")

    # TEST CASE 2: Normal Operations, Escort Authorized
    # Expectation: Path clear. The technician is granted entry because an escort is present.
    ctx_2 = {"system_state": "Normal", "time_of_day": 10, "active_escorts": ["security_officer"]}
    print("[RUN 2: Technician Day Shift - Escorted by Security Officer]")
    res_2 = engine.verify_path("perimeter_gate", "reactor_containment", "maintenance_technician", ctx_2)
    print(f"Outcome: {'SUCCESS' if res_2['path_found'] else 'FAILED'}")
    print(f"Log Trace: {res_2['audit_trail'][-1]}\n")

    print("--------------------------------------------------\n")

    # TEST CASE 3: Crisis / Emergency State Fast-Path vs Lockdown Execution
    # Expectation: Even with an escort, the technician is strictly denied access due to lockdown.
    ctx_3 = {"system_state": "Emergency", "time_of_day": 10, "active_escorts": ["security_officer"]}
    print("[RUN 3: Crisis Mode Injected - Escorted Technician Attempts Entry]")
    res_3 = engine.verify_path("perimeter_gate", "reactor_containment", "maintenance_technician", ctx_3)
    print(f"Outcome: {'SUCCESS' if res_3['path_found'] else 'FAILED'}")
    print(f"Log Trace: {res_3['audit_trail'][-2]}\n")