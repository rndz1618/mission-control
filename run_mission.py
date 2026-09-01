#!/usr/bin/env python3
"""
Mission Control - Entry Point
Run a CrewAI mission defined in missions/<mission_name>/mission.yaml
Supports dynamic CLI inputs via --input key=value or -i key=value

Usage:
    python run_mission.py <mission_name> [--input key=value ...]
    
Examples:
    python run_mission.py arah_media
    python run_mission.py arah_media --input topic="AI Coding Agents" --input audience="Developers"
"""
import sys
import os
import argparse
import json

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

# Activate virtual environment's python if running with system python
venv_python = os.path.join(project_root, ".venv", "bin", "python")
if os.path.exists(venv_python) and sys.executable != venv_python:
    os.execv(venv_python, [venv_python] + sys.argv)

from framework.crew_builder import run_mission, load_mission


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a Mission Control CrewAI Mission.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "mission_name",
        nargs="?",
        help="Name of the mission folder under missions/ (e.g. arah_media)",
    )
    parser.add_argument(
        "-i", "--input",
        action="append",
        dest="inputs",
        metavar="KEY=VALUE",
        help="Dynamic input variables passed into tasks (e.g. -i topic='AI Agents' -i audience='Tech')",
    )
    parser.add_argument(
        "--inputs-json",
        dest="inputs_json",
        metavar="JSON_STRING",
        help="Pass dynamic inputs as a raw JSON string (e.g. --inputs-json '{\"topic\": \"AI\"}')",
    )
    return parser.parse_args()


def get_available_missions():
    missions_dir = os.path.join(project_root, "missions")
    available = []
    if os.path.exists(missions_dir):
        for item in sorted(os.listdir(missions_dir)):
            if os.path.exists(os.path.join(missions_dir, item, "mission.yaml")):
                available.append(item)
    return available


def parse_inputs(args) -> dict:
    inputs = {}
    if args.inputs_json:
        try:
            inputs.update(json.loads(args.inputs_json))
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse --inputs-json: {e}")

    if args.inputs:
        for item in args.inputs:
            if "=" in item:
                k, v = item.split("=", 1)
                inputs[k.strip()] = v.strip()
            else:
                print(f"Warning: Ignoring malformed input '{item}'. Expected format: key=value")
    return inputs


def main():
    args = parse_args()

    if not args.mission_name:
        print("Usage: python run_mission.py <mission_name> [options]\n")
        print("Available missions:")
        for m in get_available_missions():
            print(f"  - {m}")
        print("\nOptions:")
        print("  -i, --input KEY=VALUE     Pass dynamic input variable")
        print("  --inputs-json JSON_STR    Pass JSON dictionary of inputs")
        sys.exit(1)

    mission_name = args.mission_name
    mission_path = os.path.join(project_root, "missions", mission_name, "mission.yaml")

    if not os.path.exists(mission_path):
        print(f"Error: Mission '{mission_name}' not found at {mission_path}")
        available = get_available_missions()
        if available:
            print(f"Available missions: {', '.join(available)}")
        sys.exit(1)

    inputs = parse_inputs(args)

    print("=" * 60)
    print(f"MISSION CONTROL - Running: {mission_name}")
    print("=" * 60)

    # Load and display mission info
    mission = load_mission(mission_path)
    goal = mission.get('mission', {}).get('overall_goal', 'N/A').strip()
    print(f"Goal: {goal[:80]}..." if len(goal) > 80 else f"Goal: {goal}")
    print(f"Agents: {len(mission.get('agents', []))}")
    print(f"Tasks: {len(mission.get('tasks', []))}")
    print(f"Process: {mission.get('process', 'sequential')}")
    if inputs:
        print(f"Dynamic Inputs: {json.dumps(inputs, indent=2)}")
    print("=" * 60)

    # Run the mission
    try:
        result = run_mission(mission_path, inputs=inputs)
        print(f"\n{'=' * 60}")
        print("MISSION COMPLETED SUCCESSFULLY")
        print(f"{'=' * 60}")
        print(result)
    except Exception as e:
        print(f"\n{'=' * 60}")
        print(f"MISSION FAILED: {str(e)}")
        print(f"{'=' * 60}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
