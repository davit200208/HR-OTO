import uuid
from datetime import timedelta

from app.core.security import create_token, decode_token, hash_password, hash_token, verify_password


def test_password_hash_is_one_way_and_verifiable() -> None:
    password = "StrongPassword!123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_contains_user_and_session_context() -> None:
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    token = create_token(user_id, session_id, "access", timedelta(minutes=5))
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["sid"] == str(session_id)
    assert hash_token(token) != token
