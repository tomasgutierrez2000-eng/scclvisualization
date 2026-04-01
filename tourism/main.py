#!/usr/bin/env python3
"""Venezuela Transport Logistics - Trip Planning CLI.

Usage:
    python -m tourism.main "Caracas to Maracaibo, 3 days"
    python -m tourism.main --interactive
"""
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tourism.orchestrator import run_pipeline
from tourism.output.heat_map import generate_heat_map


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m tourism.main \"<trip request>\"")
        print("       python -m tourism.main --interactive")
        print()
        print("Examples:")
        print("  python -m tourism.main \"Caracas to Maracaibo, 3 days\"")
        print("  python -m tourism.main \"Valencia to San Cristobal\"")
        print("  python -m tourism.main \"Plan a trip from Barquisimeto to Ciudad Bolivar, 5 days\"")
        sys.exit(1)

    if sys.argv[1] == "--interactive":
        print("Venezuela Transport Logistics Planner")
        print("=" * 40)
        print("Type your trip request (or 'quit' to exit):\n")
        while True:
            try:
                user_input = input("> ")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break
            if user_input.lower() in ("quit", "exit", "q"):
                break
            if not user_input.strip():
                continue
            try:
                result = run_pipeline(user_input)
                # Generate heat map
                map_path = generate_heat_map(
                    result["route_proposal"],
                    result["security_briefing"],
                )
                print(f"\n       Heat map: {map_path}")
            except Exception as e:
                print(f"\nError: {e}")
            print()
    else:
        user_input = " ".join(sys.argv[1:])
        try:
            result = run_pipeline(user_input)
            # Generate heat map
            map_path = generate_heat_map(
                result["route_proposal"],
                result["security_briefing"],
            )
            print(f"\n       Heat map: {map_path}")
        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
