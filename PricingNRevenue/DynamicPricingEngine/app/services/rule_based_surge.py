def get_rule_based_surge_multiplier(demand_supply_ratio: float) -> tuple[float, str]:
    """
    Maps dynamic demand-supply ratio to predefined surge tiers and multipliers.
    Tier             Demand/Supply Ratio       Surge Multiplier
    Normal           < 1.2                     1.0x
    Mild Surge       1.2 - 1.6                 1.1x - 1.3x
    Moderate Surge   1.6 - 2.2                 1.3x - 1.8x
    Peak Surge       2.2 - 3.0                 1.8x - 2.5x
    Hard Cap         > 3.0                     2.5x (max)
    """
    if demand_supply_ratio < 1.2:
        return 1.0, "normal"
    elif 1.2 <= demand_supply_ratio < 1.6:
        # Interpolate between 1.1 and 1.3
        progress = (demand_supply_ratio - 1.2) / (1.6 - 1.2)
        multiplier = 1.1 + (progress * 0.2)
        return multiplier, "mild"
    elif 1.6 <= demand_supply_ratio < 2.2:
        progress = (demand_supply_ratio - 1.6) / (2.2 - 1.6)
        multiplier = 1.3 + (progress * 0.5)
        return multiplier, "moderate"
    elif 2.2 <= demand_supply_ratio <= 3.0:
        progress = (demand_supply_ratio - 2.2) / (3.0 - 2.2)
        multiplier = 1.8 + (progress * 0.7)
        return multiplier, "peak"
    else:
        return 2.5, "capped"
