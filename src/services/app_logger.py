from datetime import datetime, timezone
import json
import streamlit as st


def _append_local_log(record):
    if "local_app_logs" not in st.session_state:
        st.session_state.local_app_logs = []
    st.session_state.local_app_logs.append(record)
    st.session_state.local_app_logs = st.session_state.local_app_logs[-100:]


def log_event(level, event, message, details=None, user_id=None, session_id=None):
    """
    Structured app logging with DB-first and local fallback.
    Tries to write to `app_logs`; if unavailable, stores logs in session_state.
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "event": event,
        "message": message,
        "details": details or {},
        "user_id": user_id,
        "session_id": session_id,
    }

    auth_service = st.session_state.get("auth_service")
    if not auth_service:
        _append_local_log(record)
        return False, "auth_service not available"

    details_json = json.dumps(record["details"], default=str)
    payloads = [
        {
            "level": level,
            "event": event,
            "message": message,
            "details": details_json,
            "user_id": user_id,
            "session_id": session_id,
            "created_at": record["timestamp"],
        },
        {
            "level": level,
            "event": event,
            "message": message,
            "details": details_json,
            "created_at": record["timestamp"],
        },
        {
            "level": level,
            "message": message,
            "created_at": record["timestamp"],
        },
    ]

    last_error = None
    for payload in payloads:
        try:
            auth_service.supabase.table("app_logs").insert(payload).execute()
            return True, None
        except Exception as e:
            last_error = str(e)

    _append_local_log(record)
    return False, last_error
