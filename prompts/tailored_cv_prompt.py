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
- This text is inserted directly under a header that the application already renders separately, showing the candidate's name and contact details (you are not given those details, and do not need them). Because that header already exists elsewhere on the page, your output must begin with the exact heading "PERSONAL STATEMENT" as its first line, with absolutely no name, address, phone number, email, or similar line above it. The single exception: if the EXISTING CV CONTENT above states the candidate's real name or contact details, you may repeat that one real line verbatim as your first line, before PERSONAL STATEMENT.
- Never write a square-bracket placeholder anywhere in the CV, such as [Candidate Name], [Phone Number], [Email Address], [LinkedIn Profile], [Start Date], or [End Date]. This applies everywhere, not just the header: in WORK EXPERIENCE, if the candidate's profile or existing CV gives only a duration (e.g. "12 months", "3-month internship", "Summer 2024") rather than specific calendar dates, state that duration exactly as given. Do not invent a specific year or date range for it either, even an approximate or hedged one (e.g. "Approximately 2023 to 2024") - that is still a guess the candidate did not provide. If a detail genuinely is not available anywhere in the input, the correct response is to omit it or phrase around it, never to insert a placeholder or guess at specifics.
- Plain text only. No markdown, no asterisks, no bullet symbols other than a simple hyphen, no tables, no images.
- Single column layout so an applicant tracking system can parse it cleanly.
- Section headers in capital letters exactly as named above, each on their own line.
- Do not invent qualifications, employers, dates, or achievements the candidate has not provided. Reframe and prioritise what is real, do not fabricate.
- Do not claim experience, familiarity, or proficiency with a specific tool or technology named in the job description unless it also appears in the candidate's profile or existing CV, even if adding it would make the CV a stronger match. If the profile describes a skill as "basic", "limited", or "developing", describe it at that same level; do not round it up to confident or regular use.
- If a profile field is marked "Not provided", write around it rather than commenting on the gap.
- Use UK English spelling throughout.
- Do not use em dashes anywhere in the response.

Return only the finished CV, nothing else.
"""
