import streamlit as st
from auth.session_manager import SessionManager
from components.auth_pages import show_login_page
from components.sidebar import show_sidebar
from components.analysis_form import show_analysis_form
from config.app_config import APP_NAME, APP_TAGLINE, APP_DESCRIPTION, APP_ICON
from services.ai_service import get_chat_response
from services.health_check import run_health_check
from services.app_logger import log_event


st.set_page_config(
    page_title="Health Insights Agent",
    page_icon="🧠",
    layout="wide",
)

# -------------------- MODERN CSS --------------------

st.markdown(
"""
<style>

.main {
    background: linear-gradient(135deg,#0f172a,#1e293b);
}

h1, h2, h3 {
    font-family: "Segoe UI";
}

.block-container {
    padding-top: 2rem;
}

.header-card {
    padding:30px;
    border-radius:15px;
    background: linear-gradient(120deg,#2563eb,#7c3aed);
    color:white;
    box-shadow:0px 6px 20px rgba(0,0,0,0.3);
}

.chat-user {
    background:#1e40af;
    padding:15px;
    border-radius:10px;
    color:white;
    margin-bottom:10px;
}

.chat-ai {
    background:#f1f5f9;
    padding:15px;
    border-radius:10px;
    margin-bottom:10px;
}

.big-button button{
    height:60px;
    font-size:20px;
    border-radius:12px;
}

.welcome-card {
    background:white;
    padding:40px;
    border-radius:16px;
    box-shadow:0px 5px 20px rgba(0,0,0,0.15);
}

.user-greeting {
    text-align:right;
    font-size:18px;
    color:#cbd5f5;
}

</style>
""",
unsafe_allow_html=True
)

# -------------------- HEADER --------------------

def show_header():

    st.markdown(
        f"""
        <div class="header-card">
        <h1>{APP_ICON} {APP_NAME}</h1>
        <p style="font-size:18px">{APP_DESCRIPTION}</p>
        <p style="opacity:0.8">{APP_TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# -------------------- WELCOME SCREEN --------------------

def show_welcome_screen():

    st.markdown("<br>", unsafe_allow_html=True)

    col1,col2,col3 = st.columns([1,2,1])

    with col2:

        st.markdown(
        f"""
        <div class="welcome-card">
        <h2 style="text-align:center;">Welcome to {APP_NAME}</h2>
        <p style="text-align:center;color:gray;">
        Start analyzing your medical reports with AI insights.
        </p>
        </div>
        """,
        unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 Start New Analysis Session",use_container_width=True):

            success, result = SessionManager.create_chat_session()

            if success:
                st.session_state.current_session = result
                st.rerun()

            else:
                st.error(f"Session creation failed: {result}")


# -------------------- CHAT HISTORY --------------------

def show_chat_history():

    success, messages = st.session_state.auth_service.get_session_messages(
        st.session_state.current_session["id"]
    )

    if not success:
        st.error(messages)
        return []

    for msg in messages:

        if msg.get("role") == "system":
            continue

        if msg.get("role") == "user":

            st.markdown(
                f'<div class="chat-user">🧑 {msg.get("content","")}</div>',
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f'<div class="chat-ai">🤖 {msg.get("content","")}</div>',
                unsafe_allow_html=True
            )

    return messages


# -------------------- CHAT INPUT --------------------

def handle_chat_input(messages):

    if prompt := st.chat_input("Ask a follow-up question about the report..."):

        st.markdown(
            f'<div class="chat-user">🧑 {prompt}</div>',
            unsafe_allow_html=True
        )

        saved, error = st.session_state.auth_service.save_chat_message(
            st.session_state.current_session["id"],
            prompt,
            role="user",
        )

        context_text = st.session_state.get("current_report_text", "")

        with st.spinner("Analyzing report..."):

            response = get_chat_response(prompt, context_text, messages)

            st.markdown(
                f'<div class="chat-ai">🤖 {response}</div>',
                unsafe_allow_html=True
            )

            st.session_state.auth_service.save_chat_message(
                st.session_state.current_session["id"],
                response,
                role="assistant",
            )

        st.rerun()


# -------------------- USER GREETING --------------------

def show_user_greeting():

    user = st.session_state.get("user")

    if not user:
        return

    display_name = user.get("name") or user.get("email","User")

    st.markdown(
        f'<div class="user-greeting">Welcome {display_name}</div>',
        unsafe_allow_html=True
    )


# -------------------- MAIN APP --------------------

def main():

    SessionManager.init_session()

    if "health_status" not in st.session_state:

        st.session_state.health_status = run_health_check(
            st.session_state.get("auth_service")
        )

    if not SessionManager.is_authenticated():

        show_login_page()
        return


    show_header()
    show_user_greeting()

    show_sidebar()

    current_session = st.session_state.get("current_session")

    if current_session:

        session_title = current_session.get("title") or "Analysis Session"

        st.subheader(f"🧾 {session_title}")

        messages = show_chat_history()

        if messages:

            with st.expander("📊 Upload New Report / Update Analysis"):

                show_analysis_form()

            handle_chat_input(messages)

        else:

            show_analysis_form()

    else:

        show_welcome_screen()

if __name__ == "__main__":
    main()