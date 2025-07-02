# state.py

from typing import Optional, TypedDict

# 🎯 Strict type definition for pending deletion
class PendingDelete(TypedDict):
    product_id: str
    confirmed: bool

# ✅ Correctly typed session state
_session_state: dict[str, Optional[PendingDelete]] = {
    "pending_delete": None
}


def set_pending_delete(product_id: str):
    """Store the ID of the product waiting for deletion confirmation."""
    _session_state["pending_delete"] = {
        "product_id": product_id,
        "confirmed": False
    }


def get_pending_delete() -> Optional[PendingDelete]:
    """Return the current pending delete object or None."""
    return _session_state.get("pending_delete")


def confirm_pending_delete():
    """Set the confirmation flag to True."""
    pending = _session_state.get("pending_delete")
    if pending is not None:
        pending["confirmed"] = True


def clear_pending_delete():
    """Clear any pending delete state."""
    _session_state["pending_delete"] = None


def has_pending_delete() -> bool:
    """Check if a delete is pending confirmation."""
    return _session_state.get("pending_delete") is not None
