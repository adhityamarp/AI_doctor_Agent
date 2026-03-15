import streamlit as st


def _check(name, ok, detail):
    return {"name": name, "ok": bool(ok), "detail": detail}


def _probe_table(auth_service, table_name):
    try:
        auth_service.supabase.table(table_name).select("*").limit(1).execute()
        return _check(f"table:{table_name}", True, "reachable")
    except Exception as e:
        return _check(f"table:{table_name}", False, str(e))


def _probe_column(auth_service, table_name, column_name):
    try:
        auth_service.supabase.table(table_name).select(column_name).limit(1).execute()
        return True, None
    except Exception as e:
        return False, str(e)


def run_health_check(auth_service=None):
    checks = []
    warnings = []

    required_secrets = ["SUPABASE_URL", "SUPABASE_KEY", "GROQ_API_KEY"]
    for key in required_secrets:
        checks.append(_check(f"secret:{key}", key in st.secrets, "present" if key in st.secrets else "missing"))

    auth_service = auth_service or st.session_state.get("auth_service")
    if not auth_service:
        checks.append(_check("auth_service", False, "not initialized"))
        return {
            "ok": False,
            "checks": checks,
            "warnings": warnings,
        }

    checks.append(_check("auth_service", True, "initialized"))
    checks.append(_probe_table(auth_service, "users"))
    checks.append(_probe_table(auth_service, "chat_sessions"))
    checks.append(_probe_table(auth_service, "chat_messages"))

    ok_title, err_title = _probe_column(auth_service, "chat_sessions", "title")
    if ok_title:
        checks.append(_check("column:chat_sessions.title", True, "present"))
    else:
        checks.append(_check("column:chat_sessions.title", False, "missing"))
        warnings.append("chat_sessions.title missing; using generated fallback titles.")

    message_columns = ["content", "message", "text", "body"]
    found_msg_col = None
    probe_errors = []
    for col in message_columns:
        ok_col, err_col = _probe_column(auth_service, "chat_messages", col)
        if ok_col:
            found_msg_col = col
            break
        probe_errors.append(err_col)

    if found_msg_col:
        checks.append(_check("column:chat_messages.text", True, f"using '{found_msg_col}'"))
    else:
        checks.append(_check("column:chat_messages.text", False, "none of content/message/text/body found"))
        warnings.append("chat_messages has no supported text column. Add one of: content, message, text, body.")
        if probe_errors:
            warnings.append(f"latest probe error: {probe_errors[-1]}")

    overall_ok = all(c["ok"] for c in checks if not c["name"].startswith("column:chat_sessions.title"))
    return {
        "ok": overall_ok,
        "checks": checks,
        "warnings": warnings,
    }
