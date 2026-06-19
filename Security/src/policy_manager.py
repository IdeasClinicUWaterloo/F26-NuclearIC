import json
import os
from blueprint_loader import BlueprintLoader

class PolicyManager:
    def __init__(self, policy_filepath, blueprint_loader: BlueprintLoader):
        self.filepath = policy_filepath
        self.blueprint = blueprint_loader
        self.author_name = ""
        self.room_to_zone = {}
        self.zone_policies = {}
        self._load_and_validate_policy()

    def _load_and_validate_policy(self):
        """Loads and processes the system config against the master layout blueprint."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Policy configuration file not found at: {self.filepath}")
            
        with open(self.filepath, 'r') as f:
            data = json.load(f)
            
        self.author_name = data.get("author_name", "Unknown Author")
        self.room_to_zone = data.get("room_to_zone", {})
        self.zone_policies = data.get("zone_policies", {})
        
        blueprint_rooms = self.blueprint.get_all_rooms()
        for room in blueprint_rooms:
            if room not in self.room_to_zone:
                raise ValueError(f"Configuration Error: Room '{room}' is missing a zone assignment!")

    def get_room_rules_for_role(self, room_id, role, state="normal"):
        """Extracts strict access bounds based on specific facility states (normal/emergency)."""
        zone = self.room_to_zone.get(room_id)
        fallback_secure = {"access": "Denied", "requires_escort": False, "time_window": [0, 0]}
        
        if not zone or zone not in self.zone_policies:
            return fallback_secure
            
        state_policies = self.zone_policies[zone].get(state, {})
        return state_policies.get(role, fallback_secure)

    def is_transition_authorized(self, room_id, role, context, log_accumulator):
        """Executes full multidimensional compliance check against the active environment state."""
        system_state = context.get("system_state", "Normal").lower() # Normal or Emergency
        rules = self.get_room_rules_for_role(room_id, role, state=system_state)
        
        # 1. Base Access Clearance Check
        if rules["access"] == "Denied":
            log_accumulator.append(f"    [-] Access Denied: '{role}' blocked from '{room_id}' under {system_state.upper()} operational state.")
            return False

        # 2. Temporal Compliance Check
        current_time = context.get("time_of_day", 12)
        time_window = rules.get("time_window", [0, 23])
        if not (time_window[0] <= current_time <= time_window[1]):
            log_accumulator.append(f"    [X] Temporal Block: '{role}' locked out of '{room_id}' at {current_time}:00.")
            return False

        # 3. Dynamic Escort Validation Check
        if rules.get("requires_escort", False):
            required_escort = rules.get("escort_role")
            active_escorts = context.get("active_escorts", [])
            
            if required_escort not in active_escorts:
                log_accumulator.append(
                    f"    [X] Escort Violation: Unsupervised asset movement detected! "
                    f"'{role}' requires a '{required_escort}' to enter '{room_id}'."
                )
                return False
            else:
                log_accumulator.append(f"    [+] Compliance Verified: Verified active supervision by '{required_escort}'.")

        return True