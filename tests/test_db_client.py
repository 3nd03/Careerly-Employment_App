import json
import pytest
from unittest.mock import patch, MagicMock


def make_mock_conn(fetchone_return=None):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = fetchone_return
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur


@patch("database.db_client.get_connection")
def test_create_user_inserts_and_returns_id(mock_get_conn):
    from database.db_client import create_user
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(42,))
    mock_get_conn.return_value = mock_conn

    user_id = create_user("oscar@example.com", "hashed-pw", "Oscar")

    sql, params = mock_cur.execute.call_args.args
    assert "users" in sql
    assert "oscar@example.com" in params
    assert user_id == 42


@patch("database.db_client.get_connection")
def test_get_user_by_email_queries_users_table(mock_get_conn):
    from database.db_client import get_user_by_email
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)
    mock_get_conn.return_value = mock_conn

    get_user_by_email("oscar@example.com")

    sql, params = mock_cur.execute.call_args.args
    assert "users" in sql
    assert "oscar@example.com" in params


@patch("database.db_client.get_connection")
def test_create_profile_stores_json_data(mock_get_conn):
    from database.db_client import create_profile
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(7,))
    mock_get_conn.return_value = mock_conn

    profile_data = {"target_role": "Data Scientist"}
    profile_id = create_profile(1, "My Profile", profile_data)

    calls_made = [str(c) for c in mock_cur.execute.call_args_list]
    assert any("profiles" in c for c in calls_made)
    assert any(json.dumps(profile_data) in c for c in calls_made)
    assert profile_id == 7


@patch("database.db_client.get_connection")
def test_save_skill_gap_stores_result(mock_get_conn):
    from database.db_client import save_skill_gap
    mock_conn, mock_cur = make_mock_conn()
    mock_get_conn.return_value = mock_conn

    result = {"score": 75, "missing": ["Docker"]}
    save_skill_gap(7, result)

    calls_made = [str(c) for c in mock_cur.execute.call_args_list]
    assert any("skill_gap_results" in c for c in calls_made)
    assert any(json.dumps(result) in c for c in calls_made)


@patch("database.db_client.get_connection")
def test_save_cover_letter_stores_text_and_jd(mock_get_conn):
    from database.db_client import save_cover_letter
    mock_conn, mock_cur = make_mock_conn()
    mock_get_conn.return_value = mock_conn

    save_cover_letter(7, "We are hiring a DS", "Dear Hiring Manager...")

    calls_made = [str(c) for c in mock_cur.execute.call_args_list]
    assert any("cover_letters" in c for c in calls_made)
    assert any("We are hiring a DS" in c for c in calls_made)
    assert any("Dear Hiring Manager" in c for c in calls_made)


@patch("database.db_client.get_connection")
def test_save_linkedin_message_stores_context_and_text(mock_get_conn):
    from database.db_client import save_linkedin_message
    mock_conn, mock_cur = make_mock_conn()
    mock_get_conn.return_value = mock_conn

    save_linkedin_message(7, "Recruiter at Google", "Hi, I saw your profile...")

    calls_made = [str(c) for c in mock_cur.execute.call_args_list]
    assert any("linkedin_messages" in c for c in calls_made)
    assert any("Recruiter at Google" in c for c in calls_made)


@patch("database.db_client.get_connection")
def test_save_cv_upload_stores_s3_key(mock_get_conn):
    from database.db_client import save_cv_upload
    mock_conn, mock_cur = make_mock_conn()
    mock_get_conn.return_value = mock_conn

    save_cv_upload(7, "uploads/cv_oscar.pdf")

    sql, params = mock_cur.execute.call_args.args
    assert "cv_uploads" in sql
    assert "uploads/cv_oscar.pdf" in params


@patch("database.db_client.get_connection")
def test_update_profile_cv_stores_s3_key_and_text(mock_get_conn):
    from database.db_client import update_profile_cv
    mock_conn, mock_cur = make_mock_conn()
    mock_get_conn.return_value = mock_conn

    update_profile_cv(7, "cvs/7/resume.pdf", "Extracted CV text")

    sql, params = mock_cur.execute.call_args.args
    assert "profiles" in sql
    assert "cvs/7/resume.pdf" in params
    assert "Extracted CV text" in params


@patch("database.db_client.get_connection")
def test_delete_application_removes_by_id_and_profile(mock_get_conn):
    from database.db_client import delete_application
    mock_conn, mock_cur = make_mock_conn()
    mock_cur.rowcount = 1
    mock_get_conn.return_value = mock_conn

    assert delete_application(3, 7) is True

    sql, params = mock_cur.execute.call_args.args
    assert "applications" in sql
    assert "profile_id" in sql
    assert params == (3, 7)


@patch("database.db_client.get_connection")
def test_update_application_status_scoped_to_profile(mock_get_conn):
    from database.db_client import update_application_status
    mock_conn, mock_cur = make_mock_conn()
    mock_cur.rowcount = 0
    mock_get_conn.return_value = mock_conn

    assert update_application_status(3, 7, "Offer") is False

    sql, params = mock_cur.execute.call_args.args
    assert "profile_id" in sql
    assert params == ("Offer", 3, 7)


@patch("database.db_client.get_connection")
def test_db_connection_closed_after_operation(mock_get_conn):
    from database.db_client import save_cv_upload
    mock_conn, mock_cur = make_mock_conn()
    mock_get_conn.return_value = mock_conn

    save_cv_upload(7, "uploads/cv_oscar.pdf")

    mock_conn.close.assert_called_once()
    mock_cur.close.assert_called_once()


def test_cv_translate_is_in_result_tables():
    # Regression: cv_translate was missing from RESULT_TABLES, so translations never appeared
    # in GET /profile/history even though save_cv_translation wrote them to the database.
    from database.db_client import RESULT_TABLES
    assert RESULT_TABLES["cv_translate"] == "cv_translations"


@patch("database.db_client.get_connection")
def test_get_history_queries_cv_translations_table(mock_get_conn):
    from database.db_client import get_history
    mock_conn, mock_cur = make_mock_conn()
    mock_cur.fetchall.return_value = []
    mock_get_conn.return_value = mock_conn

    get_history("cv_translate", 7)

    sql, params = mock_cur.execute.call_args.args
    assert "cv_translations" in str(sql)
    assert params == (7,)
