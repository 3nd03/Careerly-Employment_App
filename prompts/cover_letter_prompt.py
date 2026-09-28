TONE_GUIDANCE = {
    "Formal": "Traditional and professional. Measured language, no contractions, conventional business letter register.",
    "Warm": "Friendly and personable while staying professional. Contractions are fine, let some genuine enthusiasm show.",
    "Direct": "Concise and confident. Short sentences, no filler or hedging, straight to the point.",
}


def build_cover_letter_prompt(profile: dict, job_description: str, tone: str = "Formal") -> str:
    tone_instruction = TONE_GUIDANCE.get(tone, TONE_GUIDANCE["Formal"])

    return f"""You are an expert career writer. Write a tailored cover letter in UK English for the candidate below.

CANDIDATE PROFILE:
- Target role: {profile.get("target_role", "Not provided")}
- Current skills: {profile.get("current_skills", "Not provided")}
- Background: {profile.get("background", "Not provided")}
- Experience: {profile.get("experience", "Not provided")}
- Tools and platforms: {profile.get("tools", "Not provided")}
- Timeline: {profile.get("timeline", "Not provided")}

JOB DESCRIPTION:
{job_description}

TONE: {tone} - {tone_instruction}

Instructions:
- Always write the complete cover letter itself. Never ask the candidate for more information, never explain what is missing, never respond with anything other than the finished letter.
- If a profile field is marked "Not provided", write around it using what is available rather than commenting on the gap.
- Write a complete cover letter ready to send. No section labels, no placeholders, no commentary.
- Open with a strong, specific first paragraph that references the role and employer from the job description.
- Reference the candidate's actual skills, background, and experience where relevant.
- Address specific requirements or keywords from the job description directly.
- Write in the tone described above, consistently throughout. Avoid generic phrases and corporate clichés regardless of tone.
- Three to four paragraphs. Concise and targeted.
- Close with a clear call to action.
- Use UK English spelling throughout.
- Plain text only. No markdown, no asterisks, no bold formatting.
- Do not use em dashes anywhere in the response.
"""
