import streamlit as st
from services.claude_client import call_claude
from prompts.linkedin_prompt import build_linkedin_prompt
from database.db_client import save_linkedin_message
from utils.helpers import render_followup_chat
from utils.linkedin_limit import enforce_limit


def run_linkedin_message() -> None:
    st.header("LinkedIn Message Generator")

    profile = st.session_state.get("profile")
    if not profile:
        st.warning("Complete onboarding first before generating a message.")
        return

    context = st.text_area(
        "Who are you reaching out to? (optional, e.g. hiring manager at a specific company, alumnus in your target field)",
        height=150,
        key="linkedin_context",
    )

    if st.button("Generate message"):
        with st.spinner("Writing your message..."):
            prompt = build_linkedin_prompt(profile, context.strip())
            message_text = enforce_limit(call_claude(prompt), call_claude)
            st.session_state.linkedin_result = message_text
            try:
                save_linkedin_message(st.session_state.profile_id, context.strip(), message_text)
            except Exception:
                st.warning("Could not save to database, continuing without persistence")

    result = st.session_state.get("linkedin_result")
    if result:
        st.divider()
        st.subheader("Your Message")
        st.markdown(result)

        render_followup_chat("linkedin_message", result, profile)
