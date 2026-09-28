def build_interview_feedback_prompt(question: str, answer: str) -> str:
    return f"""You are an interview coach. The candidate was asked the interview question below and gave the answer shown.

QUESTION:
{question}

CANDIDATE'S ANSWER:
{answer}

Give specific, actionable feedback on this answer. Cover:
- What the answer does well.
- What it is missing or could strengthen, such as more concrete detail, structure, or a clearer outcome.
- One specific suggestion for how to improve the answer.

Instructions:
- Be direct and specific to what the candidate actually wrote, not generic interview advice.
- Two to three short paragraphs. No section labels, no markdown, no asterisks.
- Use UK English spelling throughout.
- Do not use em dashes anywhere in the response.
"""
