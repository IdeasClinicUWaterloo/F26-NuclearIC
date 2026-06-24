import os
import heapq
from blueprint_loader import BlueprintLoader
from policy_manager import PolicyManager
from context_validator import ExecutionContext

class GraphEngine:
    def __init__(self, blueprint_loader: BlueprintLoader, policy_manager: PolicyManager):
        self.blueprint = blueprint_loader
        self.policy = policy_manager
        self._current_traversal_path = []  # Internal path history tracking (not user-exposed)

    def _get_zone_level(self, room_id):
        """Helper to extract the numeric tier from a room's assigned zone (e.g., 'Zone_3' -> 3)."""
        zone = self.policy.room_to_zone.get(room_id, "Zone_0")
        try:
            return int(zone.split("_")[-1])
        except (ValueError, IndexError):
            return 0
    
    def _validate_role(self, role: str) -> bool:
        """Check if role is defined in blueprint operational requirements."""
        return role in self.blueprint.operational_requirements
    
    def _get_visited_zones(self) -> list:
        """Returns list of zones visited so far in current traversal."""
        return [self.policy.room_to_zone.get(room) for room in self._current_traversal_path]

    def verify_path(self, start_room, end_room, role, context=None):
        """
        Uses Dijkstra's Algorithm to find the lowest time-cost path through the facility
        while validating security policies and tracking accumulated operational delays.
        """
        # PRIORITY 1.2: Validate role input
        if not self._validate_role(role):
            return {
                "path_found": False, 
                "path": [], 
                "total_time": 0,
                "audit_trail": [
                    f"[!] Invalid role '{role}'.",
                    f"[!] Valid roles: {list(self.blueprint.operational_requirements.keys())}"
                ]
            }
        
        # PRIORITY 2.1: Normalize and validate context input
        try:
            if context is None:
                context_obj = ExecutionContext()  # Use defaults
            else:
                context_obj = ExecutionContext.from_dict(context)  # Validate & normalize
        except (ValueError, TypeError) as ctx_err:
            return {
                "path_found": False,
                "path": [],
                "total_time": 0,
                "audit_trail": [f"[!] Invalid execution context: {str(ctx_err)}"]
            }
        
        # Use validated context for the rest of the function
        context = {
            "system_state": context_obj.system_state,
            "time_of_day": context_obj.time_of_day,
            "active_escorts": context_obj.active_escorts,
            "present_roles": context_obj.present_roles,
            "guards_distracted": context_obj.guards_distracted
        }

        system_state = context.get("system_state", "Normal").lower()
        audit_trail = []
        audit_trail.append(f"[*] Simulating Transit: Role='{role}' | State='{context['system_state']}' | Time={context['time_of_day']}:00")
        
        # PRIORITY 1.1: Initialize internal path tracking (not exposed to caller)
        self._current_traversal_path = [start_room]

        all_rooms = self.blueprint.get_all_rooms()
        if start_room not in all_rooms or end_room not in all_rooms:
            return {"path_found": False, "path": [], "total_time": 0, "audit_trail": ["[!] Target node mismatch."]}

        # Check origin clearance
        if not self.policy.is_transition_authorized(start_room, role, context, audit_trail):
            return {"path_found": False, "path": [], "total_time": 0, "audit_trail": audit_trail}

        # Priority Queue element format: (accumulated_time, current_room, [ordered_path_history])
        pq = [(0, start_room, [start_room])]
        min_time_to_room = {start_room: 0}

        while pq:
            current_time, current_room, current_path = heapq.heappop(pq)

            if current_room == end_room:
                audit_trail.append(f"[+] Routing Confirmed: {' -> '.join(current_path)} (Total Path Time: {current_time} mins)")
                return {"path_found": True, "path": current_path, "total_time": current_time, "audit_trail": audit_trail}

            # Skip branch processing if an operationally cheaper configuration was already registered
            if current_time > min_time_to_room.get(current_room, float('inf')):
                continue

            for next_room in self.blueprint.get_connected_rooms(current_room):
                # PRIORITY 1.1: Use internal path tracking instead of context parameter
                # Update internal path to current position
                self._current_traversal_path = current_path
                visited_zones = self._get_visited_zones()

                if not self.policy.is_transition_authorized(next_room, role, context, audit_trail, visited_zones=visited_zones):
                    continue

                # --- Dynamic Time Cost Calculations ---
                base_cost = 1  
                zone_cost = 0
                escort_cost = 0

                # 1. Evaluate Security Gradient Step Up
                current_lvl = self._get_zone_level(current_room)
                next_lvl = self._get_zone_level(next_room)
                if next_lvl > current_lvl:
                    zone_cost = 5  

                # 2. Resource Constraints: Escalating Delay Pricing
                rules = self.policy.get_room_rules_for_role(next_room, role, state=system_state)
                if rules.get("requires_escort", False):
                    escort_count = self.policy.get_escort_requirement_count(system_state)
                    
                    if escort_count <= 1:
                        escort_cost = 15  # Optimal staffing availability
                    elif escort_count == 2:
                        escort_cost = 35  # Congestion: Guards are shared across zones
                    else:
                        escort_cost = 65  # Severe Saturation: Critical staffing log delay

                transition_time = base_cost + zone_cost + escort_cost
                next_time = current_time + transition_time

                if next_time < min_time_to_room.get(next_room, float('inf')):
                    min_time_to_room[next_room] = next_time
                    heapq.heappush(pq, (next_time, next_room, current_path + [next_room]))

        # Clean up internal state
        self._current_traversal_path = []
        audit_trail.append(f"[X] No viable paths found from '{start_room}' to '{end_room}'.")
        return {"path_found": False, "path": [], "total_time": 0, "audit_trail": audit_trail}

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    loader = BlueprintLoader(os.path.join(project_root, "data", "facility_blueprint.json"))
    pm = PolicyManager(os.path.join(project_root, "data", "policy_config.json"), loader)
    engine = GraphEngine(loader, pm)

    print("==================================================")
    print("      TESTING OPERATIONAL TIME-COST ROUTING       ")
    print("==================================================\n")

    # Run unescorted vs escorted technician to observe Dijkstra choosing different optimal balances
    ctx_escorted = {"system_state": "Normal", "time_of_day": 10, "active_escorts": ["security_officer"]}
    res = engine.verify_path("perimeter_gate", "reactor_containment", "maintenance_technician", ctx_escorted)
    for line in res["audit_trail"]:
        print(line)