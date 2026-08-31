#!/usr/bin/env python3
"""Run the Project 13 sample NYC taxi audit and prediction pipeline."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.platform import run_pipeline, infer_duration


def main() -> None:
    parser = argparse.ArgumentParser(description="NYC taxi CRISP-DM audit platform")
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=255)
    parser.add_argument("--infer", action="store_true", help="predict one trip using saved model")
    parser.add_argument("--pickup-hour", type=int, default=17)
    parser.add_argument("--weekday", type=int, default=4, help="Monday=0 ... Sunday=6")
    parser.add_argument("--distance-miles", type=float, default=3.2)
    parser.add_argument("--passengers", type=int, default=2)
    parser.add_argument("--pickup-zone", type=int, default=1)
    parser.add_argument("--dropoff-zone", type=int, default=2)
    args = parser.parse_args()
    if args.infer:
        result = infer_duration(args.output, args.pickup_hour, args.weekday, args.distance_miles,
                                args.passengers, args.pickup_zone, args.dropoff_zone)
        print(json.dumps(result, indent=2))
    else:
        result = run_pipeline(args.output, rows=args.rows, seed=args.seed, command=sys.argv)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
