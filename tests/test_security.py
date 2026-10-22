from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from app.core.security import AuthenticationError, verify_access_token

@pytest.fixture
def signing_keys():
    private_key = rsa.generate_private_key( public_exponent=65537, key_size=2048,)
    private_pem = private_key.private_bytes( encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption(),).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(encoding=serialization.Encoding.PEM,format=serialization.PublicFormat.SubjectPublicKeyInfo,).decode("utf-8")

    return private_pem, public_pem


@pytest.fixture
def token_claims():
    now = datetime.now(timezone.utc)

    return {
        "sub": "user-123",
        "iss": "https://auth.example.test",
        "aud": "nowarie-realtime",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }


def create_token(claims, private_key):
    return jwt.encode(claims, private_key, algorithm="RS256")


def test_verify_valid_access_token(signing_keys, token_claims):
    private_key, public_key = signing_keys
    token = create_token(token_claims, private_key)

    claims = verify_access_token(
        token,
        public_key=public_key,
        issuer="https://auth.example.test",
        audience="nowarie-realtime",
    )

    assert claims["sub"] == "user-123"


def test_reject_expired_token(signing_keys, token_claims):
    private_key, public_key = signing_keys

    token_claims["exp"] = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = create_token(token_claims, private_key)

    with pytest.raises(AuthenticationError):
        verify_access_token(
            token,
            public_key=public_key,
            issuer="https://auth.example.test",
            audience="nowarie-realtime",
        )


def test_reject_token_signed_with_another_key(signing_keys, token_claims):
    _, public_key = signing_keys
    another_private_key, _ = signing_keys

    other_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    ).private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    token = create_token(token_claims, other_key)

    with pytest.raises(AuthenticationError):
        verify_access_token(
            token,
            public_key=public_key,
            issuer="https://auth.example.test",
            audience="nowarie-realtime",
        )


def test_reject_wrong_issuer(signing_keys, token_claims):
    private_key, public_key = signing_keys
    token_claims["iss"] = "https://untrusted.example.test"
    token = create_token(token_claims, private_key)

    with pytest.raises(AuthenticationError):
        verify_access_token(
            token,
            public_key=public_key,
            issuer="https://auth.example.test",
            audience="nowarie-realtime",
        )


def test_reject_wrong_audience(signing_keys, token_claims):
    private_key, public_key = signing_keys
    token_claims["aud"] = "another-service"
    token = create_token(token_claims, private_key)

    with pytest.raises(AuthenticationError):
        verify_access_token(
            token,
            public_key=public_key,
            issuer="https://auth.example.test",
            audience="nowarie-realtime",
        )


def test_reject_non_string_subject(signing_keys, token_claims):

    private_key, public_key = signing_keys
    token_claims["sub"]= 123
    token = create_token(token_claims, private_key)

    with pytest.raises(AuthenticationError):
        verify_access_token(
            token,
            public_key=public_key,
            issuer="https://auth.example.test",
            audience="nowarie-realtime",
        )

def test_reject_empty_subject(signing_keys, token_claims):
    private_key, public_key = signing_keys

    token_claims["sub"] = ""
    token = create_token(token_claims, private_key)

    with pytest.raises(AuthenticationError):
        verify_access_token(
            token,
            public_key=public_key,
            issuer="https://auth.example.test",
            audience="nowarie-realtime",
    )


def test_reject_whitespace_subject(signing_keys, token_claims):
    private_key, public_key = signing_keys
    token_claims["sub"] = " "
    token = create_token(token_claims, private_key)

    with pytest.raises(AuthenticationError):
        verify_access_token(
            token,
            public_key=public_key,
            issuer="https://auth.example.test",
            audience="nowarie-realtime",
        )



