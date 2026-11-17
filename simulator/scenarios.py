"""Repeatable occupancy scenarios for evaluating the simulated facility."""

from datetime import datetime, timedelta
from random import Random

from simulator.simulator import MAX_EVENT_INTERVAL, MIN_EVENT_INTERVAL

SNAPSHOT_MINUTES = 5
DEMO_CAPACITY = 20
MINUTES_PER_WEEK = 7 * 24 * 60


def fast_run(seed: int, snapshots: int, speed: float) -> tuple[list[int], list[int], list[int]]:
    """Reproduce the automatic worker's eligible-bay probabilities and timing."""
    rng = Random(seed)
    occupied = rng.randrange(DEMO_CAPACITY + 1)
    elapsed = 0.0
    arrivals = departures = 0
    readings, arrived, departed = [], [], []
    for slot in range(snapshots):
        while elapsed <= slot * SNAPSHOT_MINUTES * 60:
            if rng.randrange(DEMO_CAPACITY) < occupied:
                occupied -= 1
                departures += 1
            else:
                occupied += 1
                arrivals += 1
            elapsed += rng.uniform(MIN_EVENT_INTERVAL, MAX_EVENT_INTERVAL) / speed
        readings.append(occupied)
        arrived.append(arrivals)
        departed.append(departures)
    return readings, arrived, departed


def seasonal_run(seed: int, start: datetime, weeks: int) -> list[int]:
    """Generate calendar demand and independently sampled vehicle stays."""
    rng = Random(seed)
    departures: list[int] = []
    readings = []
    run_demand = rng.uniform(0.9, 1.1)
    for minute in range(weeks * MINUTES_PER_WEEK):
        timestamp = start + timedelta(minutes=minute)
        departures = [departure for departure in departures if departure > minute]
        hour = timestamp.hour
        if timestamp.weekday() < 5:
            demand = 0.28 if 7 <= hour < 11 else 0.16 if 11 <= hour < 17 else 0.03
        else:
            demand = 0.18 if 10 <= hour < 17 else 0.04
        for _ in range(2):
            if len(departures) < DEMO_CAPACITY and rng.random() < demand * run_demand:
                stay = round(rng.triangular(15, 180, 65))
                departures.append(minute + stay)
        if minute % SNAPSHOT_MINUTES == 0:
            readings.append(len(departures))
    return readings
