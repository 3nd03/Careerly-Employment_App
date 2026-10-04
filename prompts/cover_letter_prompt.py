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
- Start directly with the salutation (e.g. "Dear Hiring Manager,"). Do not include a letterhead, date, or address block, and never use placeholder brackets such as [Your Name], [Your Address], or [Email Address] for any detail that is not in the profile above; simply leave it out rather than guessing or inventing one.
- Reference the candidate's actual skills, background, and experience where relevant, but do not inflate them. If the profile describes a skill as "basic", "limited", or "familiar with", describe it at that same level rather than implying regular, confident, or advanced use. Do not claim experience with a specific tool or technology named in the job description unless it also appears in the profile; where the candidate lacks something the role asks for, it is fine to lean on genuinely related experience or express enthusiasm to learn it, but never state or imply they already have it.
- Address specific requirements or keywords from the job description directly, honestly, and without overstating the candidate's fit.
- Write in the tone described above, consistently throughout. Avoid generic phrases and corporate clichés regardless of tone.
- Three to four paragraphs. Concise and targeted.
- Close with a clear call to action.
- Use UK English spelling throughout.
- Plain text only. No markdown, no asterisks, no bold formatting.
- Do not use em dashes anywhere in the response.
"""
