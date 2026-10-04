from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = ""

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, value):
        return value.strip() if isinstance(value, str) else value


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


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class UpdateMeRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_display_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class ChangePasswordRequest(BaseModel):
    current_password: str
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


class CVUploadResponse(BaseModel):
    cv_text: str
    cv_s3_key: str


class ToolsUsedResponse(BaseModel):
    count: int
    total: int


class LatestSkillGapResponse(BaseModel):
    result: dict | None = None
    created_at: datetime | None = None


class SkillGapRequest(BaseModel):
    job_description: str = ""


class CoverLetterRequest(BaseModel):
    job_description: str = Field(min_length=1)
    tone: str = "Formal"

    @field_validator("job_description", mode="before")
    @classmethod
    def strip_job_description(cls, value):
        return value.strip() if isinstance(value, str) else value


class LinkedInRequest(BaseModel):
    context: str = ""


class CVDownloadRequest(BaseModel):
    cv_text: str


class TailoredCvResponse(BaseModel):
    result: str
    ats_compatible: bool


class CVTranslateRequest(BaseModel):
    cv_text: str
    target_language: str


ApplicationStatus = Literal["Applied", "Interview", "Offer", "Rejected"]


class ApplicationCreate(BaseModel):
    company: str
    role: str
    date_applied: date
    status: ApplicationStatus = "Applied"


class ApplicationOut(BaseModel):
    id: int
    profile_id: int
    company: str
    role: str
    date_applied: date
    status: str
    created_at: datetime


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class InterviewFeedbackRequest(BaseModel):
    question: str
    answer: str


class InterviewFeedbackResponse(BaseModel):
    feedback: str


class FollowupRequest(BaseModel):
    tool_name: str
    previous_result: str | dict
    question: str


class FollowupResponse(BaseModel):
    answer: str
