from fastapi import APIRouter
from app.models.driver_schemas import DriverShiftMetrics, ShiftStatusResponse
from app.services.driver_shift_tracker import evaluate_driver_shift

router = APIRouter()

@router.post("/driver/shift-status", response_model=ShiftStatusResponse, tags=["driver-incentives"])
async def check_driver_shift(metrics: DriverShiftMetrics, depot: str = "Central Depot", center_point: str = "Downtown"):
    """
    Evaluates driver shift metrics against constraints (25 rides, 12 hrs, 135km).
    """
    return evaluate_driver_shift(metrics, depot, center_point)
