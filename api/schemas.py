from datetime import date, datetime
from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    display_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordResponse(BaseModel):
    detail: str
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str | None = None
    avatar_s3_key: str | None = None


class ProfileData(BaseModel):
    target_role: str = ""
    current_skills: str = ""
    background: str = ""
    experience: str = ""
    tools: str = ""
    location: str = ""
    salary: str = ""
    open_to_learning: str = ""
    timeline: str = ""
    self_gaps: str = ""
    access_needs: str = ""


class ProfileCreate(ProfileData):
    label: str = ""


class ProfileUpdate(BaseModel):
    target_role: str | None = None
    current_skills: str | None = None
    background: str | None = None
    experience: str | None = None
    tools: str | None = None
    location: str | None = None
    salary: str | None = None
    open_to_learning: str | None = None
    timeline: str | None = None
    self_gaps: str | None = None
    access_needs: str | None = None


class ProfileOut(BaseModel):
    id: int
    user_id: int
    label: str | None = None
    data: dict
    cv_s3_key: str | None = None
    is_active: bool
    created_at: datetime


class ProfileLabelUpdate(BaseModel):
    label: str


class CVPrefillResponse(BaseModel):
    target_role: str = ""
    current_skills: str = ""
    background: str = ""
    experience: str = ""
    tools: str = ""
    location: str = ""


class HistoryEntry(BaseModel):
    content: str | dict
    created_at: datetime


class AvatarUploadResponse(BaseModel):
    avatar_s3_key: str


class ToolsUsedResponse(BaseModel):
    count: int
    total: int


class LatestSkillGapResponse(BaseModel):
    result: dict | None = None
    created_at: datetime | None = None


class CoverLetterRequest(BaseModel):
    job_description: str


class LinkedInRequest(BaseModel):
    context: str = ""


class CVDownloadRequest(BaseModel):
    cv_text: str


class TailoredCvRequest(BaseModel):
    job_description: str
    cv_text: str = ""


class TailoredCvResponse(BaseModel):
    result: str


class CVTranslateRequest(BaseModel):
    cv_text: str
    target_language: str


class ApplicationCreate(BaseModel):
    company: str
    role: str
    date_applied: date
    status: str = "Applied"


class ApplicationOut(BaseModel):
    id: int
    profile_id: int
    company: str
    role: str
    date_applied: date
    status: str
    created_at: datetime


class ApplicationStatusUpdate(BaseModel):
    status: str


class FollowupRequest(BaseModel):
    tool_name: str
    previous_result: str | dict
    question: str


class FollowupResponse(BaseModel):
    answer: str
