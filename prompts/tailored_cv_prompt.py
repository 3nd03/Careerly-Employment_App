def build_tailored_cv_prompt(profile: dict, job_description: str, cv_text: str = "") -> str:
    existing_cv_section = (
        f"""
EXISTING CV CONTENT (base the rewrite on this where it is still accurate):
{cv_text}
"""
        if cv_text.strip()
        else "\nThe candidate has not provided an existing CV. Build the CV entirely from the profile below.\n"
    )

    return f"""You are an expert CV writer. Write a complete CV for the candidate below, tailored specifically to the job description provided.

CANDIDATE PROFILE:
- Target role: {profile.get("target_role", "Not provided")}
- Current skills: {profile.get("current_skills", "Not provided")}
- Background: {profile.get("background", "Not provided")}
- Experience: {profile.get("experience", "Not provided")}
- Tools and platforms: {profile.get("tools", "Not provided")}
- Location: {profile.get("location", "Not provided")}
{existing_cv_section}
JOB DESCRIPTION:
{job_description}

Write the CV with exactly these sections, in this order:
1. PERSONAL STATEMENT: a short, tailored statement connecting the candidate directly to this role and its requirements.
2. KEY SKILLS: skills that match what the job description asks for, drawn from the candidate's real skills and tools.
3. WORK EXPERIENCE: the candidate's real experience, reframed and reordered to highlight what is most relevant to this job.
4. EDUCATION: the candidate's education, inferred from their background where no formal education is stated.
5. ADDITIONAL INFORMATION: anything else relevant, such as tools, platforms, or availability.

Formatting rules:
- Plain text only. No markdown, no asterisks, no bullet symbols other than a simple hyphen, no tables, no images.
- Single column layout so an applicant tracking system can parse it cleanly.
- Section headers in capital letters exactly as named above, each on their own line.
- Do not invent qualifications, employers, dates, or achievements the candidate has not provided. Reframe and prioritise what is real, do not fabricate.
- If a profile field is marked "Not provided", write around it rather than commenting on the gap.
- Use UK English spelling throughout.
- Do not use em dashes anywhere in the response.

Return only the finished CV, nothing else.
"""
