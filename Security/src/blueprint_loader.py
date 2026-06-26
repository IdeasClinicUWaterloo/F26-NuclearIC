import json
import os

class BlueprintLoader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.facility_name = ""
        self.rooms = set()
        self.graph = {}  # Adjacency list representation: {room: [connected_rooms]}
        self.operational_requirements = {}
        
        self._load_and_validate()

    def _load_and_validate(self):
        """Loads the JSON blueprint and executes physical integrity checks."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Blueprint file not found at: {self.filepath}")
            
        with open(self.filepath, 'r') as f:
            data = json.load(f)
            
        self.facility_name = data.get("facility_name", "Unnamed Facility")
        self.rooms = set(data.get("rooms", []))
        self.operational_requirements = data.get("operational_requirements", {})
        
        for room in self.rooms:
            self.graph[room] = set()
            
        adjacencies = data.get("adjacencies", [])
        for edge in adjacencies:
            room_a = edge.get("from")
            room_b = edge.get("to")
            bidirectional = edge.get("bidirectional", True)
            
            if room_a not in self.rooms:
                raise ValueError(f"Blueprint Error: Connection source '{room_a}' is not defined in the 'rooms' list.")
            if room_b not in self.rooms:
                raise ValueError(f"Blueprint Error: Connection destination '{room_b}' is not defined in the 'rooms' list.")
                
            self.graph[room_a].add(room_b)
            if bidirectional:
                self.graph[room_b].add(room_a)

    def requires_two_person_rule(self, room_id):
        """Returns True if the room demands concurrent dual-authentication presence."""
        return room_id in ["main_control_room", "reactor_containment"]

    def get_connected_rooms(self, room_id):
        """Returns all rooms physically accessible from a given room."""
        return self.graph.get(room_id, set())

    def get_all_rooms(self):
        """Returns the list of all valid rooms in the facility."""
        return list(self.rooms)

    def get_role_requirements(self, role):
        """Returns the list of rooms a specific role must be able to access."""
        role_data = self.operational_requirements.get(role, {})
        return role_data.get("required_rooms", [])