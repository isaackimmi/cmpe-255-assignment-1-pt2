"""CLI entry point for the Project 07 experiment."""

from __future__ import annotations

import argparse

from experiment import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Project 07 tabular model comparison")
    parser.add_argument("--output-dir", default="artifacts", help="Directory for leaderboard and metrics")
    parser.add_argument("--no-autogluon", action="store_true", help="Skip the optional AutoGluon run")
    args = parser.parse_args()
    leaderboard = run_experiment(args.output_dir, include_autogluon=not args.no_autogluon)
    print(leaderboard.to_string(index=False))


if __name__ == "__main__":
    main()
