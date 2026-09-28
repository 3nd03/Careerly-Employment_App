def build_skill_gap_prompt(profile: dict, job_description: str = "") -> str:
    target_section = (
        f"JOB DESCRIPTION TO MATCH AGAINST:\n{job_description}"
        if job_description.strip()
        else f"Target role: {profile.get('target_role', 'Not provided')}"
    )

    return f"""You are a career advisor. Analyse the candidate profile below and produce a skill gap report against the target below.

{target_section}

CANDIDATE PROFILE:
- Target role: {profile.get("target_role", "Not provided")}
- Current skills: {profile.get("current_skills", "Not provided")}
- Background: {profile.get("background", "Not provided")}
- Experience: {profile.get("experience", "Not provided")}
- Tools and platforms: {profile.get("tools", "Not provided")}
- Open to learning: {profile.get("open_to_learning", "Not provided")}
- Self-identified gaps: {profile.get("self_gaps", "Not provided")}

Return your response using exactly these section labels, in this order. Do not add extra sections or change the label names. Do not use em dashes anywhere in the response.

MATCH_SCORE: <a single percentage, e.g. 72%>

STRONG_SKILLS:
<bullet list of skills the candidate has that are relevant to the target role>

MISSING_SKILLS:
<bullet list of skills or experience the candidate is lacking for the target role>

NEXT_STEPS:
<numbered list of 2 to 3 specific, actionable steps the candidate should take>
"""
