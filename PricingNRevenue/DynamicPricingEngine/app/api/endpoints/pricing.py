from fastapi import APIRouter
from app.models.schemas import PricingRequest, PricingResponse
from app.services.pricing_calculator import PricingCalculator

router = APIRouter()
calculator = PricingCalculator()

@router.post("/compute-fare", response_model=PricingResponse)
async def compute_fare(request: PricingRequest):
    """
    Computes real-time surge multipliers and final fare estimates for the Urban Black rider app.
    """
    response = await calculator.calculate(request)
    return response
