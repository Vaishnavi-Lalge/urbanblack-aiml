from datetime import datetime, timedelta, timezone
from app.models.schemas import PricingRequest, PricingResponse, FareBreakdown
from app.services.rule_based_surge import get_rule_based_surge_multiplier
from app.services.ml_surge_predictor import ml_predictor

class PricingCalculator:
    def __init__(self):
        self.platform_fee_percentage = 0.05
        self.gst_percentage = 0.05
    
    async def calculate(self, request: PricingRequest) -> PricingResponse:
        # Base Fare Rule: ₹55 for 1.5 km
        base_fare = 55.0
        
        # Additional charge: ₹25 per km 
        extra_distance = max(0.0, request.estimated_distance_km - 1.5)
        distance_charge = extra_distance * 25.0
        
        # Waiting charges: First 5 minutes free, then ₹2 per minute
        chargeable_waiting_time = max(0, request.waiting_time_minutes - 5)
        waiting_charge = chargeable_waiting_time * 2.0
        
        running_subtotal = base_fare + distance_charge + waiting_charge
        
        # Night charges: 25% extra
        is_night = request.is_night_trip or request.hour_of_day < 6 or request.hour_of_day >= 22
        night_surcharge = running_subtotal * 0.25 if is_night else 0.0
        
        # Weather surge: 10–20% depending on conditions.
        weather_surcharge = 0.0
        if request.rainfall_mm_per_hour > 10.0:
            weather_surcharge = running_subtotal * 0.20
        elif request.rainfall_mm_per_hour > 2.0:
            weather_surcharge = running_subtotal * 0.10
            
        operational_subtotal = running_subtotal + night_surcharge + weather_surcharge

        # Dynamic Demand Surge Multiplier (ML model or Rule-based fallback)
        if ml_predictor.model is not None:
            surge_multiplier = ml_predictor.predict_surge(request)
            if surge_multiplier < 1.2: surge_tier = "normal"
            elif surge_multiplier < 1.6: surge_tier = "mild"
            elif surge_multiplier < 2.2: surge_tier = "moderate"
            elif surge_multiplier < 2.5: surge_tier = "peak"
            else: surge_tier = "capped"
        else:
            surge_multiplier, surge_tier = get_rule_based_surge_multiplier(request.zone_demand_supply_ratio)
            
        is_surge_capped = surge_multiplier >= 2.5
        
        # Calculate amount added strictly by demand surge
        demand_surge_amount = operational_subtotal * max(0.0, surge_multiplier - 1.0)
        
        pre_fee_total = operational_subtotal + demand_surge_amount
        
        # Platform Fee
        platform_fee = pre_fee_total * self.platform_fee_percentage
        
        # GST 5% on everything except toll
        taxable_amount = pre_fee_total + platform_fee
        gst_amount = taxable_amount * self.gst_percentage
        
        # Final Fare
        final_fare = taxable_amount + gst_amount + request.toll_cost_estimate
        
        # Breakdown
        breakdown = FareBreakdown(
            base_fare=round(base_fare, 2),
            distance_charge=round(distance_charge, 2),
            waiting_charge=round(waiting_charge, 2),
            night_surcharge=round(night_surcharge, 2),
            weather_surcharge=round(weather_surcharge, 2),
            demand_surge_amount=round(demand_surge_amount, 2),
            toll_component=round(request.toll_cost_estimate, 2),
            platform_fee=round(platform_fee, 2),
            gst_amount=round(gst_amount, 2)
        )
        
        banner_text = "Standard fare"
        if surge_tier == "mild": banner_text = "High demand"
        elif surge_tier == "moderate": banner_text = "Very high demand"
        elif surge_tier in ["peak", "capped"]: banner_text = "Peak surge active"

        return PricingResponse(
            request_id=request.request_id,
            surge_multiplier=round(surge_multiplier, 2),
            surge_tier=surge_tier,
            final_fare=round(final_fare, 2),
            fare_breakdown=breakdown,
            currency="INR",
            fare_valid_until=datetime.now(timezone.utc) + timedelta(minutes=2),
            surge_banner_text=banner_text,
            is_surge_capped=is_surge_capped
        )
