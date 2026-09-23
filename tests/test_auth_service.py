from services.auth_service import hash_password, verify_password


def test_hash_password_returns_different_string_than_input():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"


def test_hash_password_produces_unique_hashes_for_same_input():
    hashed_a = hash_password("same-password")
    hashed_b = hash_password("same-password")
    assert hashed_a != hashed_b


def test_verify_password_accepts_correct_password():
    hashed = hash_password("my-secret-password")
    assert verify_password("my-secret-password", hashed) is True


def test_verify_password_rejects_incorrect_password():
    hashed = hash_password("my-secret-password")
    assert verify_password("wrong-password", hashed) is False
