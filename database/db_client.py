import functools
import os
import json
import logging
import secrets
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESULT_TABLES = {
    "skill_gap": "skill_gap_results",
    "cv_analysis": "cv_analysis_results",
    "cover_letter": "cover_letters",
    "job_roles": "job_role_suggestions",
    "linkedin_message": "linkedin_messages",
    "interview_prep": "interview_prep_results",
    "cv_download": "cv_download_results",
    "career_roadmap": "career_roadmap_results",
    "salary_insights": "salary_insights_results",
    "tailored_cv": "tailored_cv_results",
}

_TABLE_BY_FUNC = {
    "init_db": "schema",
    "create_user": "users",
    "update_user": "users",
    "create_profile": "profiles",
    "set_active_profile": "profiles",
    "update_profile_label": "profiles",
    "set_profile_cv": "profiles",
    "update_profile": "profiles",
    "save_cv_upload": "cv_uploads",
    "save_cover_letter": "cover_letters",
    "save_linkedin_message": "linkedin_messages",
    "save_cv_translation": "cv_translations",
    "save_application": "applications",
    "update_application_status": "applications",
    "create_remember_token": "remember_tokens",
    "delete_remember_token": "remember_tokens",
    "save_tailored_cv": "tailored_cv_results",
    "create_password_reset_token": "password_reset_tokens",
    "delete_reset_token": "password_reset_tokens",
}


def _log_db_write(func):
    """Logs function name, record id, table name, and success/failure for every DB write."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if func.__name__ == "_insert":
            table = args[0] if args else kwargs.get("table")
            record_id = args[1] if len(args) > 1 else kwargs.get("profile_id")
        else:
            table = _TABLE_BY_FUNC.get(func.__name__, "unknown")
            record_id = args[0] if args else next(iter(kwargs.values()), None)
        try:
            result = func(*args, **kwargs)
            logger.info(
                "function=%s id=%s table=%s status=success",
                func.__name__, record_id, table,
            )
            return result
        except Exception as e:
            logger.error(
                "function=%s id=%s table=%s status=failure error=%s",
                func.__name__, record_id, table, e,
            )
            raise
    return wrapper


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


@_log_db_write
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            avatar_s3_key TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS profiles (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(id) ON DELETE CASCADE,
            label TEXT,
            data JSONB,
            cv_s3_key TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS cv_uploads (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            s3_key TEXT,
            uploaded_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS skill_gap_results (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            result JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS cv_analysis_results (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            result JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS cover_letters (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            job_description TEXT,
            letter_text TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS job_role_suggestions (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            result JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS linkedin_messages (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            context TEXT,
            message_text TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS interview_prep_results (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            result JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS cv_download_results (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            result JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS career_roadmap_results (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            result JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS salary_insights_results (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            result JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS cv_translations (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            target_language TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            company TEXT,
            role TEXT,
            date_applied DATE,
            status TEXT DEFAULT 'Applied',
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS remember_tokens (
            token TEXT PRIMARY KEY,
            user_id INT REFERENCES users(id) ON DELETE CASCADE,
            expires_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tailored_cv_results (
            id SERIAL PRIMARY KEY,
            profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
            job_description TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            token TEXT PRIMARY KEY,
            user_id INT REFERENCES users(id) ON DELETE CASCADE,
            expires_at TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()


# --- users ---

@_log_db_write
def create_user(email: str, password_hash: str, display_name: str = "") -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash, display_name) VALUES (%s, %s, %s) RETURNING id;",
        (email, password_hash, display_name),
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return user_id


def get_user_by_email(email: str) -> dict | None:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


@_log_db_write
def update_user(user_id: int, **fields) -> None:
    if not fields:
        return
    allowed = {"display_name", "avatar_s3_key", "password_hash"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{col} = %s" for col in updates)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE users SET {set_clause} WHERE id = %s;",
        (*updates.values(), user_id),
    )
    conn.commit()
    cur.close()
    conn.close()


# --- profiles ---

@_log_db_write
def create_profile(user_id: int, label: str, data: dict, cv_s3_key: str = None) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE profiles SET is_active = FALSE WHERE user_id = %s;", (user_id,))
    cur.execute(
        """INSERT INTO profiles (user_id, label, data, cv_s3_key, is_active)
           VALUES (%s, %s, %s, %s, TRUE) RETURNING id;""",
        (user_id, label, json.dumps(data), cv_s3_key),
    )
    profile_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return profile_id


def get_profiles_for_user(user_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM profiles WHERE user_id = %s ORDER BY created_at DESC;",
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def get_active_profile(user_id: int) -> dict | None:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM profiles WHERE user_id = %s AND is_active = TRUE LIMIT 1;",
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


@_log_db_write
def set_active_profile(user_id: int, profile_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE profiles SET is_active = FALSE WHERE user_id = %s;", (user_id,))
    cur.execute(
        "UPDATE profiles SET is_active = TRUE WHERE id = %s AND user_id = %s;",
        (profile_id, user_id),
    )
    conn.commit()
    cur.close()
    conn.close()


@_log_db_write
def update_profile_label(profile_id: int, label: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE profiles SET label = %s WHERE id = %s;", (label, profile_id))
    conn.commit()
    cur.close()
    conn.close()


@_log_db_write
def set_profile_cv(profile_id: int, cv_s3_key: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE profiles SET cv_s3_key = %s WHERE id = %s;", (cv_s3_key, profile_id))
    conn.commit()
    cur.close()
    conn.close()


@_log_db_write
def update_profile(profile_id: int, data: dict) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE profiles SET data = %s WHERE id = %s;",
        (json.dumps(data), profile_id),
    )
    conn.commit()
    cur.close()
    conn.close()


# --- results (append-only history, keyed by profile_id) ---

@_log_db_write
def save_cv_upload(profile_id: int, s3_key: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO cv_uploads (profile_id, s3_key) VALUES (%s, %s);",
        (profile_id, s3_key),
    )
    conn.commit()
    cur.close()
    conn.close()


def save_skill_gap(profile_id: int, result_dict: dict) -> None:
    _insert(RESULT_TABLES["skill_gap"], profile_id, "result", json.dumps(result_dict))


def save_cv_analysis(profile_id: int, result_dict) -> None:
    _insert(RESULT_TABLES["cv_analysis"], profile_id, "result", json.dumps(result_dict))


@_log_db_write
def save_cover_letter(profile_id: int, job_description: str, letter_text: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO cover_letters (profile_id, job_description, letter_text)
           VALUES (%s, %s, %s);""",
        (profile_id, job_description, letter_text),
    )
    conn.commit()
    cur.close()
    conn.close()


def save_job_roles(profile_id: int, result_dict) -> None:
    _insert(RESULT_TABLES["job_roles"], profile_id, "result", json.dumps(result_dict))


@_log_db_write
def save_linkedin_message(profile_id: int, context: str, message_text: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO linkedin_messages (profile_id, context, message_text)
           VALUES (%s, %s, %s);""",
        (profile_id, context, message_text),
    )
    conn.commit()
    cur.close()
    conn.close()


def save_interview_prep(profile_id: int, result_dict) -> None:
    _insert(RESULT_TABLES["interview_prep"], profile_id, "result", json.dumps(result_dict))


def save_cv_download(profile_id: int, result_dict) -> None:
    _insert(RESULT_TABLES["cv_download"], profile_id, "result", json.dumps(result_dict))


@_log_db_write
def save_tailored_cv(profile_id: int, job_description: str, result: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO tailored_cv_results (profile_id, job_description, result)
           VALUES (%s, %s, %s);""",
        (profile_id, job_description, result),
    )
    conn.commit()
    cur.close()
    conn.close()


def save_career_roadmap(profile_id: int, result_dict) -> None:
    _insert(RESULT_TABLES["career_roadmap"], profile_id, "result", json.dumps(result_dict))


def save_salary_insights(profile_id: int, result_dict) -> None:
    _insert(RESULT_TABLES["salary_insights"], profile_id, "result", json.dumps(result_dict))


@_log_db_write
def save_cv_translation(profile_id: int, target_language: str, result: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO cv_translations (profile_id, target_language, result)
           VALUES (%s, %s, %s);""",
        (profile_id, target_language, result),
    )
    conn.commit()
    cur.close()
    conn.close()


@_log_db_write
def save_application(profile_id: int, company: str, role: str, date_applied, status: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO applications (profile_id, company, role, date_applied, status)
           VALUES (%s, %s, %s, %s, %s);""",
        (profile_id, company, role, date_applied, status),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_applications(profile_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM applications WHERE profile_id = %s ORDER BY date_applied DESC, created_at DESC;",
        (profile_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


@_log_db_write
def update_application_status(application_id: int, status: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE applications SET status = %s WHERE id = %s;", (status, application_id))
    conn.commit()
    cur.close()
    conn.close()


@_log_db_write
def _insert(table: str, profile_id: int, column: str, value) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        sql.SQL("INSERT INTO {table} (profile_id, {column}) VALUES (%s, %s);")
        .format(table=sql.Identifier(table), column=sql.Identifier(column)),
        (profile_id, value),
    )
    conn.commit()
    cur.close()
    conn.close()


# The 8 tools counted toward the dashboard's "tools used" metric. Deliberately
# excludes cv_download_results, cv_translations, and applications, which aren't
# part of this metric.
TOOLS_USED_KEYS = [
    "skill_gap",
    "cv_analysis",
    "cover_letter",
    "job_roles",
    "linkedin_message",
    "interview_prep",
    "career_roadmap",
    "salary_insights",
]


def get_tools_used_count(profile_id: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    count = 0
    for tool_key in TOOLS_USED_KEYS:
        table = RESULT_TABLES[tool_key]
        cur.execute(
            sql.SQL("SELECT EXISTS(SELECT 1 FROM {table} WHERE profile_id = %s);")
            .format(table=sql.Identifier(table)),
            (profile_id,),
        )
        if cur.fetchone()[0]:
            count += 1
    cur.close()
    conn.close()
    return count


def get_latest(tool_key: str, profile_id: int) -> dict | None:
    table = RESULT_TABLES[tool_key]
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        sql.SQL("SELECT * FROM {table} WHERE profile_id = %s ORDER BY created_at DESC LIMIT 1;")
        .format(table=sql.Identifier(table)),
        (profile_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


@_log_db_write
def create_remember_token(user_id: int, days: int = 30) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=days)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO remember_tokens (token, user_id, expires_at) VALUES (%s, %s, %s);",
        (token, user_id, expires_at),
    )
    conn.commit()
    cur.close()
    conn.close()
    return token


def get_user_by_remember_token(token: str) -> dict | None:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT u.* FROM users u
           JOIN remember_tokens t ON t.user_id = u.id
           WHERE t.token = %s AND t.expires_at > NOW();""",
        (token,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


@_log_db_write
def delete_remember_token(token: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM remember_tokens WHERE token = %s;", (token,))
    conn.commit()
    cur.close()
    conn.close()


@_log_db_write
def create_password_reset_token(user_id: int, hours: int = 1) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=hours)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO password_reset_tokens (token, user_id, expires_at) VALUES (%s, %s, %s);",
        (token, user_id, expires_at),
    )
    conn.commit()
    cur.close()
    conn.close()
    return token


def get_user_by_reset_token(token: str) -> dict | None:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT u.* FROM users u
           JOIN password_reset_tokens t ON t.user_id = u.id
           WHERE t.token = %s AND t.expires_at > NOW();""",
        (token,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


@_log_db_write
def delete_reset_token(token: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM password_reset_tokens WHERE token = %s;", (token,))
    conn.commit()
    cur.close()
    conn.close()


def get_history(tool_key: str, profile_id: int) -> list[dict]:
    table = RESULT_TABLES[tool_key]
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        sql.SQL("SELECT * FROM {table} WHERE profile_id = %s ORDER BY created_at DESC;")
        .format(table=sql.Identifier(table)),
        (profile_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]
