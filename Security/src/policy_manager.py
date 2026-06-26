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
        fallback_secure = {"access": "Denied", "requires_escort": False, "time_window": [0, 0], "zone_dependency": None}
        
        if not zone or zone not in self.zone_policies:
            return fallback_secure
            
        state_policies = self.zone_policies[zone].get(state, {})
        return state_policies.get(role, fallback_secure)

    def get_escort_requirement_count(self, state="normal"):
        """Resource Tracker: Counts total role-zone pairs demanding active escort deployments."""
        count = 0
        for zone, states in self.zone_policies.items():
            role_configs = states.get(state, {})
            for role, rules in role_configs.items():
                if rules.get("requires_escort", False):
                    count += 1
        return count

    def _is_role_basic_authorized(self, room_id, role, context):
        """Determines if an accompanying buddy role holds baseline authorization clearances for a room."""
        system_state = context.get("system_state", "Normal").lower()
        rules = self.get_room_rules_for_role(room_id, role, state=system_state)
        if rules["access"] == "Denied":
            return False
        current_time = context.get("time_of_day", 12)
        time_window = rules.get("time_window", [0, 23])
        return time_window[0] <= current_time <= time_window[1]

    def is_transition_authorized(self, room_id, role, context, log_accumulator, visited_zones=None):
        """Executes full multidimensional compliance check against the active environment state."""
        system_state = context.get("system_state", "Normal").lower()
        rules = self.get_room_rules_for_role(room_id, role, state=system_state)
        
        # PRIORITY 1.1: Use internally-tracked visited_zones instead of context-provided path_history
        if visited_zones is None:
            visited_zones = []  # Fail-secure default
        
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

        # 3. Sequential Zone Dependency Check
        dependent_zone = rules.get("zone_dependency")
        if dependent_zone:
            # PRIORITY 1.1: Use internally-tracked visited zones (safe from spoofing)
            cleared_zones = visited_zones
            
            if dependent_zone not in cleared_zones:
                log_accumulator.append(
                    f"    [X] Sequential Violation: Gate entry to '{room_id}' rejected. "
                    f"Policy mandates prior clearance of '{dependent_zone}'."
                )
                return False
            else:
                log_accumulator.append(f"    [+] Sequence Verified: Path logs confirm historical clearance of '{dependent_zone}'.")

        # 4. Two-Person Rule (Concurrent Authentication) Verification Check
        if self.blueprint.requires_two_person_rule(room_id):
            present_roles = context.get("present_roles", [role])
            authorized_buddies = [r for r in present_roles if self._is_role_basic_authorized(room_id, r, context)]
            
            if len(authorized_buddies) < 2:
                log_accumulator.append(
                    f"    [X] Two-Person Rule Violation: Vital area '{room_id}' requires 2 concurrently authorized roles. "
                    f"Present authorized team: {authorized_buddies}."
                )
                return False
            else:
                log_accumulator.append(f"    [+] Two-Person Rule Satisfied: Dual authorized presence confirmed: {authorized_buddies}.")

        # 5. Dynamic Escort Validation Check with Resource Bottlenecking
        if rules.get("requires_escort", False):
            if context.get("guards_distracted", False):
                log_accumulator.append(
                    f"    [!] Resource Exploit: Security Officers are spread thin by excessive escort assignments. "
                    f"Bypassed verification check for '{role}' entering '{room_id}'!"
                )
                return True
                
            required_escort = rules.get("escort_role")
            
            # PRIORITY 1.3: Validate escort_role exists before using
            if not required_escort:
                log_accumulator.append(
                    f"    [!] Configuration Error: Zone '{self.room_to_zone.get(room_id)}' requires escort "
                    f"but 'escort_role' is undefined. Failing secure."
                )
                return False
            
            active_escorts = context.get("active_escorts", [])
            
            if required_escort not in active_escorts:
                log_accumulator.append(f"    [X] Escort Violation: '{role}' requires a '{required_escort}' to enter '{room_id}'.")
                return False
            else:
                log_accumulator.append(f"    [+] Compliance Verified: Active supervision by '{required_escort}'.")

        return True