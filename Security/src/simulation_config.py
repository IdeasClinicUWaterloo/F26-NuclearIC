class SimulationConstants:
   """
   Centralized configuration for simulation mechanics and cost model.
   Game designers can adjust these to tune difficulty and realism.
   """
   # ========== TRAVERSAL TIME COSTS (minutes) ==========
   BASE_ROOM_TRANSITION_COST = 1  # Minimum time to cross one room
   ZONE_GRADIENT_STEP_UP_COST = 5  # Additional cost per zone security level increase
   # ========== ESCORT DISPATCH DELAYS (minutes) ==========
   # Represents queuing time when security officers are busy
   ESCORT_DELAY_OPTIMAL = 15  # 0-1 concurrent escort assignments
   ESCORT_DELAY_CONGESTION = 35  # 2 concurrent escort assignments  
   ESCORT_DELAY_SATURATION = 65  # 3+ concurrent escort assignments
   # ========== THREAT EVALUATION THRESHOLDS (minutes) ==========
   EMERGENCY_RESPONSE_CRITICAL_THRESHOLD = 20  # If response > threshold, sabotage succeeds
   SOCIAL_ENGINEER_ACCEPTABLE_RESPONSE_TIME = 20  # Threshold for social engineering success
   # ========== OPERATIONAL BASELINES ==========
   # SCALED FOR 13-ROOM LAYOUT: Adjusted from 25 to 180 to represent an optimized secure run
   BASELINE_FACILITY_MISSION_TIME = 180  
   PERFECT_EFFICIENCY_THRESHOLD = 100  # % rating if mission completes <= baseline
   MINIMUM_EFFICIENCY_THRESHOLD = 10  # Floors rating to prevent extreme negatives
   # ========== SYSTEM STATE DEFINITIONS ==========
   VALID_SYSTEM_STATES = ["Normal", "Emergency", "Alert"]
   @classmethod
   def get_escort_delay(cls, concurrent_assignments: int) -> int:
       if concurrent_assignments <= 1:
           return cls.ESCORT_DELAY_OPTIMAL
       elif concurrent_assignments == 2:
           return cls.ESCORT_DELAY_CONGESTION
       else:  # 3+
           return cls.ESCORT_DELAY_SATURATION
   @classmethod
   def calculate_efficiency_rating(cls, actual_mission_time: int) -> int:
       if actual_mission_time == 0:
           return 0
       rating = int((cls.BASELINE_FACILITY_MISSION_TIME / actual_mission_time) * 100)
       return max(cls.MINIMUM_EFFICIENCY_THRESHOLD, min(100, rating))