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
        """Loads the security policy and cross-references it with the physical layout blueprint."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Policy configuration file not found at: {self.filepath}")
            
        with open(self.filepath, 'r') as f:
            data = json.load(f)
            
        self.author_name = data.get("author_name", "Unknown Author")
        self.room_to_zone = data.get("room_to_zone", {})
        self.zone_policies = data.get("zone_policies", {})
        
        # Guardrail: Ensure every single blueprint room is explicitly mapped to a zone layout
        blueprint_rooms = self.blueprint.get_all_rooms()
        for room in blueprint_rooms:
            if room not in self.room_to_zone:
                raise ValueError(f"Configuration Error: Room '{room}' from blueprint is missing a zone assignment!")
                
        # Guardrail: Prevent mapping of non-existent rooms
        for room in self.room_to_zone.keys():
            if room not in blueprint_rooms:
                raise ValueError(f"Configuration Error: Policy configuration references a room '{room}' that does not exist in the layout blueprint.")

    def get_room_rules_for_role(self, room_id, role):
        """
        Retrieves access parameters for a given role within a room's designated zone.
        Strictly enforces Least Privilege: missing definitions default to 'Denied'.
        """
        zone = self.room_to_zone.get(room_id)
        if not zone:
            return {"access": "Denied", "requires_escort": False}
            
        role_rules = self.zone_policies.get(zone, {}).get(role)
        if not role_rules:
            # Fallback mechanism: If a zone or role configuration block is omitted, default to fail-secure
            return {"access": "Denied", "requires_escort": False}
            
        return role_rules

# --- Local Test Execution ---
if __name__ == "__main__":
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        blueprint_path = os.path.join(project_root, "data", "facility_blueprint.json")
        policy_path = os.path.join(project_root, "data", "policy_config.json")
        
        loader = BlueprintLoader(blueprint_path)
        pm = PolicyManager(policy_path, loader)
        
        print(f"Successfully verified configuration policy by: {pm.author_name}")
        
        # Testing explicitly defined Zone 5 rule
        defined_rules = pm.get_room_rules_for_role("reactor_containment", "maintenance_technician")
        print(f"Explicit Zone 5 Rule (Maintenance Tech): {defined_rules}")
        
        # Testing omitted Zone 2 rule (Fail-Secure Fallback)
        fallback_rules = pm.get_room_rules_for_role("office_hallway", "reactor_operator")
        print(f"Omitted Zone 2 Fallback Rule (Reactor Operator): {fallback_rules}")
        
    except Exception as e:
        print(f"Policy Manager System Fault: {e}")