def default_rule_weights() -> dict:
    return {
        "speed_high_threshold": 12.0,
        "speed_high_boost": 0.05,
        "speed_idle_threshold": 2.0,
        "speed_idle_penalty": -0.15,
        "inactive_minutes_threshold": 20.0,
        "inactive_penalty": -0.10,
        "slow_speed_threshold": 6.0,
        "low_ping_threshold": 20,
        "slow_wandering_penalty": -0.08,
        "active_ping_threshold": 50,
        "active_shift_hours_threshold": 6.0,
        "active_driver_boost": 0.05,
    }


def default_decision_config() -> dict:
    return {
        "decision_threshold": 0.55,
        "low_conf": 0.40,
        "high_conf": 0.70,
        "max_adjustment_abs": 0.15,
        "rule_trigger_margin": 0.04,
        "direct_model_margin": 0.06,
        "min_rule_signals": 2,
        "rule_weights": default_rule_weights(),
    }


def clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def is_model_source(source: str) -> bool:
    return source.startswith("model")


def apply_soft_rules(
    row: dict,
    proba: float,
    rule_weights: dict | None = None,
    max_adjustment_abs: float = 0.15,
) -> tuple[float, list[str], float]:
    weights = default_rule_weights()
    if rule_weights:
        weights.update(rule_weights)

    adjustments = []
    total_adjustment = 0.0

    if row["speed_kmh"] > weights["speed_high_threshold"]:
        total_adjustment += weights["speed_high_boost"]
        adjustments.append("speed_high")

    if row["speed_kmh"] < weights["speed_idle_threshold"]:
        total_adjustment += weights["speed_idle_penalty"]
        adjustments.append("speed_idle")

    if row["time_since_last_trip_end_min"] > weights["inactive_minutes_threshold"]:
        total_adjustment += weights["inactive_penalty"]
        adjustments.append("inactive_long")

    if row["speed_kmh"] < weights["slow_speed_threshold"] and row["ping_count"] < weights["low_ping_threshold"]:
        total_adjustment += weights["slow_wandering_penalty"]
        adjustments.append("slow_wandering")

    if (
        row["ping_count"] > weights["active_ping_threshold"]
        and row["driver_shift_hours_elapsed"] < weights["active_shift_hours_threshold"]
    ):
        total_adjustment += weights["active_driver_boost"]
        adjustments.append("active_driver")

    capped_adjustment = max(
        min(float(total_adjustment), float(max_adjustment_abs)),
        -float(max_adjustment_abs),
    )
    adjusted_score = clamp_probability(float(proba) + capped_adjustment)

    return adjusted_score, adjustments, capped_adjustment


def evaluate_decision(row: dict, proba: float, decision_config: dict | None = None) -> dict:
    config = default_decision_config()
    if decision_config:
        config.update({k: v for k, v in decision_config.items() if k != "rule_weights"})
        rule_weights = default_rule_weights()
        rule_weights.update(decision_config.get("rule_weights", {}))
        config["rule_weights"] = rule_weights

    if (
        row.get("speed_kmh") == 0
        and row.get("ping_count", 0) > 50
        and row.get("time_since_last_trip_end_min", 0) < 10
    ):
        return {
            "prediction": 1,
            "source": "rule_waiting_active",
            "decision_score": 1.0,
            "adjustments": [],
            "total_adjustment": 0.0,
        }

    if row.get("speed_kmh", 0) > 80 and row.get("total_distance_km", 0) > 20:
        return {
            "prediction": 1,
            "source": "rule_high_activity",
            "decision_score": 1.0,
            "adjustments": [],
            "total_adjustment": 0.0,
        }

    if proba >= config["high_conf"]:
        return {
            "prediction": 1,
            "source": "model_high_conf_positive",
            "decision_score": clamp_probability(proba),
            "adjustments": [],
            "total_adjustment": 0.0,
        }

    if proba <= config["low_conf"]:
        return {
            "prediction": 0,
            "source": "model_high_conf_negative",
            "decision_score": clamp_probability(proba),
            "adjustments": [],
            "total_adjustment": 0.0,
        }

    distance_from_threshold = abs(float(proba) - float(config["decision_threshold"]))
    direct_model_margin = float(config["direct_model_margin"])
    rule_trigger_margin = float(config["rule_trigger_margin"])

    if rule_trigger_margin >= direct_model_margin:
        raise ValueError("rule_trigger_margin must be smaller than direct_model_margin")

    if distance_from_threshold > direct_model_margin:
        return {
            "prediction": int(proba >= config["decision_threshold"]),
            "source": "model_uncertain_fallback",
            "decision_score": clamp_probability(proba),
            "adjustments": [],
            "total_adjustment": 0.0,
        }

    if distance_from_threshold > rule_trigger_margin:
        return {
            "prediction": int(proba >= config["decision_threshold"]),
            "source": "model_uncertain_fallback",
            "decision_score": clamp_probability(proba),
            "adjustments": [],
            "total_adjustment": 0.0,
        }

    adjusted_score, adjustments, total_adjustment = apply_soft_rules(
        row,
        proba,
        config["rule_weights"],
        config["max_adjustment_abs"],
    )
    if len(adjustments) >= int(config["min_rule_signals"]):
        return {
            "prediction": int(adjusted_score >= config["decision_threshold"]),
            "source": "soft_rule_adjusted",
            "decision_score": adjusted_score,
            "adjustments": adjustments,
            "total_adjustment": total_adjustment,
        }

    return {
        "prediction": int(proba >= config["decision_threshold"]),
        "source": "model_uncertain_fallback",
        "decision_score": clamp_probability(proba),
        "adjustments": [],
        "total_adjustment": 0.0,
    }


def decision_engine(row: dict, proba: float, decision_config: dict | None = None) -> tuple[int, str]:
    decision = evaluate_decision(row, proba, decision_config)
    return decision["prediction"], decision["source"]
