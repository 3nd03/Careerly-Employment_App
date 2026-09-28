import io
import json
import re

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from database.db_client import (
    create_profile,
    get_profiles_for_user,
    get_active_profile,
    set_active_profile,
    update_profile,
    update_profile_label,
    update_profile_cv,
    update_user,
    get_history,
    get_latest,
    get_tools_used_count,
    TOOLS_USED_KEYS,
    RESULT_TABLES,
)
from services.claude_client import call_claude
from services.s3_client import upload_avatar, upload_cv
from utils.pdf import extract_pdf_text
from utils.file_validation import validate_pdf
from prompts.profile_extraction_prompt import build_profile_extraction_prompt
from api.schemas import (
    ProfileCreate,
    ProfileUpdate,
    ProfileOut,
    ProfileLabelUpdate,
    CVPrefillResponse,
    HistoryEntry,
    AvatarUploadResponse,
    CVUploadResponse,
    ToolsUsedResponse,
    LatestSkillGapResponse,
)
from api.dependencies import get_current_user, get_current_profile

router = APIRouter(prefix="/profile", tags=["profile"])

CV_EXTRACTABLE_KEYS = ["target_role", "current_skills", "background", "experience", "tools", "location"]


def _ensure_owns_profile(user_id: int, profile_id: int) -> None:
    profiles = get_profiles_for_user(user_id)
    if not any(p["id"] == profile_id for p in profiles):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")


def _parse_extracted(raw: str) -> dict:
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {key: str(parsed.get(key) or "") for key in CV_EXTRACTABLE_KEYS}


@router.post("/cv-prefill", response_model=CVPrefillResponse)
async def cv_prefill(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    file_bytes = await file.read()
    validate_pdf(file_bytes, file.filename)
    try:
        cv_text = extract_pdf_text(io.BytesIO(file_bytes)).strip()
    except Exception:
        return CVPrefillResponse()

    if not cv_text:
        return CVPrefillResponse()

    prompt = build_profile_extraction_prompt(cv_text)
    raw = call_claude(prompt)
    return CVPrefillResponse(**_parse_extracted(raw))


@router.post("", response_model=ProfileOut)
def create_profile_endpoint(payload: ProfileCreate, user: dict = Depends(get_current_user)):
    data = payload.model_dump(exclude={"label"})
    label = payload.label or data.get("target_role") or "My profile"
    create_profile(user["id"], label, data)
    return get_active_profile(user["id"])


@router.get("", response_model=ProfileOut)
def get_profile(profile: dict = Depends(get_current_profile)):
    return profile


@router.put("", response_model=ProfileOut)
def update_active_profile(payload: ProfileUpdate, profile: dict = Depends(get_current_profile)):
    merged = {**profile["data"], **payload.model_dump(exclude_none=True)}
    update_profile(profile["id"], merged)
    profile["data"] = merged
    return profile


@router.get("/all", response_model=list[ProfileOut])
def get_all_profiles(user: dict = Depends(get_current_user)):
    return get_profiles_for_user(user["id"])


@router.put("/{profile_id}/activate", response_model=ProfileOut)
def activate_profile(profile_id: int, user: dict = Depends(get_current_user)):
    _ensure_owns_profile(user["id"], profile_id)
    set_active_profile(user["id"], profile_id)
    return get_active_profile(user["id"])


@router.put("/{profile_id}/label")
def rename_profile(profile_id: int, payload: ProfileLabelUpdate, user: dict = Depends(get_current_user)):
    _ensure_owns_profile(user["id"], profile_id)
    update_profile_label(profile_id, payload.label)
    return {"detail": "Label updated"}


def _format_history_entries(entries: list[dict]) -> list[dict]:
    return [
        {
            "content": entry.get("result") or entry.get("letter_text") or entry.get("message_text") or "",
            "created_at": entry["created_at"],
        }
        for entry in entries
    ]


@router.get("/history", response_model=dict[str, list[HistoryEntry]])
def get_profile_history(profile: dict = Depends(get_current_profile)):
    return {tool_key: _format_history_entries(get_history(tool_key, profile["id"])) for tool_key in RESULT_TABLES}


@router.get("/history/{tool_key}", response_model=list[HistoryEntry])
def get_profile_history_for_tool(tool_key: str, profile: dict = Depends(get_current_profile)):
    if tool_key not in RESULT_TABLES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown tool")
    return _format_history_entries(get_history(tool_key, profile["id"]))


@router.post("/cv", response_model=CVUploadResponse)
async def upload_profile_cv(file: UploadFile = File(...), profile: dict = Depends(get_current_profile)):
    file_bytes = await file.read()
    validate_pdf(file_bytes, file.filename)
    cv_text = extract_pdf_text(io.BytesIO(file_bytes)).strip()
    s3_key = upload_cv(file_bytes, profile["id"], file.filename)
    update_profile_cv(profile["id"], s3_key, cv_text)
    return CVUploadResponse(cv_text=cv_text, cv_s3_key=s3_key)


@router.post("/avatar", response_model=AvatarUploadResponse)
async def upload_avatar_endpoint(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    file_bytes = await file.read()
    key = upload_avatar(file_bytes, user["id"], file.filename)
    update_user(user["id"], avatar_s3_key=key)
    return AvatarUploadResponse(avatar_s3_key=key)


@router.get("/tools-used", response_model=ToolsUsedResponse)
def get_tools_used(profile: dict = Depends(get_current_profile)):
    return ToolsUsedResponse(count=get_tools_used_count(profile["id"]), total=len(TOOLS_USED_KEYS))


@router.get("/latest-skill-gap", response_model=LatestSkillGapResponse)
def get_latest_skill_gap(profile: dict = Depends(get_current_profile)):
    latest = get_latest("skill_gap", profile["id"])
    if not latest:
        return LatestSkillGapResponse()
    return LatestSkillGapResponse(result=latest["result"], created_at=latest["created_at"])
