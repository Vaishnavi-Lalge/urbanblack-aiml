from pydantic import BaseModel

class DriverShiftMetrics(BaseModel):
    driver_id: str
    shift_id: str
    total_rides_completed: int = 0
    total_hours_online: float = 0.0
    total_distance_km: float = 0.0
    
    # Target definitions per explicit requirements
    min_rides_required: int = 25
    min_hours_required: float = 12.0
    min_distance_required: float = 135.0
    
class ShiftStatusResponse(BaseModel):
    driver_id: str
    shift_id: str
    requirements_met: bool
    rides_shortfall: int
    hours_shortfall: float
    distance_shortfall: float
    fixed_depot_allocation: str
    center_point: str
