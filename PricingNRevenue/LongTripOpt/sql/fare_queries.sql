-- Sample queries for the fare dataset

-- 1. Get all completed rides
SELECT * FROM fare_dataset WHERE ride_status = 'RIDE_COMPLETED';

-- 2. Average fare by trip type
SELECT trip_type, AVG(offered_fare) AS avg_fare, COUNT(*) AS count
FROM fare_dataset
WHERE ride_status = 'RIDE_COMPLETED'
GROUP BY trip_type
ORDER BY avg_fare DESC;

-- 3. Fares by hour of day
SELECT hour_of_day, AVG(offered_fare) AS avg_fare, COUNT(*) AS count
FROM fare_dataset
WHERE ride_status = 'RIDE_COMPLETED'
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- 4. Fares by vehicle type
SELECT vehicle_type, AVG(offered_fare) AS avg_fare, COUNT(*) AS count
FROM fare_dataset
WHERE ride_status = 'RIDE_COMPLETED'
GROUP BY vehicle_type;

-- 5. Longest distance rides
SELECT * FROM fare_dataset
WHERE ride_status = 'RIDE_COMPLETED'
ORDER BY actual_distance_km DESC
LIMIT 10;

-- 6. Peak hour analysis (assuming peak hours 7-10, 17-21)
SELECT
    CASE
        WHEN hour_of_day BETWEEN 7 AND 10 OR hour_of_day BETWEEN 17 AND 21 THEN 'Peak'
        ELSE 'Off-Peak'
    END AS time_period,
    AVG(offered_fare) AS avg_fare,
    COUNT(*) AS count
FROM fare_dataset
WHERE ride_status = 'RIDE_COMPLETED'
GROUP BY time_period;

-- 7. Fare vs distance correlation
SELECT actual_distance_km, offered_fare
FROM fare_dataset
WHERE ride_status = 'RIDE_COMPLETED'
ORDER BY actual_distance_km;