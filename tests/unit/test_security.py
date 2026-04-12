"""Unit tests for JWT security utilities."""
from __future__ import annotations

import time
from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        plain = "S3cur3P@ssword!"
        hashed = get_password_hash(plain)
        assert hashed != plain

    def test_verify_correct_password(self):
        plain = "S3cur3P@ssword!"
        hashed = get_password_hash(plain)
        assert verify_password(plain, hashed) is True

    def test_reject_wrong_password(self):
        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self):
        """bcrypt uses unique salts — two hashes of the same password differ."""
        plain = "same_password"
        h1 = get_password_hash(plain)
        h2 = get_password_hash(plain)
        assert h1 != h2
        # But both verify correctly
        assert verify_password(plain, h1)
        assert verify_password(plain, h2)


class TestJWT:
    def test_create_and_verify_token(self):
        import uuid
        uid = str(uuid.uuid4())
        payload = {"sub": "doc@hospital.com", "user_id": uid, "role": "physician"}
        token = create_access_token(data=payload)
        assert isinstance(token, str)
        assert len(token) > 10

        token_data = verify_token(token)
        assert str(token_data.user_id) == uid
        assert token_data.email == "doc@hospital.com"
        assert token_data.role == "physician"

    def test_expired_token_raises(self):
        import uuid
        from app.core.exceptions import AuthenticationError

        uid = str(uuid.uuid4())
        payload = {"sub": "doc@hospital.com", "user_id": uid, "role": "physician"}
        token = create_access_token(
            data=payload,
            expires_delta=timedelta(seconds=-1),  # Already expired
        )
        with pytest.raises(AuthenticationError):
            verify_token(token)

    def test_invalid_token_raises(self):
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError):
            verify_token("not.a.valid.jwt.token")

    def test_tampered_token_raises(self):
        import uuid
        from app.core.exceptions import AuthenticationError

        uid = str(uuid.uuid4())
        payload = {"sub": "doc@hospital.com", "user_id": uid, "role": "physician"}
        token = create_access_token(data=payload)
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(AuthenticationError):
            verify_token(tampered)

    def test_custom_expiry(self):
        import uuid
        uid = str(uuid.uuid4())
        payload = {"sub": "a@b.com", "user_id": uid, "role": "nurse"}
        token = create_access_token(data=payload, expires_delta=timedelta(hours=1))
        token_data = verify_token(token)
        assert str(token_data.user_id) == uid
