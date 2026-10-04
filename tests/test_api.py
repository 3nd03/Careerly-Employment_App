"""API tests mapped to the Careerly Test Documentation (test IDs in each test name).

The database, S3 and Claude are replaced with an in-memory fake, so these tests
never touch AWS or the Anthropic API.
"""
import secrets
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from api.main import app
from prompts.linkedin_prompt import build_linkedin_prompt

PDF_BYTES = b"%PDF-1.4 fake test pdf"


class FakeDB:
    def __init__(self):
        self.users = {}
        self.tokens = {}
        self.reset_tokens = {}
        self.profiles = {}
        self.applications = {}
        self.cover_letters = []
        self.claude_prompts = []

    # users and tokens
    def create_user(self, email, password_hash, display_name):
        user_id = len(self.users) + 1
        self.users[user_id] = {
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "display_name": display_name,
            "avatar_s3_key": None,
        }
        self.profiles[user_id] = {"id": user_id * 100, "user_id": user_id, "data": {"target_role": "Engineer"}}
        return user_id

    def get_user_by_email(self, email):
        return next((u for u in self.users.values() if u["email"] == email), None)

    def create_remember_token(self, user_id):
        token = secrets.token_hex(8)
        self.tokens[token] = user_id
        return token

    def get_user_by_remember_token(self, token):
        return self.users.get(self.tokens.get(token))

    def delete_remember_token(self, token):
        self.tokens.pop(token, None)

    def create_password_reset_token(self, user_id):
        token = secrets.token_hex(8)
        self.reset_tokens[token] = user_id
        return token

    def get_user_by_reset_token(self, token):
        return self.users.get(self.reset_tokens.get(token))

    def delete_reset_token(self, token):
        self.reset_tokens.pop(token, None)

    def update_user(self, user_id, **fields):
        self.users[user_id].update(fields)

    def get_active_profile(self, user_id):
        return self.profiles.get(user_id)

    # applications
    def save_application(self, profile_id, company, role, date_applied, status):
        app_id = len(self.applications) + 1
        self.applications[app_id] = {
            "id": app_id,
            "profile_id": profile_id,
            "company": company,
            "role": role,
            "date_applied": date_applied,
            "status": status,
            "created_at": datetime.now(),
        }

    def get_applications(self, profile_id):
        return [a for a in self.applications.values() if a["profile_id"] == profile_id]

    def update_application_status(self, application_id, profile_id, status):
        row = self.applications.get(application_id)
        if not row or row["profile_id"] != profile_id:
            return False
        row["status"] = status
        return True

    def delete_application(self, application_id, profile_id):
        row = self.applications.get(application_id)
        if not row or row["profile_id"] != profile_id:
            return False
        del self.applications[application_id]
        return True

    # tools
    def call_claude(self, prompt):
        self.claude_prompts.append(prompt)
        return "Generated text"

    def save_cover_letter(self, profile_id, job_description, letter_text):
        self.cover_letters.append((profile_id, job_description, letter_text))


@pytest.fixture
def db(monkeypatch):
    fake = FakeDB()
    patches = {
        "api.dependencies": ["get_user_by_remember_token", "get_active_profile"],
        "api.routers.auth": [
            "create_user", "get_user_by_email", "create_remember_token", "delete_remember_token",
            "create_password_reset_token", "get_user_by_reset_token", "delete_reset_token", "update_user",
        ],
        "api.routers.tools": [
            "save_application", "get_applications", "update_application_status", "delete_application",
            "call_claude", "save_cover_letter",
        ],
    }
    for module, names in patches.items():
        for name in names:
            monkeypatch.setattr(f"{module}.{name}", getattr(fake, name))
    for name in ["save_tailored_cv", "save_linkedin_message"]:
        monkeypatch.setattr(f"api.routers.tools.{name}", lambda *args, **kwargs: None)
    monkeypatch.setattr("api.routers.profile.upload_cv", lambda *args, **kwargs: "cvs/test.pdf")
    monkeypatch.setattr("api.routers.profile.update_profile_cv", lambda *args, **kwargs: None)
    monkeypatch.setattr("api.routers.profile.extract_pdf_text", lambda *args, **kwargs: "CV text")
    return fake


@pytest.fixture
def client():
    return TestClient(app)


def signup(client, email="user@example.com", password="password123"):
    response = client.post("/auth/signup", json={"email": email, "password": password, "display_name": "Test"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def add_application(client, headers, company="Acme"):
    response = client.post(
        "/tools/applications",
        json={"company": company, "role": "Engineer", "date_applied": "2026-10-01", "status": "Applied"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


# M3 – Account, Sign-up & Secure Login

def test_M3_T01_create_account(client, db):
    headers = signup(client)
    assert client.get("/auth/me", headers=headers).json()["email"] == "user@example.com"


@pytest.mark.parametrize("email", ["not-an-email", "missing-at.com", "a@b", ""])
def test_M3_T02_invalid_email_rejected(client, db, email):
    response = client.post("/auth/signup", json={"email": email, "password": "password123"})
    assert response.status_code == 422
    assert db.users == {}


def test_M3_T02_email_is_trimmed_and_lowercased(client, db):
    signup(client, email="  User@Example.com ")
    assert db.get_user_by_email("user@example.com") is not None


def test_M3_T03_login_after_logout(client, db):
    headers = signup(client)
    client.post("/auth/logout", headers=headers)
    assert client.get("/auth/me", headers=headers).status_code == 401

    response = client.post("/auth/login", json={"email": "user@example.com", "password": "password123"})
    assert response.status_code == 200


def test_M3_T03_login_wrong_password(client, db):
    signup(client)
    response = client.post("/auth/login", json={"email": "user@example.com", "password": "wrong-password"})
    assert response.status_code == 401


def test_M3_T05_password_stored_hashed(client, db):
    signup(client, password="password123")
    stored = db.get_user_by_email("user@example.com")["password_hash"]
    assert stored != "password123"
    assert "password123" not in stored


def test_M3_T07_password_reset(client, db):
    signup(client)
    token = client.post("/auth/forgot-password", json={"email": "user@example.com"}).json()["reset_token"]

    response = client.post("/auth/reset-password", json={"token": token, "new_password": "newpassword456"})
    assert response.status_code == 200

    old = client.post("/auth/login", json={"email": "user@example.com", "password": "password123"})
    new = client.post("/auth/login", json={"email": "user@example.com", "password": "newpassword456"})
    assert old.status_code == 401
    assert new.status_code == 200


def test_N_T03_duplicate_account_rejected(client, db):
    signup(client)
    response = client.post("/auth/signup", json={"email": "user@example.com", "password": "password123"})
    assert response.status_code == 409


def test_N_T03_short_password_rejected(client, db):
    response = client.post("/auth/signup", json={"email": "user@example.com", "password": "short"})
    assert response.status_code == 422


# M3-T06 / N-T04 – users can only access their own data

def test_N_T04_unauthenticated_requests_rejected(client, db):
    assert client.get("/tools/applications").status_code in (401, 403)
    assert client.put("/tools/applications/1", json={"status": "Offer"}).status_code in (401, 403)
    assert client.delete("/tools/applications/1").status_code in (401, 403)


def test_M3_T06_user_cannot_update_others_application(client, db):
    owner = signup(client, email="owner@example.com")
    attacker = signup(client, email="attacker@example.com")
    app_id = add_application(client, owner)

    response = client.put(f"/tools/applications/{app_id}", json={"status": "Rejected"}, headers=attacker)

    assert response.status_code == 404
    assert db.applications[app_id]["status"] == "Applied"


def test_M3_T06_user_cannot_delete_others_application(client, db):
    owner = signup(client, email="owner@example.com")
    attacker = signup(client, email="attacker@example.com")
    app_id = add_application(client, owner)

    response = client.delete(f"/tools/applications/{app_id}", headers=attacker)

    assert response.status_code == 404
    assert app_id in db.applications


def test_M3_T06_users_only_see_own_applications(client, db):
    owner = signup(client, email="owner@example.com")
    other = signup(client, email="other@example.com")
    add_application(client, owner)

    assert len(client.get("/tools/applications", headers=owner).json()) == 1
    assert client.get("/tools/applications", headers=other).json() == []


# S-B.5 – Job Application Tracker

def test_S5_T01_add_application(client, db):
    headers = signup(client)
    add_application(client, headers, company="Acme")
    applications = client.get("/tools/applications", headers=headers).json()
    assert [a["company"] for a in applications] == ["Acme"]


def test_S5_T02_update_application_status(client, db):
    headers = signup(client)
    app_id = add_application(client, headers)

    response = client.put(f"/tools/applications/{app_id}", json={"status": "Interview"}, headers=headers)

    assert response.status_code == 200
    assert db.applications[app_id]["status"] == "Interview"


def test_S5_T03_delete_application(client, db):
    headers = signup(client)
    app_id = add_application(client, headers)

    response = client.delete(f"/tools/applications/{app_id}", headers=headers)

    assert response.status_code == 200
    assert client.get("/tools/applications", headers=headers).json() == []


def test_S5_T03_delete_missing_application_returns_404(client, db):
    headers = signup(client)
    assert client.delete("/tools/applications/999", headers=headers).status_code == 404


# M1-T02 / N-T01 – invalid CV files

@pytest.mark.parametrize(
    "filename, content",
    [("cv.docx", PDF_BYTES), ("cv.pdf", b"not really a pdf"), ("cv.pdf", b"%PDF" + b"0" * (5 * 1024 * 1024))],
    ids=["wrong-extension", "not-a-pdf", "over-5mb"],
)
def test_N_T01_invalid_cv_rejected(client, db, filename, content):
    headers = signup(client)
    response = client.post("/profile/cv", files={"file": (filename, content)}, headers=headers)
    assert response.status_code == 400


def test_M2_T09_replace_cv_with_valid_pdf(client, db):
    headers = signup(client)
    response = client.post("/profile/cv", files={"file": ("cv.pdf", PDF_BYTES)}, headers=headers)
    assert response.status_code == 200
    assert response.json()["cv_s3_key"] == "cvs/test.pdf"


# N-T05 / N-T06 – generation needs a profile and a job description

def test_N_T05_generation_without_profile_rejected(client, db):
    headers = signup(client)
    db.profiles.clear()
    response = client.post("/tools/cover-letter", json={"job_description": "Python developer"}, headers=headers)
    assert response.status_code == 404
    assert db.claude_prompts == []


@pytest.mark.parametrize("job_description", ["", "   \n  "])
def test_N_T06_empty_job_description_cover_letter(client, db, job_description):
    headers = signup(client)
    response = client.post("/tools/cover-letter", json={"job_description": job_description}, headers=headers)
    assert response.status_code == 422
    assert db.claude_prompts == []


@pytest.mark.parametrize("job_description", ["", "   \n  "])
def test_N_T06_empty_job_description_tailored_cv(client, db, job_description):
    headers = signup(client)
    response = client.post("/tools/tailored-cv", data={"job_description": job_description}, headers=headers)
    assert response.status_code in (400, 422)
    assert db.claude_prompts == []


def test_M2_T01_tailored_cv_accepts_job_description(client, db):
    headers = signup(client)
    response = client.post("/tools/tailored-cv", data={"job_description": "Python developer"}, headers=headers)
    assert response.status_code == 200
    assert "Python developer" in db.claude_prompts[0]


# S-B.2 – Cover Letter Generator

def test_S2_T01_generate_and_save_cover_letter(client, db):
    headers = signup(client)
    response = client.post("/tools/cover-letter", json={"job_description": "Python developer"}, headers=headers)
    assert response.json()["letter_text"] == "Generated text"
    assert len(db.cover_letters) == 1


@pytest.mark.parametrize("tone", ["Formal", "Warm", "Direct"])
def test_S2_T02_T03_selected_tone_used(client, db, tone):
    headers = signup(client)
    client.post("/tools/cover-letter", json={"job_description": "Python developer", "tone": tone}, headers=headers)
    assert f"TONE: {tone}" in db.claude_prompts[0]


# S-B.4 – LinkedIn Message Generator

def test_S4_T02_prompt_enforces_character_limit():
    # The 300-character limit is only enforced via the prompt, so this checks the instruction is present.
    prompt = build_linkedin_prompt({"target_role": "Engineer"}, "")
    assert "300 characters" in prompt
