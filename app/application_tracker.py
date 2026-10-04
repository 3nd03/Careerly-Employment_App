import streamlit as st
from database.db_client import save_application, get_applications, update_application_status

STATUS_OPTIONS = ["Applied", "Interview", "Offer", "Rejected"]


def run_application_tracker() -> None:
    st.header("Application Tracker")

    profile = st.session_state.get("profile")
    if not profile:
        st.warning("Complete onboarding first before tracking applications.")
        return

    profile_id = st.session_state.profile_id

    with st.form("add_application_form", clear_on_submit=True):
        st.subheader("Add an application")
        company = st.text_input("Company")
        role = st.text_input("Role")
        date_applied = st.date_input("Date applied")
        status = st.selectbox("Status", STATUS_OPTIONS)
        submitted = st.form_submit_button("Add application")

    if submitted:
        if not company.strip() or not role.strip():
            st.warning("Enter a company and role before adding.")
        else:
            try:
                save_application(profile_id, company.strip(), role.strip(), date_applied, status)
                st.success("Application added.")
            except Exception:
                st.warning("Could not save to database, continuing without persistence")

    st.divider()
    st.subheader("Your applications")

    try:
        applications = get_applications(profile_id)
    except Exception:
        applications = []
        st.warning("Could not load applications from the database.")

    if not applications:
        st.info("No applications tracked yet. Add one above.")
        return

    header = st.columns([2, 2, 2, 2])
    header[0].markdown("**Company**")
    header[1].markdown("**Role**")
    header[2].markdown("**Date applied**")
    header[3].markdown("**Status**")

    for application in applications:
        cols = st.columns([2, 2, 2, 2])
        cols[0].write(application["company"])
        cols[1].write(application["role"])
        cols[2].write(str(application["date_applied"]))
        new_status = cols[3].selectbox(
            "Status",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(application["status"]),
            key=f"status_{application['id']}",
            label_visibility="collapsed",
        )
        if new_status != application["status"]:
            try:
                update_application_status(application["id"], profile_id, new_status)
                st.rerun()
            except Exception:
                st.warning("Could not update status in the database.")
