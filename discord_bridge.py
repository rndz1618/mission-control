#!/usr/bin/env python3
"""
Discord Interactive Bridge for Mission Control
Handles mission triggering, approval queue storage, and Discord broadcasting.
Uses exclusive file locks so concurrent missions (manual + scout cron) cannot
clobber pending_approvals.json.
"""
import datetime
import fcntl
import json
import logging
import os
import sys
import uuid
from typing import Any, Dict, Optional

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


def _locked_read_write(mutator):
    """Exclusive lock around read-modify-write of the approval JSON."""
    ensure_state_dir()
    with open(APPROVAL_FILE, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            try:
                f.seek(0)
                raw = f.read().strip()
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                logger.warning("Corrupt approval file; resetting to empty dict.")
                data = {}
            result = mutator(data)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.truncate()
            return result
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _locked_read() -> dict:
    ensure_state_dir()
    with open(APPROVAL_FILE, "r", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            raw = f.read().strip()
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return {}
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def save_pending_approval(
    mission_name: str,
    drafts: Any,
    context_meta: dict,
    status: str = "PENDING_APPROVAL",
) -> str:
    """Save generated drafts (or a failure payload) awaiting human review."""
    session_id = f"{mission_name}_{uuid.uuid4().hex[:8]}"
    now = datetime.datetime.now().isoformat()

    def mutator(data: dict):
        data[session_id] = {
            "mission_name": mission_name,
            "created_at": now,
            "status": status,
            "context": context_meta,
            "drafts": drafts,
        }
        return session_id

    return _locked_read_write(mutator)


def get_approval(session_id: str) -> Optional[Dict[str, Any]]:
    """Load one approval session by ID."""
    data = _locked_read()
    item = data.get(session_id)
    if not item:
        return None
    return {"id": session_id, **item}


def get_latest_pending_approval() -> Optional[Dict[str, Any]]:
    """Retrieve the most recent pending approval session."""
    data = _locked_read()
    pending = [
        {"id": k, **v}
        for k, v in data.items()
        if v.get("status") == "PENDING_APPROVAL"
    ]
    if not pending:
        return None
    pending.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return pending[0]


def update_approval_status(session_id: str, new_status: str, notes: str = "") -> bool:
    """Update approval status (APPROVED, REVISED, REJECTED, PUBLISHED, FAILED)."""

    def mutator(data: dict):
        if session_id not in data:
            return False
        data[session_id]["status"] = new_status
        data[session_id]["updated_at"] = datetime.datetime.now().isoformat()
        if notes:
            data[session_id]["resolution_notes"] = notes
        return True

    return bool(_locked_read_write(mutator))


def _smart_truncate(text: str, limit: int = 1400) -> str:
    """Truncate at a newline/word boundary so Discord markdown stays intact."""
    if len(text) <= limit:
        return text
    truncated = text[:limit]
    last_nl = truncated.rfind("\n")
    if last_nl > int(limit * 0.7):
        truncated = truncated[:last_nl]
    else:
        last_space = truncated.rfind(" ")
        if last_space > int(limit * 0.7):
            truncated = truncated[:last_space]
    return truncated.rstrip() + "\n... (truncated, full output in approval queue)"


def format_discord_proposal(session_id: str, mission_name: str, raw_output: str, inputs: dict) -> str:
    """Format crew raw output into a Discord review message under 2000 chars."""
    topic = inputs.get("topic", "N/A")
    audience = inputs.get("audience", "General")
    body = _smart_truncate(str(raw_output), 1400)

    lines = [
        "🚀 **[MISSION CONTROL] Draft Konten Siap Review**",
        f"> **Misi:** `{mission_name}` | **Topik:** *{topic}* | **Audiens:** *{audience}*",
        f"> **Approval ID:** `{session_id}`",
        "",
        "**Hasil Draft & Editorial Review:**",
        "```markdown",
        body,
        "```",
        "",
        "👉 **Instruksi Tindakan:**",
        "• Balas: `approve <id>` untuk rilis publikasi.",
        "• Balas: `revisi <catatan>` untuk minta revisi konten.",
        "• Balas: `reject <id>` untuk batalkan misi.",
    ]
    return "\n".join(lines)


def format_discord_failure(session_id: str, mission_name: str, error: str, inputs: dict) -> str:
    """Format a failed mission so Discord still gets an actionable message."""
    topic = inputs.get("topic", "N/A")
    snippet = _smart_truncate(str(error), 800)
    return "\n".join([
        "❌ **[MISSION CONTROL] Misi Gagal**",
        f"> **Misi:** `{mission_name}` | **Topik:** *{topic}*",
        f"> **Approval ID:** `{session_id}` | **Status:** `FAILED`",
        "",
        "```",
        snippet,
        "```",
        "Cek log runner atau jalankan ulang. Full error tersimpan di approval queue.",
    ])


if __name__ == "__main__":
    ensure_state_dir()
    print(f"Discord Bridge initialized at: {PROJECT_ROOT}")
