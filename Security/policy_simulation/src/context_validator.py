from dataclasses import dataclass, field
from typing import List


@dataclass
class ExecutionContext:
    """
    Validated and normalized execution context for policy evaluation.
    Ensures all required fields are present with correct types.
    """
    system_state: str = "Normal"  # "Normal", "Emergency", "Alert"
    time_of_day: int = 12  # 0-23 hours
    active_escorts: List[str] = field(default_factory=list)
    present_roles: List[str] = field(default_factory=list)
    guards_distracted: bool = False
    
    def __post_init__(self):
        """Validate context values."""
        # Validate system_state
        valid_states = {"normal", "emergency", "alert"}
        if self.system_state.lower() not in valid_states:
            raise ValueError(
                f"Invalid system_state: '{self.system_state}'. "
                f"Must be one of: {valid_states}"
            )
        
        # Validate time_of_day
        if not isinstance(self.time_of_day, int) or not (0 <= self.time_of_day <= 23):
            raise ValueError(f"Invalid time_of_day: {self.time_of_day}. Must be int 0-23.")
        
        # Validate list types
        if not isinstance(self.active_escorts, list):
            raise TypeError(f"active_escorts must be list, got {type(self.active_escorts)}")
        if not isinstance(self.present_roles, list):
            raise TypeError(f"present_roles must be list, got {type(self.present_roles)}")
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExecutionContext':
        """Factory method to create and validate from dictionary."""
        return cls(
            system_state=data.get("system_state", "Normal"),
            time_of_day=data.get("time_of_day", 12),
            active_escorts=data.get("active_escorts", []),
            present_roles=data.get("present_roles", []),
            guards_distracted=data.get("guards_distracted", False)
        )
