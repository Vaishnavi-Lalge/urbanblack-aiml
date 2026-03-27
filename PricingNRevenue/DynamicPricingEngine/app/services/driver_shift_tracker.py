from app.models.driver_schemas import DriverShiftMetrics, ShiftStatusResponse

def evaluate_driver_shift(metrics: DriverShiftMetrics, allocated_depot: str, center_point: str) -> ShiftStatusResponse:
    """
    Evaluates whether a driver has met the shift requirements:
    - Minimum 25 rides
    - 12 hours working time
    - 135 km minimum distance
    """
    rides_short = max(0, metrics.min_rides_required - metrics.total_rides_completed)
    hours_short = round(max(0.0, metrics.min_hours_required - metrics.total_hours_online), 2)
    dist_short = round(max(0.0, metrics.min_distance_required - metrics.total_distance_km), 2)
    
    met_all = (rides_short == 0 and hours_short == 0 and dist_short == 0)
    
    return ShiftStatusResponse(
        driver_id=metrics.driver_id,
        shift_id=metrics.shift_id,
        requirements_met=met_all,
        rides_shortfall=rides_short,
        hours_shortfall=hours_short,
        distance_shortfall=dist_short,
        fixed_depot_allocation=allocated_depot,
        center_point=center_point
    )
