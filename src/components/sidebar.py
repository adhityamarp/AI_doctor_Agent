import streamlit as st
from auth.session_manager import SessionManager
from config.app_config import ANALYSIS_DAILY_LIMIT
from services.health_check import run_health_check


def show_sidebar():
    with st.sidebar:
        st.title("Chat Sessions")

        if st.button("+ New Analysis Session", use_container_width=True):
            if st.session_state.user and "id" in st.session_state.user:
                success, result = SessionManager.create_chat_session()
                if success:
                    st.session_state.current_session = result
                    st.rerun()
                else:
                    st.error(f"Failed to create session: {result}")
            else:
                st.error("Please log in again")
                SessionManager.logout()
                st.rerun()

        if "analysis_count" not in st.session_state:
            st.session_state.analysis_count = 0

        remaining = ANALYSIS_DAILY_LIMIT - st.session_state.analysis_count
        st.markdown(
            f"""
            <div style='
                padding: 0.5rem;
                border-radius: 0.5rem;
                background: rgba(100, 181, 246, 0.1);
                margin: 0.5rem 0;
                text-align: center;
                font-size: 0.9em;
            '>
                <p style='margin: 0; color: #666;'>Daily Analysis Limit</p>
                <p style='
                    margin: 0.2rem 0 0 0;
                    color: {"#1976D2" if remaining > 3 else "#FF4B4B"};
                    font-weight: 500;
                '>
                    {remaining}/{ANALYSIS_DAILY_LIMIT} remaining
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        show_session_list()

        with st.expander("System Health", expanded=False):
            if st.button("Run Health Check", use_container_width=True):
                st.session_state.health_status = run_health_check(
                    st.session_state.get("auth_service")
                )
                st.rerun()

            health = st.session_state.get("health_status")
            if health:
                st.write(f"Overall: {'OK' if health.get('ok') else 'Needs Attention'}")
                for check in health.get("checks", []):
                    prefix = "PASS" if check.get("ok") else "FAIL"
                    st.caption(f"{prefix} {check.get('name')}: {check.get('detail')}")
                for warn in health.get("warnings", []):
                    st.warning(warn)
            else:
                st.info("Health check has not run yet.")

            local_logs = st.session_state.get("local_app_logs", [])
            if local_logs:
                st.caption("Recent Local Logs")
                for entry in local_logs[-5:]:
                    st.caption(f"{entry.get('timestamp')} | {entry.get('level')} | {entry.get('event')}")

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            SessionManager.logout()
            st.rerun()

        


def show_session_list():
    if st.session_state.user and "id" in st.session_state.user:
        success, sessions = SessionManager.get_user_sessions()
        if success:
            if sessions:
                st.subheader("Previous Sessions")
                render_session_list(sessions)
            else:
                st.info("No previous sessions")


def render_session_list(sessions):
    if "delete_confirmation" not in st.session_state:
        st.session_state.delete_confirmation = None

    for session in sessions:
        render_session_item(session)


def render_session_item(session):
    if not session or not isinstance(session, dict) or "id" not in session:
        return

    session_id = session["id"]
    session_title = session.get("title") or f"Session {str(session_id)[:8]}"
    current_session = st.session_state.get("current_session", {})
    current_session_id = (
        current_session.get("id") if isinstance(current_session, dict) else None
    )

    with st.container():
        title_col, delete_col = st.columns([4, 1])

        with title_col:
            if st.button(
                session_title, key=f"session_{session_id}", use_container_width=True
            ):
                st.session_state.current_session = session
                st.rerun()

        with delete_col:
            if st.button("Delete", key=f"delete_{session_id}", help="Delete this session"):
                if st.session_state.delete_confirmation == session_id:
                    st.session_state.delete_confirmation = None
                else:
                    st.session_state.delete_confirmation = session_id
                st.rerun()

        if st.session_state.delete_confirmation == session_id:
            st.warning("Delete above session?")
            left_btn, right_btn = st.columns(2)
            with left_btn:
                if st.button(
                    "Yes",
                    key=f"confirm_delete_{session_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    handle_delete_confirmation(session_id, current_session_id)
            with right_btn:
                if st.button(
                    "No",
                    key=f"cancel_delete_{session_id}",
                    use_container_width=True,
                ):
                    st.session_state.delete_confirmation = None
                    st.rerun()


def handle_delete_confirmation(session_id, current_session_id):
    if not session_id:
        st.error("Invalid session")
        return

    success, error = SessionManager.delete_session(session_id)
    if success:
        st.session_state.delete_confirmation = None
        if current_session_id and current_session_id == session_id:
            st.session_state.current_session = None
        st.rerun()
    else:
        st.error(f"Failed to delete: {error}")
