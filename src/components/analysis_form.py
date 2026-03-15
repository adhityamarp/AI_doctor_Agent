import streamlit as st
from config.prompts import SPECIALIST_PROMPTS
from utils.pdf_extractor import extract_text_from_pdf
from config.sample_data import SAMPLE_REPORT
from config.app_config import MAX_UPLOAD_SIZE_MB
from services.app_logger import log_event


def show_analysis_form():
    # Initialize report source in session state for new sessions
    if (
        "current_session" in st.session_state
        and "report_source" not in st.session_state
    ):
        st.session_state.report_source = "Upload PDF"

    report_source = st.radio(
        "Choose report source",
        ["Upload PDF", "Use Sample PDF"],
        index=0 if st.session_state.get("report_source") == "Upload PDF" else 1,
        horizontal=True,
        key="report_source",
    )

    pdf_contents = get_report_contents(report_source)

    if pdf_contents:  # Only show form if we have report content
        render_patient_form(pdf_contents)


def get_report_contents(report_source):
    if report_source == "Upload PDF":
        uploaded_file = st.file_uploader(
            f"Upload blood report PDF (Max {MAX_UPLOAD_SIZE_MB}MB)",
            type=["pdf"],
            help=f"Maximum file size: {MAX_UPLOAD_SIZE_MB}MB. Only PDF files containing medical reports are supported",
        )
        if uploaded_file:
            # Check file size before processing
            file_size_mb = uploaded_file.size / (1024 * 1024)  # Convert to MB
            if file_size_mb > MAX_UPLOAD_SIZE_MB:
                st.error(
                    f"File size ({file_size_mb:.1f}MB) exceeds the {MAX_UPLOAD_SIZE_MB}MB limit."
                )
                return None

            if uploaded_file.type != "application/pdf":
                st.error("Please upload a valid PDF file.")
                return None

            pdf_contents = extract_text_from_pdf(uploaded_file)
            if isinstance(pdf_contents, str) and (
                pdf_contents.startswith(
                    ("File size exceeds", "Invalid file type", "Error validating")
                )
                or pdf_contents.startswith("The uploaded file")
                or "error" in pdf_contents.lower()
            ):
                st.error(pdf_contents)
                return None
            with st.expander("View Extracted Report"):
                st.text(pdf_contents)
            return pdf_contents
    else:
        with st.expander("View Sample Report"):
            st.text(SAMPLE_REPORT)
        return SAMPLE_REPORT
    return None


def render_patient_form(pdf_contents):
    with st.form("analysis_form"):
        patient_name = st.text_input("Patient Name")
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=0, max_value=120)
        with col2:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])

        if st.form_submit_button("Analyze Report"):
            handle_form_submission(patient_name, age, gender, pdf_contents)


def handle_form_submission(patient_name, age, gender, pdf_contents):
    if not all([patient_name, age, gender]):
        st.error("Please fill in all fields")
        return

    # Check rate limit first, outside of spinner
    from services.ai_service import generate_analysis

    can_analyze, error_msg = generate_analysis(None, None, check_only=True)
    if not can_analyze:
        st.error(error_msg)
        log_event(
            "warning",
            "analysis_rate_limited",
            "Analysis blocked by rate limit",
            {"error": error_msg},
            user_id=st.session_state.get("user", {}).get("id"),
            session_id=st.session_state.get("current_session", {}).get("id"),
        )
        return

    with st.spinner("Analyzing report..."):
        # Save report content for follow-up chat (session state for immediate use)
        st.session_state.current_report_text = pdf_contents

        # Save user message and proceed with analysis
        _, user_save_error = st.session_state.auth_service.save_chat_message(
            st.session_state.current_session["id"],
            f"Analyzing report for patient: {patient_name}",
        )
        if user_save_error:
            st.warning(f"Could not save user message: {user_save_error}")
            log_event(
                "warning",
                "analysis_user_message_save_failed",
                "Could not save analysis trigger user message",
                {"error": user_save_error},
                user_id=st.session_state.get("user", {}).get("id"),
                session_id=st.session_state.get("current_session", {}).get("id"),
            )

        # Generate analysis
        result = generate_analysis(
            {
                "patient_name": patient_name,
                "age": age,
                "gender": gender,
                "report": pdf_contents,
            },
            SPECIALIST_PROMPTS["comprehensive_analyst"],
        )

        if result.get("success"):
            # Store report text as a system message for persistence
            # This allows us to retrieve it later even after page refresh
            report_metadata = f"__REPORT_TEXT__\n{pdf_contents}\n__END_REPORT_TEXT__"
            _, report_save_error = st.session_state.auth_service.save_chat_message(
                st.session_state.current_session["id"], report_metadata, role="system"
            )

            # Add model used information if available
            content = result["content"]
            if "model_used" in result:
                model_info = f"\n\n*Analysis generated using {result['model_used']}*"
                content += model_info

            saved, assistant_save_error = st.session_state.auth_service.save_chat_message(
                st.session_state.current_session["id"], content, role="assistant"
            )

            if saved and not report_save_error:
                st.rerun()
                return

            st.warning(
                "Analysis was generated but could not be fully saved to chat history."
            )
            if report_save_error:
                st.warning(f"Report metadata save failed: {report_save_error}")
                log_event(
                    "warning",
                    "report_metadata_save_failed",
                    "Could not save report metadata",
                    {"error": report_save_error},
                    user_id=st.session_state.get("user", {}).get("id"),
                    session_id=st.session_state.get("current_session", {}).get("id"),
                )
            if assistant_save_error:
                st.warning(f"Analysis save failed: {assistant_save_error}")
                log_event(
                    "warning",
                    "analysis_message_save_failed",
                    "Could not save assistant analysis message",
                    {"error": assistant_save_error},
                    user_id=st.session_state.get("user", {}).get("id"),
                    session_id=st.session_state.get("current_session", {}).get("id"),
                )
            st.markdown(content)
        else:
            error_text = result.get("error", "Analysis failed with an unknown error.")
            st.error(error_text)
            log_event(
                "error",
                "analysis_generation_failed",
                "AI analysis generation failed",
                {"error": error_text},
                user_id=st.session_state.get("user", {}).get("id"),
                session_id=st.session_state.get("current_session", {}).get("id"),
            )
