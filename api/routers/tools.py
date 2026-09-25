import io

from fastapi import APIRouter, Depends, File, Response, UploadFile

from services.claude_client import call_claude
from services.s3_client import upload_cv
from database.db_client import (
    save_skill_gap,
    save_cv_analysis,
    save_cv_upload,
    save_cover_letter,
    save_job_roles,
    save_linkedin_message,
    save_interview_prep,
    save_cv_download,
    save_career_roadmap,
    save_salary_insights,
    save_cv_translation,
    save_application,
    get_applications,
    update_application_status,
    save_tailored_cv,
    get_latest,
)
from utils.pdf import extract_pdf_text, generate_pdf

from prompts.skill_gap_prompt import build_skill_gap_prompt
from prompts.cv_prompt import build_cv_prompt
from prompts.cover_letter_prompt import build_cover_letter_prompt
from prompts.job_roles_prompt import build_job_roles_prompt
from prompts.linkedin_prompt import build_linkedin_prompt
from prompts.interview_prep_prompt import build_interview_prep_prompt
from prompts.cv_download_prompt import build_cv_download_prompt
from prompts.career_roadmap_prompt import build_career_roadmap_prompt
from prompts.salary_insights_prompt import build_salary_insights_prompt
from prompts.cv_translator_prompt import build_cv_translator_prompt
from prompts.tailored_cv_prompt import build_tailored_cv_prompt

from api.dependencies import get_current_profile
from api.schemas import (
    CoverLetterRequest,
    LinkedInRequest,
    CVDownloadRequest,
    CVTranslateRequest,
    ApplicationCreate,
    ApplicationOut,
    ApplicationStatusUpdate,
    FollowupRequest,
    FollowupResponse,
    TailoredCvRequest,
    TailoredCvResponse,
)

router = APIRouter(prefix="/tools", tags=["tools"])


def _parse_labeled(text: str, labels: list[str]) -> dict:
    sections = {}
    for i, label in enumerate(labels):
        start = text.find(f"{label}:")
        if start == -1:
            sections[label] = ""
            continue
        start += len(f"{label}:")
        end = len(text)
        for next_label in labels[i + 1:]:
            pos = text.find(f"{next_label}:")
            if pos != -1 and pos < end:
                end = pos
        sections[label] = text[start:end].strip()
    return sections


@router.post("/skill-gap")
def run_skill_gap(profile: dict = Depends(get_current_profile)):
    prompt = build_skill_gap_prompt(profile["data"])
    response = call_claude(prompt)
    result = _parse_labeled(response, ["MATCH_SCORE", "STRONG_SKILLS", "MISSING_SKILLS", "NEXT_STEPS"])
    save_skill_gap(profile["id"], result)
    return result


@router.post("/cv-analyse")
async def run_cv_analyse(file: UploadFile = File(...), profile: dict = Depends(get_current_profile)):
    file_bytes = await file.read()
    cv_text = extract_pdf_text(io.BytesIO(file_bytes)).strip()
    prompt = build_cv_prompt(profile["data"], cv_text)
    result = call_claude(prompt)
    s3_key = upload_cv(file_bytes, profile["id"], file.filename)
    save_cv_upload(profile["id"], s3_key)
    save_cv_analysis(profile["id"], result)
    return {"result": result}


@router.post("/cover-letter")
def run_cover_letter(payload: CoverLetterRequest, profile: dict = Depends(get_current_profile)):
    prompt = build_cover_letter_prompt(profile["data"], payload.job_description)
    letter_text = call_claude(prompt)
    save_cover_letter(profile["id"], payload.job_description, letter_text)
    return {"letter_text": letter_text}


@router.post("/job-roles")
def run_job_roles(profile: dict = Depends(get_current_profile)):
    latest_skill_gap = get_latest("skill_gap", profile["id"])
    missing_skills = latest_skill_gap["result"].get("MISSING_SKILLS", "") if latest_skill_gap else ""
    prompt = build_job_roles_prompt(profile["data"], missing_skills)
    response = call_claude(prompt)
    result = _parse_labeled(response, ["CURRENT_ROLES", "FUTURE_ROLES"])
    save_job_roles(profile["id"], result)
    return result


@router.post("/linkedin-message")
def run_linkedin_message(payload: LinkedInRequest, profile: dict = Depends(get_current_profile)):
    context = (payload.context or "").strip()
    prompt = build_linkedin_prompt(profile["data"], context)
    message_text = call_claude(prompt)
    save_linkedin_message(profile["id"], context, message_text)
    return {"message_text": message_text}


@router.post("/interview-prep")
def run_interview_prep(profile: dict = Depends(get_current_profile)):
    latest_skill_gap = get_latest("skill_gap", profile["id"])
    missing_skills = latest_skill_gap["result"].get("MISSING_SKILLS", "") if latest_skill_gap else ""
    prompt = build_interview_prep_prompt(profile["data"], missing_skills)
    result = call_claude(prompt)
    save_interview_prep(profile["id"], result)
    return {"result": result}


@router.post("/cv-download")
def run_cv_download(payload: CVDownloadRequest, profile: dict = Depends(get_current_profile)):
    prompt = build_cv_download_prompt(payload.cv_text)
    result = call_claude(prompt)
    save_cv_download(profile["id"], result)
    pdf_bytes = generate_pdf(result)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cv.pdf"},
    )


@router.post("/career-roadmap")
def run_career_roadmap(profile: dict = Depends(get_current_profile)):
    latest_skill_gap = get_latest("skill_gap", profile["id"])
    skill_gap_result = latest_skill_gap["result"] if latest_skill_gap else None
    prompt = build_career_roadmap_prompt(profile["data"], skill_gap_result)
    response = call_claude(prompt)
    result = _parse_labeled(response, ["WHERE_NOW", "THREE_MONTH", "SIX_MONTH", "ONE_YEAR"])
    save_career_roadmap(profile["id"], result)
    return result


@router.post("/salary-insights")
def run_salary_insights(profile: dict = Depends(get_current_profile)):
    prompt = build_salary_insights_prompt(profile["data"])
    response = call_claude(prompt)
    result = _parse_labeled(response, ["RANGE_JUNIOR", "RANGE_MID", "RANGE_SENIOR", "FACTORS", "NEGOTIATION_TIPS"])
    save_salary_insights(profile["id"], result)
    return result


@router.post("/cv-translate")
def run_cv_translate(payload: CVTranslateRequest, profile: dict = Depends(get_current_profile)):
    prompt = build_cv_translator_prompt(payload.cv_text, payload.target_language)
    result = call_claude(prompt)
    save_cv_translation(profile["id"], payload.target_language, result)
    pdf_bytes = generate_pdf(result, language=payload.target_language)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cv_translated.pdf"},
    )


@router.post("/tailored-cv", response_model=TailoredCvResponse)
def run_tailored_cv(payload: TailoredCvRequest, profile: dict = Depends(get_current_profile)):
    prompt = build_tailored_cv_prompt(profile["data"], payload.job_description, payload.cv_text)
    result = call_claude(prompt)
    save_tailored_cv(profile["id"], payload.job_description, result)
    return TailoredCvResponse(result=result)


@router.get("/applications", response_model=list[ApplicationOut])
def list_applications(profile: dict = Depends(get_current_profile)):
    return get_applications(profile["id"])


@router.post("/applications", response_model=ApplicationOut)
def add_application(payload: ApplicationCreate, profile: dict = Depends(get_current_profile)):
    save_application(profile["id"], payload.company, payload.role, payload.date_applied, payload.status)
    applications = get_applications(profile["id"])
    return max(applications, key=lambda a: a["created_at"])


@router.put("/applications/{application_id}")
def update_application(application_id: int, payload: ApplicationStatusUpdate):
    update_application_status(application_id, payload.status)
    return {"detail": "Status updated"}


@router.post("/followup", response_model=FollowupResponse)
def run_followup(payload: FollowupRequest, profile: dict = Depends(get_current_profile)):
    prompt = (
        f"Here is the user's result from this tool: {payload.previous_result}\n\n"
        f"Here is their profile: {profile['data']}\n\n"
        f"Answer this follow-up question: {payload.question}"
    )
    answer = call_claude(prompt)
    return FollowupResponse(answer=answer)
