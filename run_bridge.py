#!/usr/bin/env python3
"""
Mission Control Async Runner for Discord Bridge
Runs a mission in the background and saves proposal to pending approvals.
"""
import os
import sys
import json
import logging

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from framework.crew_builder import run_mission
import discord_bridge

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def execute_and_queue(mission_name: str, inputs: dict) -> dict:
    """Execute mission and queue output for Discord approval."""
    mission_path = os.path.join(PROJECT_ROOT, "missions", mission_name, "mission.yaml")
    if not os.path.exists(mission_path):
        raise FileNotFoundError(f"Mission config not found: {mission_path}")

    logging.info("Starting mission '%s' with inputs: %s", mission_name, inputs)
    result = run_mission(mission_path, inputs=inputs)
    raw_text = str(result)

    session_id = discord_bridge.save_pending_approval(
        mission_name=mission_name,
        drafts=raw_text,
        context_meta=inputs
    )

    formatted_msg = discord_bridge.format_discord_proposal(
        session_id=session_id,
        mission_name=mission_name,
        raw_output=raw_text,
        inputs=inputs
    )

    return {
        "session_id": session_id,
        "raw_result": raw_text,
        "discord_message": formatted_msg
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_bridge.py <mission_name> [inputs_json]")
        sys.exit(1)
    
    m_name = sys.argv[1]
    in_meta = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    res = execute_and_queue(m_name, in_meta)
    print(res["discord_message"])
