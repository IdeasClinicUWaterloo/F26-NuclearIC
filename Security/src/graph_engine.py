import os
from collections import deque
from blueprint_loader import BlueprintLoader
from policy_manager import PolicyManager

class GraphEngine:
    def __init__(self, blueprint_loader: BlueprintLoader, policy_manager: PolicyManager):
        self.blueprint = blueprint_loader
        self.policy = policy_manager

    def verify_path(self, start_room, end_room, role, context=None):
        """
        Uses Breadth-First Search (BFS) to discover and validate a path through the facility.
        Cross-references security rules at every physical node transition.
        
        Returns:
            dict: {
                "path_found": bool,
                "path": list of room IDs,
                "audit_trail": list of logging strings detailing the evaluation
            }
        """
        # Establish default system context for future-proofing directives
        if context is None:
            context = {"system_state": "Normal", "active_escorts": []}

        audit_trail = []
        audit_trail.append(f"[*] Initializing navigation validation for Role: '{role}'")
        audit_trail.append(f"    -> Departure: '{start_room}'")
        audit_trail.append(f"    -> Destination: '{end_room}'")

        all_rooms = self.blueprint.get_all_rooms()
        if start_room not in all_rooms or end_room not in all_rooms:
            audit_trail.append("[!] Evaluation Aborted: Invalid start or end room provided.")
            return {"path_found": False, "path": [], "audit_trail": audit_trail}

        # Principle of Least Privilege: Validate baseline entry to the origin point
        initial_rules = self.policy.get_room_rules_for_role(start_room, role)
        if initial_rules["access"] == "Denied":
            audit_trail.append(f"[X] Access Denied: Role '{role}' lacks clearance to occupy origin point '{start_room}'.")
            return {"path_found": False, "path": [], "audit_trail": audit_trail}

        # Queue tracking format: (current_room_id, [ordered_path_history])
        queue = deque([(start_room, [start_room])])
        visited = set([start_room])

        while queue:
            current_room, current_path = queue.popleft()

            # Target Destination Reached Successfully
            if current_room == end_room:
                audit_trail.append(f"[+] Route Verified: {' -> '.join(current_path)}")
                return {"path_found": True, "path": current_path, "audit_trail": audit_trail}

            # Evaluate outward physical transitions
            connected_rooms = self.blueprint.get_connected_rooms(current_room)
            for next_room in connected_rooms:
                if next_room in visited:
                    continue

                # Gatekeeper Pattern Hook: Query policy engine regarding the target room
                rules = self.policy.get_room_rules_for_role(next_room, role)
                
                # Check 1: Explicit Access Blocks
                if rules["access"] == "Denied":
                    audit_trail.append(f"[-] Barrier Hit: '{role}' blocked from transitioning into '{next_room}' (Access: Denied).")
                    continue
                
                # Check 2: Escort Constraints (Future Directive Hook)
                if rules.get("requires_escort", False):
                    audit_trail.append(f"[*] Escort Flagged: Entering '{next_room}' requires active escort supervision.")
                    # Note: Future challenge iterations will check if an escort role is present in context

                # Node is valid and authorized; proceed to register transit
                visited.add(next_room)
                queue.append((next_room, current_path + [next_room]))

        audit_trail.append(f"[X] Isolation Verified: No authorized routes exist for '{role}' to navigate to '{end_room}'.")
        return {"path_found": False, "path": [], "audit_trail": audit_trail}


# --- Local Orchestration & Test Execution ---
if __name__ == "__main__":
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        blueprint_path = os.path.join(project_root, "data", "facility_blueprint.json")
        policy_path = os.path.join(project_root, "data", "policy_config.json")
        
        # Dependency Injection Chain
        loader = BlueprintLoader(blueprint_path)
        pm = PolicyManager(policy_path, loader)
        engine = GraphEngine(loader, pm)
        
        print("==================================================")
        print("        GRAPH ENGINE INTERCONNECTIVITY TEST       ")
        print("==================================================\n")
        
        # Test Case A: Valid Path Verification (Operator tracking to Control Room)
        result_a = engine.verify_path("perimeter_gate", "main_control_room", "reactor_operator")
        for log in result_a["audit_trail"]:
            print(log)
            
        print("\n--------------------------------------------------\n")
        
        # Test Case B: Blocked Path/Fail-Secure Verification 
        # (Operator tries to enter Zone 2 / Office Hallway, which was deliberately left out of config)
        result_b = engine.verify_path("perimeter_gate", "staff_lounge", "reactor_operator")
        for log in result_b["audit_trail"]:
            print(log)

    except Exception as e:
        print(f"Graph Engine System Fault: {e}")