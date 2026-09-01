#!/usr/bin/env python3
"""
Mission Control - Entry Point
Run a CrewAI mission defined in missions/<mission_name>/mission.yaml

Usage:
    python run_mission.py <mission_name>
    
Example:
    python run_mission.py arah_media
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

# Activate virtual environment's python
venv_python = os.path.join(project_root, ".venv", "bin", "python")
if os.path.exists(venv_python) and sys.executable != venv_python:
    # Re-execute with venv python
    os.execv(venv_python, [venv_python] + sys.argv)


from framework.crew_builder import run_mission, load_mission


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_mission.py <mission_name>")
        print("\nAvailable missions:")
        missions_dir = os.path.join(project_root, "missions")
        if os.path.exists(missions_dir):
            for item in sorted(os.listdir(missions_dir)):
                mission_path = os.path.join(missions_dir, item, "mission.yaml")
                if os.path.exists(mission_path):
                    print(f"  - {item}")
        sys.exit(1)
    
    mission_name = sys.argv[1]
    mission_path = os.path.join(project_root, "missions", mission_name, "mission.yaml")
    
    if not os.path.exists(mission_path):
        print(f"Error: Mission '{mission_name}' not found at {mission_path}")
        sys.exit(1)
    
    print(f"=" * 60)
    print(f"MISSION CONTROL - Running: {mission_name}")
    print(f"=" * 60)
    
    # Load and display mission info
    mission = load_mission(mission_path)
    print(f"Goal: {mission.get('mission', {}).get('overall_goal', 'N/A')[:80]}...")
    print(f"Agents: {len(mission.get('agents', []))}")
    print(f"Tasks: {len(mission.get('tasks', []))}")
    print(f"Process: {mission.get('process', 'sequential')}")
    print(f"=" * 60)
    
    # Run the mission
    try:
        result = run_mission(mission_path)
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