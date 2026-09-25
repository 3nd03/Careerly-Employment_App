from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from database.db_client import (
    create_user,
    get_user_by_email,
    update_user,
    create_remember_token,
    delete_remember_token,
    create_password_reset_token,
    get_user_by_reset_token,
    delete_reset_token,
)
from services.auth_service import hash_password, verify_password
from api.schemas import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserOut,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
)
from api.dependencies import security, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest):
    email = payload.email.strip().lower()
    if get_user_by_email(email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    user_id = create_user(email, hash_password(payload.password), payload.display_name.strip())
    token = create_remember_token(user_id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    email = payload.email.strip().lower()
    user = get_user_by_email(email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_remember_token(user["id"])
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    delete_remember_token(credentials.credentials)
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserOut)
def get_me(user: dict = Depends(get_current_user)):
    return user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest):
    email = payload.email.strip().lower()
    user = get_user_by_email(email)
    if not user:
        return ForgotPasswordResponse(
            detail="If that email is registered, a reset link has been sent."
        )
    token = create_password_reset_token(user["id"])
    return ForgotPasswordResponse(
        detail=(
            "If that email is registered, a reset link has been sent. "
            "Email sending not yet configured, use this token directly."
        ),
        reset_token=token,
    )


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    user = get_user_by_reset_token(payload.token)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    update_user(user["id"], password_hash=hash_password(payload.new_password))
    delete_reset_token(payload.token)
    return {"detail": "Password has been reset"}
