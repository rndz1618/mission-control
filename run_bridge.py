#!/usr/bin/env python3
"""
Mission Control Async Runner for Discord Bridge
Runs a mission in the background and saves proposal (or failure) to pending approvals.
"""
import json
import logging
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from framework.crew_builder import run_mission
import discord_bridge

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def execute_and_queue(mission_name: str, inputs: dict) -> dict:
    """Execute mission and queue output for Discord approval.

    On failure, persist status FAILED so Discord still receives an Approval ID
    instead of a raw traceback.
    """
    mission_path = os.path.join(PROJECT_ROOT, "missions", mission_name, "mission.yaml")
    if not os.path.exists(mission_path):
        raise FileNotFoundError(f"Mission config not found: {mission_path}")

    logging.info("Starting mission '%s' with inputs: %s", mission_name, inputs)
    os.environ["MISSION_CONTROL_SKIP_HUMAN_INPUT"] = "1"

    try:
        result = run_mission(mission_path, inputs=inputs, skip_human_input=True)
        raw_text = str(result)
        session_id = discord_bridge.save_pending_approval(
            mission_name=mission_name,
            drafts=raw_text,
            context_meta=inputs,
            status="PENDING_APPROVAL",
        )
        formatted_msg = discord_bridge.format_discord_proposal(
            session_id=session_id,
            mission_name=mission_name,
            raw_output=raw_text,
            inputs=inputs,
        )
        return {
            "session_id": session_id,
            "status": "PENDING_APPROVAL",
            "raw_result": raw_text,
            "discord_message": formatted_msg,
        }
    except Exception as e:
        logging.exception("Mission '%s' failed", mission_name)
        err_text = f"{type(e).__name__}: {e}"
        session_id = discord_bridge.save_pending_approval(
            mission_name=mission_name,
            drafts=err_text,
            context_meta=inputs,
            status="FAILED",
        )
        formatted_msg = discord_bridge.format_discord_failure(
            session_id=session_id,
            mission_name=mission_name,
            error=err_text,
            inputs=inputs,
        )
        return {
            "session_id": session_id,
            "status": "FAILED",
            "raw_result": err_text,
            "discord_message": formatted_msg,
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_bridge.py <mission_name> [inputs_json]")
        sys.exit(1)

    m_name = sys.argv[1]
    in_meta = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    res = execute_and_queue(m_name, in_meta)
    print(res["discord_message"])
    if res.get("status") == "FAILED":
        sys.exit(1)
