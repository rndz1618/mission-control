#!/usr/bin/env python3
"""
Discord Interactive Bridge for Mission Control
Handles mission triggering, approval queue storage, and Discord broadcasting.
"""
import os
import sys
import json
import logging
import datetime
from typing import Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

logger = logging.getLogger("discord_bridge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

STATE_DIR = os.path.join(PROJECT_ROOT, "work")
APPROVAL_FILE = os.path.join(STATE_DIR, "pending_approvals.json")


def ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)
    if not os.path.exists(APPROVAL_FILE):
        with open(APPROVAL_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def save_pending_approval(mission_name: str, drafts: Any, context_meta: dict) -> str:
    """Save generated drafts awaiting human review in Discord."""
    ensure_state_dir()
    with open(APPROVAL_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    session_id = f"{mission_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    data[session_id] = {
        "mission_name": mission_name,
        "created_at": datetime.datetime.now().isoformat(),
        "status": "PENDING_APPROVAL",
        "context": context_meta,
        "drafts": drafts
    }

    with open(APPROVAL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return session_id


def get_approval(session_id: str) -> Optional[Dict[str, Any]]:
    """Load one approval session by ID."""
    ensure_state_dir()
    with open(APPROVAL_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    item = data.get(session_id)
    if not item:
        return None
    return {"id": session_id, **item}


def get_latest_pending_approval() -> Optional[Dict[str, Any]]:
    """Retrieve the most recent pending approval session."""
    ensure_state_dir()
    with open(APPROVAL_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    pending = [
        {"id": k, **v} for k, v in data.items() 
        if v.get("status") == "PENDING_APPROVAL"
    ]
    if not pending:
        return None
    pending.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return pending[0]


def update_approval_status(session_id: str, new_status: str, notes: str = "") -> bool:
    """Update approval status (APPROVED, REVISED, REJECTED, PUBLISHED)."""
    ensure_state_dir()
    with open(APPROVAL_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if session_id in data:
        data[session_id]["status"] = new_status
        data[session_id]["updated_at"] = datetime.datetime.now().isoformat()
        if notes:
            data[session_id]["resolution_notes"] = notes
        with open(APPROVAL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    return False


def format_discord_proposal(session_id: str, mission_name: str, raw_output: str, inputs: dict) -> str:
    """Format crew raw output into clean human-friendly Discord review message."""
    topic = inputs.get("topic", "N/A")
    audience = inputs.get("audience", "General")
    
    lines = [
        f"🚀 **[MISSION CONTROL] Draft Konten Siap Review**",
        f"> **Misi:** `{mission_name}` | **Topik:** *{topic}* | **Audiens:** *{audience}*",
        f"> **Approval ID:** `{session_id}`",
        "",
        "**Hasil Draft & Editorial Review:**",
        "```markdown",
        raw_output[:1400] + ("..." if len(raw_output) > 1400 else ""),
        "```",
        "",
        "👉 **Instruksi Tindakan:**",
        "• Balas: `approve <id>` untuk rilis publikasi.",
        "• Balas: `revisi <catatan>` untuk minta revisi konten.",
        "• Balas: `reject <id>` untuk batalkan misi."
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    ensure_state_dir()
    print(f"Discord Bridge initialized at: {PROJECT_ROOT}")
